#!/usr/bin/env bash
# The only gate entry: preflight, constrained scope, then strictly serial checks.
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
report="docs/dev/deliver/task-001/gate_report.txt"
if [[ "${1:-}" != "--in-scope" ]]; then
  start=$SECONDS
  while true; do
    free -m
    cat /proc/loadavg
    available=$(awk '/MemAvailable:/ {print int($2/1024)}' /proc/meminfo)
    load=$(awk '{print $1}' /proc/loadavg)
    cores=$(nproc)
    if [[ "$available" -ge 4096 ]] && awk -v load="$load" -v cores="$cores" 'BEGIN {exit !(load <= cores/2)}'; then
      break
    fi
    if (( SECONDS - start >= 1800 )); then
      printf 'Resource preflight timed out\n' >&2
      exit 1
    fi
    sleep 15
  done
  mkdir -p "$(dirname "$report")"
  : > "$report"
  exec systemd-run --user --scope -p CPUQuota=200% -p MemoryMax=3G -p MemorySwapMax=0 \
    nice -n 19 ionice -c3 bash ci/gate.sh --in-scope
fi
exec > >(tee -a "$report") 2>&1
finish() {
  rc=$?
  status=fail
  [[ "$rc" == 0 ]] && status=ok
  printf 'ALL-END %s status=%s rc=%s\n' "$(date -u +%FT%TZ)" "$status" "$rc"
}
trap finish EXIT
# Do not trust the internal flag: verify the live cgroup limits.
cgroup=$(awk -F: '$1 == "0" {print $3}' /proc/self/cgroup)
limits="/sys/fs/cgroup${cgroup}"
[[ "$(cat "$limits/memory.max")" == 3221225472 ]]
[[ "$(cat "$limits/memory.swap.max")" == 0 ]]
awk '{exit !($1 != "max" && $1/$2 <= 2)}' "$limits/cpu.max"
printf "Verified cgroup cpu.max: %s; memory.max: %s; memory.swap.max: %s\n" \
  "$(cat "$limits/cpu.max")" "$(cat "$limits/memory.max")" "$(cat "$limits/memory.swap.max")"
export PYTHONDONTWRITEBYTECODE=1 UV_CONCURRENT_BUILDS=1 UV_CONCURRENT_DOWNLOADS=1
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
printf 'HEAD: %s\nTime: %s\n' "$(git rev-parse HEAD)" "$(date -u +%FT%TZ)"
printf 'Resources: CPUQuota=200%% MemoryMax=3G MemorySwapMax=0 nice=19 ionice=idle\n'
free -m
cat /proc/loadavg
sha256sum uv.lock
run() {
  label=$1
  shift
  begin=$SECONDS
  printf '\nGATE %s START\n' "$label"
  if "$@"; then
    printf 'GATE %s PASS elapsed=%ss\n' "$label" "$((SECONDS-begin))"
  else
    rc=$?
    printf 'GATE %s FAIL elapsed=%ss rc=%s\n' "$label" "$((SECONDS-begin))" "$rc"
    return "$rc"
  fi
}
lock_check() {
  uv lock --check --offline || return $?
  uv sync --locked --no-install-workspace --no-python-downloads || return $?
  uv sync --locked --all-packages --no-build-isolation --no-python-downloads || return $?
  .venv/bin/python --version
}
ruff_check() {
  .venv/bin/ruff check . || return $?
  .venv/bin/ruff format --check .
}
coverage_check() {
  .venv/bin/python -m pytest --cov --cov-report=term-missing --cov-report=json:.coverage.json -ra || return $?
  .venv/bin/python -m ci.coverage_check || return $?
  printf 'Provisional annotations: '
  # Count code annotations only; the empty register is not itself an implementation.
  (rg -o 'PROVISIONAL\([^)]*\)' framework agents conformance ci --glob '*.py' || true) | wc -l
}
run 1-lock lock_check
run 2-ruff ruff_check
run 3-mypy .venv/bin/mypy --strict
run 4-import-linter .venv/bin/lint-imports --no-cache
run 5-pytest-coverage coverage_check
run 6-d23 .venv/bin/python -m ci.checks d23
run 7-content .venv/bin/python -m ci.checks content
printf 'GATE 8-contract SKIP elapsed=0s 尚无 contracts 包，跳过并在报告中注明（仅目录空壳，无契约模型）\n'
printf 'GATE 9-cf SKIP elapsed=0s 尚无 contracts 包，跳过并在报告中注明（仅目录空壳，无 CF 实现）\n'
