#!/bin/bash
set -euo pipefail
bundle=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
command -v python3 >/dev/null
command -v omarchy-restart-shell >/dev/null
case "${1:-}" in
  '') action=() ;;
  --uninstall | --check) action=("$1") ;;
  *) echo 'Usage: install-local.sh [--uninstall|--check]' >&2; exit 1 ;;
esac
(( $# <= 1 )) || exit 1
if (( EUID == 0 )); then
  echo 'Run as your desktop user; sudo is used only for the file transaction.' >&2
  exit 1
fi
sudo python3 "$bundle/scripts/apply.py" --bundle "$bundle" "${action[@]}"
if [[ ${1:-} != --check ]]; then
  omarchy-restart-shell
fi
