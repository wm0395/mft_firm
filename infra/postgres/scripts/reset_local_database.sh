#!/usr/bin/env bash
set -euo pipefail

if [[ "${RESET_CONFIRM:-}" != "yes" ]]; then
  echo "Set RESET_CONFIRM=yes to drop and recreate the local database."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
ENV_FILE="${ENV_FILE:-${REPO_ROOT}/.env}"

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

PGDATABASE="${PGDATABASE:-mft_platform}"

sudo -u postgres dropdb --if-exists "${PGDATABASE}"
"${SCRIPT_DIR}/init_database.sh"
