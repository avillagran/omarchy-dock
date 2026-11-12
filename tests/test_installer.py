#!/usr/bin/python3
"""Exercise transactions in retained fixtures; never recursively delete trees."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('overlay', REPO / 'scripts/apply.py')
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        cache = Path(os.environ.get('TMPDIR', Path.home() / '.cache/omarchy-dock-tests'))
        cache.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix='fixture-', dir=cache))
        self.bundle = self.root / 'bundle'
        self.target = self.root / 'dock'
        self.state = self.root / 'state'
        (self.bundle / 'variants/test').mkdir(parents=True)
        self.target.mkdir()
        self.original = {}
        self.payload = {}
        for i, name in enumerate(overlay.FILES):
            data = ('original ' + name).encode() if i < 3 else None
            self.original[name] = data
            if data is not None:
                (self.target / name).write_bytes(data)
            self.payload[name] = ('new ' + name).encode()
            (self.bundle / 'variants/test' / name).write_bytes(self.payload[name])
        self.manifest()

    def manifest(self):
        (self.bundle / 'variants.json').write_text(json.dumps({'test': {
            'original': {name: overlay.digest(data) for name, data in self.original.items()},
            'payload': {name: overlay.digest(data) for name, data in self.payload.items()},
        }}))

    def run_apply(self, **kwargs):
        overlay.apply(self.bundle, self.target, self.state, **kwargs)

    def contents(self):
        return {name: (self.target / name).read_bytes() if (self.target / name).exists() else None for name in overlay.FILES}

    def test_install_upgrade_and_restore_initial_files(self):
        self.run_apply()
        self.assertEqual(self.contents(), self.payload)
        self.payload['Dock.qml'] = b'upgraded dock'
        (self.bundle / 'variants/test/Dock.qml').write_bytes(self.payload['Dock.qml'])
        self.manifest()
        self.run_apply()
        self.assertEqual(self.contents(), self.payload)
        self.run_apply(uninstall=True)
        self.assertEqual(self.contents(), self.original)

    def test_unknown_version_is_left_untouched(self):
        (self.target / 'Dock.qml').write_bytes(b'new package revision')
        before = self.contents()
        with self.assertRaises(ValueError):
            self.run_apply()
        self.assertEqual(self.contents(), before)
        self.assertFalse((self.state / 'receipt.json').exists())

    def test_damaged_payload_is_rejected_before_install(self):
        (self.bundle / 'variants/test/WindowPeek.qml').write_bytes(b'damaged')
        with self.assertRaises(ValueError):
            self.run_apply()
        self.assertEqual(self.contents(), self.original)

    def test_package_update_is_preserved_on_uninstall(self):
        self.run_apply()
        (self.target / 'Dock.qml').write_bytes(b'package update')
        before = self.contents()
        with self.assertRaises(ValueError):
            self.run_apply(uninstall=True)
        self.assertEqual(self.contents(), before)

    def test_fixture_symlink_is_not_followed(self):
        other = self.root / 'fixture-link-target'
        other.write_bytes(b'leave this alone')
        (self.target / 'WindowPeek.qml').symlink_to(other)
        with self.assertRaises(ValueError):
            self.run_apply()
        self.assertEqual(other.read_bytes(), b'leave this alone')

    def test_failed_transaction_restores_files(self):
        write = overlay.atomic_write
        failed = False

        def fail_once(path, data, mode=0o644):
            nonlocal failed
            if path == self.target / 'DockWindow.qml' and not failed:
                failed = True
                raise OSError('simulated write failure')
            return write(path, data, mode)

        with patch.object(overlay, 'atomic_write', side_effect=fail_once):
            with self.assertRaises(OSError):
                self.run_apply()
        self.assertEqual(self.contents(), self.original)
        self.assertFalse((self.state / 'receipt.json').exists())

    def test_check_does_not_install(self):
        self.run_apply(check=True)
        self.assertEqual(self.contents(), self.original)
        self.assertFalse((self.state / 'receipt.json').exists())


if __name__ == '__main__':
    unittest.main()
