#!/usr/bin/env bash
export PYTHONDONTWRITEBYTECODE=1
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [[ $# != 1 || ! "$1" =~ ^task-[0-9]{3}$ ]]; then
  printf "Usage: ci/gate.sh task-NNN\n" >&2
  exit 2
fi
# No interpreter or resource preflight may precede the worktree check.
dirty=$(git status --porcelain=v1 --untracked-files=all -- . ":(exclude)docs/dev/STATUS.md" ":(exclude)docs/dev/deliver/$1")
if [[ -n "$dirty" ]]; then
  printf "Working tree differs from HEAD outside task records:\n%s\n" "$dirty" >&2
  exit 1
fi
exec systemd-run --user --scope -p CPUQuota=200% -p MemoryMax=3G -p MemorySwapMax=0 \
  nice -n 19 ionice -c3 python3.12 -B -m ci.gate_runtime "$1"
