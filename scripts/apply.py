#!/usr/bin/python3
"""Install a version-matched dock overlay and preserve the previous files."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile

FILES = ('Dock.qml', 'DockWindow.qml', 'DockModel.js', 'WindowIndicator.qml', 'WindowPeek.qml')
TARGET = Path('/usr/share/omarchy/shell/plugins/dock')
STATE = Path('/var/lib/omarchy-dock-overlay')


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def plain_path(path):
    """Reject symlinks in files and ancestors before touching a destination."""
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError(f'Refusing symlink: {part}')
    return path


def read_file(path):
    plain_path(path)
    if path.exists() and not path.is_file():
        raise ValueError(f'Not a regular file: {path}')
    return path.read_bytes() if path.exists() else None


def atomic_write(path, data, mode=0o644):
    plain_path(path)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def apply(bundle, target=TARGET, state=STATE, uninstall=False, check=False):
    bundle, target, state = map(plain_path, (bundle, target, state))
    if not target.is_dir():
        raise ValueError(f'Omarchy dock not found: {target}')
    # Keep the lock outside the receipt directory, including across uninstall.
    state.parent.mkdir(parents=True, exist_ok=True)
    lock_path = plain_path(state.parent / (state.name + '.lock'))
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        current = {name: read_file(target / name) for name in FILES}
        receipt_raw = read_file(state / 'receipt.json')
        receipt = json.loads(receipt_raw) if receipt_raw is not None else None
        if receipt:
            if set(receipt['installed']) != set(FILES) or set(receipt['original']) != set(FILES):
                raise ValueError('Invalid installation receipt')
            for name in FILES:
                if digest(current[name]) != receipt['installed'][name]:
                    raise ValueError(f'{name} changed since installation; refusing to overwrite it. '
                                     'A package update or local edit may have replaced the overlay.')
        if uninstall:
            if not receipt:
                print('No managed dock overlay is installed.')
                return
            incoming = {}
            modes = {}
            for name in FILES:
                before = receipt['original'][name]
                incoming[name] = read_file(state / ('original-' + name)) if before['sha256'] else None
                modes[name] = before['mode']
                if digest(incoming[name]) != before['sha256']:
                    raise ValueError(f'Invalid original backup: {name}')
            variant = receipt['variant']
        else:
            variants = json.loads((bundle / 'variants.json').read_text())
            matches = []
            for variant, spec in variants.items():
                expected = receipt['installed'] if receipt else spec['original']
                if all(digest(current[name]) in (expected[name], spec['payload'][name]) for name in FILES):
                    if not receipt or variant == receipt['variant']:
                        matches.append(variant)
            if len(matches) != 1:
                raise ValueError('The installed dock does not match a supported source revision. '
                                 'Nothing was changed. Supported: Omarchy 4.5.0 and the documented quattro revision.')
            variant = matches[0]
            spec = variants[variant]
            incoming = {name: read_file(bundle / 'variants' / variant / name) for name in FILES}
            for name in FILES:
                if incoming[name] is None or digest(incoming[name]) != spec['payload'][name]:
                    raise ValueError(f'Invalid payload checksum: {name}')
            modes = dict.fromkeys(FILES, 0o644)
        if check:
            print(f'Compatible dock: {variant}; no files changed.')
            return
        state.mkdir(mode=0o700, exist_ok=True)
        if not uninstall and receipt is None:
            original = {}
            for name, data in current.items():
                original[name] = {'sha256': digest(data), 'mode': stat.S_IMODE((target / name).stat().st_mode) if data is not None else 0o644}
                if data is not None:
                    atomic_write(state / ('original-' + name), data, 0o600)
            receipt = {'variant': variant, 'original': original, 'installed': {}}
        previous_modes = {name: stat.S_IMODE((target / name).stat().st_mode) if current[name] is not None else 0o644 for name in FILES}
        try:
            for name, data in incoming.items():
                if data is None:
                    if (target / name).exists():
                        (target / name).unlink()
                else:
                    atomic_write(target / name, data, modes[name])
            if uninstall:
                # Keep backups for inspection; remove only the active receipt.
                (state / 'receipt.json').unlink()
            else:
                receipt['installed'] = {name: digest(data) for name, data in incoming.items()}
                atomic_write(state / 'receipt.json', (json.dumps(receipt, indent=2) + '\n').encode(), 0o600)
        except BaseException:
            for name, data in current.items():
                if data is None:
                    if (target / name).exists():
                        (target / name).unlink()
                else:
                    atomic_write(target / name, data, previous_modes[name])
            raise
        print(('Restored previous dock' if uninstall else 'Installed dock overlay') + f' ({variant}).')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--target', type=Path, default=TARGET, help='Dock directory (fixture directory for tests)')
    parser.add_argument('--state', type=Path, default=STATE, help='Backup and receipt directory')
    parser.add_argument('--uninstall', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        apply(args.bundle, args.target, args.state, args.uninstall, args.check)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'omarchy-dock: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
