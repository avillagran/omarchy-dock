#!/bin/bash
# Download and verify the immutable source bundle before requesting sudo.
set -euo pipefail
revision=f1838e9c9e11e6ccf6bc89b24625d9d68b5877bf
checksum=96d10a06c9062123f5b689bf8b0ba47cdfe4c356917dcd19ff03ee28d2499640
case "${1:-}" in
  '' | --check | --uninstall) ;;
  *) echo 'Usage: install.sh [--check|--uninstall]' >&2; exit 1 ;;
esac
(( $# <= 1 )) || exit 1
for dependency in curl tar sha256sum python3 sudo; do
  command -v "$dependency" >/dev/null || { echo "Missing dependency: $dependency" >&2; exit 1; }
done
command -v omarchy-restart-shell >/dev/null || { echo 'Run inside an Omarchy desktop session.' >&2; exit 1; }
cache=${XDG_CACHE_HOME:-$HOME/.cache}/omarchy-dock
mkdir -p "$cache"
work=$(mktemp -d "$cache/install.XXXXXXXX")
curl -fLsS --retry 2 "https://codeload.github.com/avillagran/omarchy-dock/tar.gz/$revision" -o "$work/source.tar.gz"
printf '%s  %s\n' "$checksum" "$work/source.tar.gz" | sha256sum --check --status
# GitHub's immutable archive has one top-level directory. Keep the verified
# cache for inspection rather than recursively deleting a downloaded tree.
tar -xzf "$work/source.tar.gz" -C "$work" --strip-components=1 --no-same-owner --no-same-permissions
exec bash "$work/scripts/install-local.sh" "$@"
