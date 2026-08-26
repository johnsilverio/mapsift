-- ADR-0013 Context: the census that says no PostGIS predicate is leakproof as shipped, and the
-- declared costs decision 7 and the leak's reachability argument both turn on.
-- Needs no fixture. Read-only.

\pset border 2
\echo '--- every extension in this database, and how much of it is leakproof (postgis: 0 of 776, btree_gist: 0 of 212) ---'
SELECT e.extname, count(*) FILTER (WHERE p.proleakproof) AS leakproof, count(*) AS total
FROM pg_depend d JOIN pg_extension e ON e.oid = d.refobjid JOIN pg_proc p ON p.oid = d.objid
WHERE d.refclassid = 'pg_extension'::regclass AND d.classid = 'pg_proc'::regclass
GROUP BY 1 ORDER BY 1;

\echo '--- the 21 predicates carrying postgis_index_supportfn: the only ones a rewrite can turn into an index cond ---'
SELECT count(*) FILTER (WHERE proleakproof) AS leakproof, count(*) AS total
FROM pg_proc WHERE prosupport = 'postgis_index_supportfn'::regproc;
SELECT p.oid::regprocedure AS func, p.proleakproof, p.procost
FROM pg_proc p WHERE p.prosupport = 'postgis_index_supportfn'::regproc ORDER BY 1;

\echo '--- the 14 gist_geometry_ops_2d members: what an index cond on a plain GiST can be built from ---'
SELECT count(*) FILTER (WHERE p.proleakproof) AS leakproof, count(*) AS total
FROM pg_amop amop JOIN pg_opclass opc ON opc.opcfamily = amop.amopfamily
JOIN pg_operator opr ON opr.oid = amop.amopopr JOIN pg_proc p ON p.oid = opr.oprcode
WHERE opc.opcname = 'gist_geometry_ops_2d' AND amop.amoplefttype = 'geometry'::regtype;

\echo '--- the four functions the decision names one by one ---'
\echo '    uuid_eq leakproof=t is what decision 2 rests on; st_intersects cost 5000 is the residual decision 1 closes'
SELECT p.oid::regprocedure AS func, p.proleakproof, p.procost, p.prosupport::regprocedure AS support
FROM pg_proc p WHERE p.oid IN (
 'st_intersects(geometry,geometry)'::regprocedure,
 'geometry_overlaps(geometry,geometry)'::regprocedure,
 'uuid_eq(uuid,uuid)'::regprocedure,
 'current_setting(text,boolean)'::regprocedure) ORDER BY 1;

\echo '--- the marking is superuser-only (dependencies.md item 18): the function OWNER is refused ---'
BEGIN;
CREATE ROLE map51_owner_probe;
ALTER FUNCTION st_intersects(geometry,geometry) OWNER TO map51_owner_probe;
DO $$
BEGIN
  SET LOCAL ROLE map51_owner_probe;
  ALTER FUNCTION st_intersects(geometry,geometry) LEAKPROOF;
  RAISE NOTICE 'the owner was ALLOWED to mark it, which contradicts ADR-0013';
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'refused, as ADR-0013 records: %', SQLERRM;
END $$;
ROLLBACK;
SELECT proleakproof AS still_unmarked_after_rollback
FROM pg_proc WHERE oid = 'st_intersects(geometry,geometry)'::regprocedure;
