-- ADR-0013 decision 1 ("the assertion is formally false") and decision 7 (the geometry_overlaps
-- alternative). Needs no fixture. Read-only, nothing is marked and nothing is created.
--
-- PostgreSQL's CREATE FUNCTION reference disqualifies a function that "throws an error message for
-- some argument values but not others, or which includes the argument values in any error message".
-- Part A finds the surfaces where st_intersects does exactly that. Part B is the negative result
-- that made geometry_overlaps the smaller assertion, and it is a negative result from a finite list
-- of attempts, never a proof that no input raises.

\pset border 2
\set ON_ERROR_STOP off

\echo '======== A. the error surfaces of the st_intersects family ========'
\echo '--- A1. st_intersects(geometry,geometry), mixed SRID: names both geometry types and both SRIDs ---'
SELECT ST_Intersects('SRID=4326;POINT(1.23456 -2.34567)'::geometry,
                     'SRID=4674;POLYGON((0 0,1 0,1 1,0 1,0 0))'::geometry);
\echo '--- A2. st_intersects(geometry,geometry), unsupported type: names the hidden row''s geometry type ---'
\echo '        this is the surface leak_wide.sql drives through the index-condition channel'
SELECT ST_Intersects('SRID=4674;POLYHEDRALSURFACE(((0 0,0 1,1 1,1 0,0 0)))'::geometry,
                     'SRID=4674;POINT(0 0)'::geometry);
\echo '--- A3. st_intersects(geography,geography), mixed SRID: type and SRID again, other overload ---'
SELECT ST_Intersects('SRID=4674;POINT(1 2)'::geography, 'SRID=4326;POINT(1 2)'::geography);
\echo '--- A4. st_intersects(text,text): the HINT quotes the argument value itself ---'
SELECT ST_Intersects('the-hidden-secret-value'::text, 'POINT(0 0)'::text);

\echo '--- A5. the same-shaped inputs that do NOT raise, which is the "for some argument values but'
\echo '        not others" half: a curved or collection geometry answers normally ---'
SELECT ST_Intersects('SRID=4674;CURVEPOLYGON(CIRCULARSTRING(0 0,1 1,2 0,1 -1,0 0))'::geometry,
                     'SRID=4674;POINT(1 0)'::geometry) AS curvepolygon,
       ST_Intersects('SRID=4674;TIN(((0 0,0 1,1 1,0 0)))'::geometry,
                     'SRID=4674;POINT(0 0)'::geometry) AS tin,
       ST_Intersects('SRID=4674;GEOMETRYCOLLECTION(POINT(1 1))'::geometry,
                     'SRID=4674;POINT(1 1)'::geometry) AS geometrycollection;

\echo '======== B. can geometry_overlaps (&&) be made to raise at all? ========'
DO $$
DECLARE probe record; raised int := 0; n int := 0; res boolean;
BEGIN
  FOR probe IN SELECT * FROM (VALUES
    ('mixed SRID',            'SRID=4326;POINT(1 1)',        'SRID=4674;POINT(1 1)'),
    ('SRID 0 vs 4674',        'SRID=0;POINT(1 1)',           'SRID=4674;POINT(1 1)'),
    ('empty polygon',         'SRID=4674;POLYGON EMPTY',     'SRID=4674;POINT(0 0)'),
    ('empty vs empty',        'SRID=4674;GEOMETRYCOLLECTION EMPTY','SRID=4674;POLYGON EMPTY'),
    ('PolyhedralSurface',     'SRID=4674;POLYHEDRALSURFACE(((0 0,0 1,1 1,1 0,0 0)))','SRID=4674;POINT(0 0)'),
    ('TIN',                   'SRID=4674;TIN(((0 0,0 1,1 1,0 0)))','SRID=4674;POINT(0 0)'),
    ('CircularString',        'SRID=4674;CIRCULARSTRING(0 0,1 1,2 0)','SRID=4674;POINT(0 0)'),
    ('CurvePolygon',          'SRID=4674;CURVEPOLYGON(CIRCULARSTRING(0 0,1 1,2 0,1 -1,0 0))','SRID=4674;POINT(1 0)'),
    ('CompoundCurve',         'SRID=4674;COMPOUNDCURVE(CIRCULARSTRING(0 0,1 1,2 0),(2 0,0 0))','SRID=4674;POINT(0 0)'),
    ('GeometryCollection',    'SRID=4674;GEOMETRYCOLLECTION(POINT(0 0),LINESTRING(1 1,2 2))','SRID=4674;POINT(0 0)'),
    ('bowtie (invalid ring)', 'SRID=4674;POLYGON((0 0,1 1,1 0,0 1,0 0))','SRID=4674;POLYGON((0 0,1 1,1 0,0 1,0 0))')
  ) AS t(label, a, b) LOOP
    n := n + 1;
    BEGIN
      EXECUTE format('SELECT %L::geometry && %L::geometry', probe.a, probe.b) INTO res;
      RAISE NOTICE '% -> returned %', rpad(probe.label,24), res;
    EXCEPTION WHEN OTHERS THEN
      raised := raised + 1;
      RAISE NOTICE '% -> RAISED: %', rpad(probe.label,24), SQLERRM;
    END;
  END LOOP;
  RAISE NOTICE 'inputs=% raised=%', n, raised;
END $$;

\echo '--- B2. NaN and Infinity, built through the constructor rather than through WKT ---'
SELECT ST_SetSRID(ST_MakePoint('NaN'::float8,0),4674) && 'SRID=4674;POINT(0 0)'::geometry AS nan_lhs,
       ST_SetSRID(ST_MakePoint('Infinity'::float8,0),4674) && 'SRID=4674;POINT(0 0)'::geometry AS inf_lhs;
