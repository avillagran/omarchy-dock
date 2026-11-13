# Omarchy Dock previews

Live window previews and small slanted window indicators for Omarchy's floating-workspace dock.

![Live previews and the size control](https://github.com/avillagran/omarchy-dock/releases/download/v0.1.0/after.png)

[Watch the demo](https://github.com/avillagran/omarchy-dock/releases/download/v0.1.0/demo.mp4) · [Upstream PR](https://github.com/omacom/omarchy/pull/18712)

- One indicator segment per window, up to six; minimized windows are dimmed.
- Hover an app to browse its live windows. The selected preview highlights its indicator.
- Click a preview to focus its window; middle-click to close it.
- Stay over the previews for five seconds to reveal the size slider: beside a horizontal dock or below a vertical dock. Resize from 45% to 175%, limited by the screen, and keep the setting between sessions.
- Motion follows Omarchy's animation setting.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/avillagran/omarchy-dock/v0.1.1/install.sh | bash
```

Run from a terminal in your Omarchy desktop session. The installer downloads a pinned source archive, verifies its SHA-256, and asks for sudo only to apply the file transaction. The shell restarts afterward.

This is a source overlay for the built-in dock, not a marketplace plugin. It replaces five files under `/usr/share/omarchy/shell/plugins/dock` and keeps their previous contents under `/var/lib/omarchy-dock-overlay`. It does not change your pins or dock position. Omarchy package upgrades may replace the overlay. Reinstall only when the installer recognizes the package revision; it stops on unrecognized or locally edited dock files.

Supported source revisions are Omarchy 4.5.0 (`ac2690cd7`) and quattro (`ac6cb9c71`). Compatibility is checked against the actual file hashes, not just the package version or CPU architecture. x86_64 and aarch64 use the same QML sources.

The standard clone API does not expose the dock's app library and configuration access on these revisions, so this preview release uses an explicit, reversible overlay rather than a partially functioning third-party clone.

## Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/avillagran/omarchy-dock/v0.1.1/install.sh | bash -s -- --uninstall
```

This restores the exact files present before the first managed installation. If an Omarchy update or local edit has changed any managed file, uninstall stops rather than overwriting it. Backups remain available for inspection.

If you already installed an experimental copy of these exact sources by hand, that copy becomes the rollback baseline. To return to the stock dock after that, reinstall the Omarchy package instead.

## Inspect or install locally

```bash
git clone https://github.com/avillagran/omarchy-dock.git
cd omarchy-dock
./scripts/install-local.sh --check
./scripts/install-local.sh
./scripts/install-local.sh --uninstall
```

The two source variants are in `variants/`; their original and installed file hashes are in `variants.json`. `scripts/apply.py` validates the complete transaction before changing the dock. It rejects symlinks and preserves package updates, supports upgrades without replacing the original backup, and rolls back if a write fails.

## Development

```bash
python3 -m unittest discover -s tests -v
```

Tests use small retained fixture directories under `~/.cache/omarchy-dock-tests` (or `$TMPDIR`) and never recursively remove trees. No live desktop is changed by these tests.

The code is based on [Omarchy](https://github.com/omacom/omarchy), under its MIT license. The upstream contribution contains the dock changes only; this repository adds distribution and rollback tooling.
