#!/usr/bin/env bash
export PYTHONDONTWRITEBYTECODE=1
set -Eeuo pipefail
export UV_CONCURRENT_BUILDS=1 UV_CONCURRENT_DOWNLOADS=1
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
[[ ! ${CODINGSYSTEM_INTRANET+x} ]]
python3.12 -B -c "from ci.gate_runtime import effective_limits; effective_limits()"
run() {
  local label=$1 begin=$SECONDS rc
  shift
  printf "\nGATE %s START\n" "$label"
  if "$@"; then
    printf "GATE %s PASS elapsed=%ss\n" "$label" "$((SECONDS-begin))"
  else
    rc=$?
    printf "GATE %s FAIL elapsed=%ss rc=%s\n" "$label" "$((SECONDS-begin))" "$rc"
    return "$rc"
  fi
}
verify_python() {
  local actual
  actual=$(.venv/bin/python -B -c "import sys; print(str(sys.version_info.major) + chr(46) + str(sys.version_info.minor))") || return $?
  if [[ "$actual" != 3.12 ]]; then
    printf "Interpreter mismatch: expected 3.12, got %s\n" "$actual" >&2
    return 1
  fi
}
lock_check() {
  verify_python || return $?
  uv --version || return $?
  sha256sum uv.lock pyproject.toml .importlinter || return $?
  uv lock --check --offline || return $?
  uv sync --python /usr/bin/python3.12 --locked --no-install-workspace --no-python-downloads || return $?
  uv sync --python /usr/bin/python3.12 --locked --all-packages --no-build-isolation --no-python-downloads || return $?
  verify_python || return $?
  .venv/bin/python --version
}
ruff_check() {
  .venv/bin/ruff check . || return $?
  .venv/bin/ruff format --check .
}
coverage_check() {
  local -a namespace=()
  if unshare --user --net --map-current-user true 2>/dev/null; then
    namespace=(unshare --user --net --map-current-user)
    export CODINGSYSTEM_TEST_NETNS=on
  else
    export CODINGSYSTEM_TEST_NETNS=off
  fi
  printf "network-namespace: %s\n" "$CODINGSYSTEM_TEST_NETNS"
  "${namespace[@]}" .venv/bin/python -B -m pytest --cov --cov-report=term-missing --cov-report=json:.coverage.json -ra || return $?
  .venv/bin/python -B -m ci.coverage_check
}
run 1-lock lock_check
run 2-ruff ruff_check
run 3-mypy .venv/bin/mypy --strict
run 4-import-linter .venv/bin/lint-imports --no-cache
run 5-pytest-coverage coverage_check
run 6-d23 .venv/bin/python -B -m ci.checks d23
run 7-content .venv/bin/python -B -m ci.checks content
run 8-bypass .venv/bin/python -B -m ci.checks bypass
run 9-provisional .venv/bin/python -B -m ci.checks provisional
printf "GATE 10-contract SKIP elapsed=0s 尚无契约模型；将来比较 01 §0.3 契约包版本，非文档草案号\n"
printf "GATE 11-cf SKIP elapsed=0s 尚无 CF 实现；契约基线采用 01 §0.3 契约包版本\n"
