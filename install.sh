#!/bin/bash
# Download and verify the immutable source bundle before requesting sudo.
set -euo pipefail
revision=08f86fea384b793456ce01a64cd781bcad34a37f
checksum=b943772e9d61c2bf56bd1a9bcd9cc1a595f444a7d7b3942e883b811e9c4d6a85
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
if ! printf '%s  %s\n' "$checksum" "$work/source.tar.gz" | sha256sum --check --status; then
  echo 'Archive checksum mismatch; nothing was installed.' >&2
  exit 1
fi
# GitHub's immutable archive has one top-level directory. Keep the verified
# cache for inspection rather than recursively deleting a downloaded tree.
tar -xzf "$work/source.tar.gz" -C "$work" --strip-components=1 --no-same-owner --no-same-permissions
exec bash "$work/scripts/install-local.sh" "$@"
