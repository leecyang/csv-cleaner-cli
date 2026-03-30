#!/usr/bin/env sh
set +e

PYTHON_BIN="python3"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  exit 1
fi

"$PYTHON_BIN" tests/test_logic.py --cleaner solution/cleaner.py
status=$?

if [ "$status" -eq 0 ]; then
  exit 0
fi

exit 1
