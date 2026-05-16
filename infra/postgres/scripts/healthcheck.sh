#!/usr/bin/env bash
set -euo pipefail

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
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-mft}"
PGPASSWORD="${PGPASSWORD:-mft}"

pg_isready -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" >/dev/null

schema_and_view_count="$(
  PGPASSWORD="${PGPASSWORD}" psql -v ON_ERROR_STOP=1 -At \
    -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" \
    -c "select
            (select count(*) from information_schema.schemata where schema_name in ('market_raw', 'mft'))
          + (select count(*) from information_schema.views
             where table_schema = 'market_raw'
               and table_name = 'ohlcv_deduplicated');"
)"

[[ "${schema_and_view_count}" == "3" ]]
