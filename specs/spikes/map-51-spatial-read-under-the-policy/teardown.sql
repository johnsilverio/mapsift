-- Drops the fixture and grades the round the way `safety.sql` grades the instrument. Run it last,
-- and especially after `sweep_marked.sh` or `leak_wide.sql`: both mark functions LEAKPROOF inside a
-- transaction, and check 2 is what proves the rollback held.

\set ON_ERROR_STOP on
DROP SCHEMA IF EXISTS map51_probe CASCADE;

\echo '--- 1. no probe schema remains ---'
SELECT count(*) AS leftover_schemas FROM information_schema.schemata
WHERE schema_name LIKE 'map5%_probe' OR schema_name IN ('k','w','c','m51');

\echo '--- 2. nothing is marked LEAKPROOF, which is the state ADR-0013 decision 1 requires ---'
SELECT count(*) FILTER (WHERE proleakproof) AS marked, count(*) AS index_support_predicates
FROM pg_proc WHERE prosupport = 'postgis_index_supportfn'::regproc;
SELECT count(*) AS any_leakproof_postgis_function
FROM pg_depend d JOIN pg_extension e ON e.oid = d.refobjid JOIN pg_proc p ON p.oid = d.objid
WHERE d.refclassid = 'pg_extension'::regclass AND d.classid = 'pg_proc'::regclass
  AND e.extname LIKE 'postgis%' AND p.proleakproof;

\echo '--- 3. st_intersects carries its shipped declared cost again ---'
SELECT proleakproof, procost FROM pg_proc WHERE oid='st_intersects(geometry,geometry)'::regprocedure;

\echo '--- 4. extensions unchanged ---'
SELECT extname, extversion FROM pg_extension ORDER BY 1;

\echo '--- 5. the real table is untouched: this directory never writes outside map51_probe ---'
SELECT indexrelid::regclass::text AS idx, pg_get_indexdef(indexrelid)
FROM pg_index WHERE indrelid = 'public.layers_feature'::regclass ORDER BY 1;
SELECT relrowsecurity, relforcerowsecurity, (SELECT count(*) FROM public.layers_feature) AS rows
FROM pg_class WHERE oid = 'public.layers_feature'::regclass;
