-- ADR-0013 decision 7: the covering index refuses the write. Run this with `include.sql`'s p_inc in
-- place, or it proves nothing, because the limit belongs to the btree tuple and not to the table.
--
-- Every insert below is undone: the block ends by raising, which rolls the whole DO back. The
-- closing count is the check that it did.

\set ON_ERROR_STOP off
SELECT count(*) AS rows_before FROM map51_probe.feature;
DO $$
DECLARE n int; sz int;
BEGIN
  FOREACH n IN ARRAY ARRAY[100,160,200,220,250,256,260,270,280,300,360,500,2000] LOOP
    BEGIN
      sz := pg_column_size(map51_probe.ring(-47.5,-17.5,n));
      INSERT INTO map51_probe.feature VALUES (gen_random_uuid(), map51_probe.ring(-47.5,-17.5,n),
        'bbbbbbbb-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000001',
        'cccccccc-0000-0000-0000-000000000001');
      RAISE NOTICE 'ring segments=% geometry_bytes=% -> ACCEPTED', lpad(n::text,4), sz;
    EXCEPTION WHEN OTHERS THEN
      RAISE NOTICE 'ring segments=% geometry_bytes=% -> REFUSED: %', lpad(n::text,4), sz, SQLERRM;
    END;
  END LOOP;
  RAISE EXCEPTION 'probe finished, undoing every insert above';
END $$;
SELECT count(*) AS rows_after FROM map51_probe.feature;
