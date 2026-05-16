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

sudo -u postgres psql -v ON_ERROR_STOP=1 -d postgres \
  -v dbname="${PGDATABASE}" -v dbuser="${PGUSER}" -v dbpass="${PGPASSWORD}" <<'SQL'
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'dbuser') THEN
        EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', :'dbuser', :'dbpass');
    ELSE
        EXECUTE format('ALTER ROLE %I LOGIN PASSWORD %L', :'dbuser', :'dbpass');
    END IF;
END
$$;

SELECT format('CREATE DATABASE %I OWNER %I', :'dbname', :'dbuser')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'dbname')
\gexec

ALTER DATABASE :"dbname" OWNER TO :"dbuser";
SQL

PGPASSWORD="${PGPASSWORD}" psql -v ON_ERROR_STOP=1 \
  -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" \
  -f "${REPO_ROOT}/infra/postgres/init/001_market_raw_schema.sql"

PGPASSWORD="${PGPASSWORD}" psql -v ON_ERROR_STOP=1 \
  -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" \
  -f "${REPO_ROOT}/infra/postgres/init/002_mft_schema.sql"
