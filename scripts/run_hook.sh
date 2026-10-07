#!/bin/sh
# awesome-github-readme: start readme_hook.py with whichever Python 3 runs.
# Windows often has no python3, or only the Microsoft Store stub that exits
# 9009, so probe rather than assume. The probe reads nothing from stdin, so
# the hook's JSON input still reaches the script. No interpreter: stay quiet.
for p in python3 python py; do
  if "$p" -c 'import sys; sys.exit(sys.version_info < (3, 9))' </dev/null >/dev/null 2>&1; then
    exec "$p" "$(dirname "$0")/readme_hook.py"
  fi
done
exit 0
