#!/bin/bash
# The migrate profile of ADR-0005 section 2. It is the one role that cannot come from the first
# migration where that ADR puts the other three: it has to exist before a migration can run, and a
# credential does not belong in a tracked file (N3, C6).
#
# NOSUPERUSER and NOBYPASSRLS are the defaults and are written out anyway, because the whole wall
# is void for a role holding either and the test suite connects as this one. CREATEDB is for the
# test database Django builds and drops; CREATEROLE is for the three roles the migration creates.

set -euo pipefail

psql -v ON_ERROR_STOP=1 \
     --username "$POSTGRES_USER" \
     --dbname "$POSTGRES_DB" \
     -v owner_password="$DB_OWNER_PASSWORD" \
     -v database="$POSTGRES_DB" <<-'EOSQL'
	CREATE ROLE mapsift_owner
	    LOGIN PASSWORD :'owner_password'
	    NOSUPERUSER NOBYPASSRLS CREATEDB CREATEROLE;

	-- Handing over the database rather than the schema is what makes development match the test
	-- run: `public` belongs to `pg_database_owner`, so the database Django creates for the suite
	-- resolves the same way with no second rule to keep in step.
	ALTER DATABASE :"database" OWNER TO mapsift_owner;
EOSQL
