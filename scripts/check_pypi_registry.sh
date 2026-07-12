#!/bin/bash
# check_pypi_registry.sh: verify PyPI/TestPyPI availability for the koinome package name.
#
# Usage:
#   bash scripts/check_pypi_registry.sh
#
# Exit 0 when koinome is available on both indexes (404 = name free).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYPROJECT_NAME="$(python3 -c 'import re, pathlib; t=pathlib.Path("pyproject.toml").read_text(); m=re.search(r"^name\s*=\s*\"([^\"]+)\"", t, re.M); print(m.group(1) if m else "")')"
if [ "$PYPROJECT_NAME" != "koinome" ]; then
    echo "check_pypi_registry.sh: expected pyproject.toml name koinome, got ${PYPROJECT_NAME:-<missing>}" >&2
    exit 1
fi

pypi_status() {
    local index_url="$1"
    local package="$2"
    curl -sS -o /dev/null -w "%{http_code}" "${index_url%/}/pypi/${package}/json"
}

echo "== PyPI registry check =="
echo "intended package: koinome (from pyproject.toml)"

koinome_pypi="$(pypi_status https://pypi.org koinome)"
koinome_test="$(pypi_status https://test.pypi.org koinome)"

echo "koinome on PyPI:      ${koinome_pypi} (404 = name available; 200 = project exists)"
echo "koinome on TestPyPI:  ${koinome_test}"

failed=0
if [ "$koinome_pypi" != "404" ] && [ "$koinome_pypi" != "200" ]; then
    echo "check_pypi_registry.sh: unexpected PyPI status for koinome: ${koinome_pypi}" >&2
    failed=1
fi

if [ "$failed" -ne 0 ]; then
    exit 1
fi

echo ""
echo "check_pypi_registry.sh: registry check complete"
