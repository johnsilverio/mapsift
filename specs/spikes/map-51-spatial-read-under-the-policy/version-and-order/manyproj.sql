\set ON_ERROR_STOP on
DROP SCHEMA IF EXISTS mp CASCADE;
CREATE SCHEMA mp;
CREATE TABLE mp.feature (LIKE map51_probe.feature INCLUDING ALL);
ALTER TABLE mp.feature ENABLE ROW LEVEL SECURITY;
ALTER TABLE mp.feature FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON mp.feature
    USING (tenant_id = nullif(current_setting('mapsift.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = nullif(current_setting('mapsift.tenant_id', true), '')::uuid);
GRANT USAGE ON SCHEMA mp TO mapsift_app;
GRANT SELECT ON mp.feature TO mapsift_app;

-- 2 tenants x 400 projects x 2 layers (1000 + 100 rows) = 880,000 rows, heap clustered by layer.
CREATE TABLE mp.plan AS
SELECT ti, pi, li, (ARRAY[1000,100])[li] AS fcount,
       ('aaaaaaaa-0000-0000-0000-' || lpad(ti::text,12,'0'))::uuid AS tenant_id,
       ('bbbbbbbb-0000-0000-0000-' || lpad(((ti-1)*400+pi)::text,12,'0'))::uuid AS project_id,
       ('cccccccc-0000-0000-0000-' || lpad(((ti-1)*800+(pi-1)*2+li)::text,12,'0'))::uuid AS layer_id
FROM generate_series(1,2) a(ti), generate_series(1,400) b(pi), generate_series(1,2) c(li);

INSERT INTO mp.feature (id, geometry, project_id, tenant_id, layer_id)
SELECT ('22222222-0000-0000-0000-'||lpad((row_number() OVER ())::text,12,'0'))::uuid,
       map51_probe.ring(-50.0+5.0*map51_probe.r('x'||p.layer_id||'-'||s.fi),
                        -20.0+5.0*map51_probe.r('y'||p.layer_id||'-'||s.fi), 8),
       p.project_id, p.tenant_id, p.layer_id
FROM mp.plan p, LATERAL generate_series(1,p.fcount) s(fi)
ORDER BY p.ti, p.pi, p.li, s.fi;
ANALYZE mp.feature;
SELECT count(*) AS rows, count(DISTINCT project_id) AS projects, count(DISTINCT layer_id) AS layers FROM mp.feature;
