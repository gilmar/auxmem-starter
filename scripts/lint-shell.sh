#!/bin/bash
# lint-shell.sh: shellcheck all project shell scripts (maintainer).
# Requires shellcheck on PATH. Uses bash 3.2 as the baseline for #!/bin/bash scripts.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v shellcheck >/dev/null 2>&1; then
    echo "shellcheck not found; install from https://www.shellcheck.net/" >&2
    exit 1
fi

failed=0
count=0
while IFS= read -r script; do
    count=$((count + 1))
    echo "shellcheck $script"
    if ! shellcheck -s bash "$script"; then
        failed=1
    fi
done < <(find auxmem/template auxmem/importers -type f \( -name '*.sh' -o -name 'pre-commit' \) | sort)

if [ "$failed" -ne 0 ]; then
    exit 1
fi

echo "shellcheck clean (${count} file(s))"

# smoke-test syntax under macOS-style bash 3.2 if available
if /bin/bash --version 2>/dev/null | grep -q 'version 3\.'; then
    echo "bash 3.2 syntax check"
    /bin/bash -n auxmem/template/.scripts/pre-commit
    /bin/bash -n auxmem/template/.scripts/auxmem-sync.sh
    /bin/bash -n auxmem/template/bootstrap.sh
    echo "bash -n clean"
fi
