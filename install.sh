#!/bin/bash
# Download and verify the immutable source bundle before requesting sudo.
set -euo pipefail
revision=4ba87893e289f5684ff0d3cc3762f21513076b09
checksum=18428eb03d25522e765bf65749d6890a42625335071cebf1dfacdc279ecb8f6f
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
