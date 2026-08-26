"""Reduce one psql run of gen_queries.sh to one JSON line per (config, prefix shape, box).

The fields ADR-0013 quotes are `buffers` (shared hit + read, on the plan root, cumulative for the
whole plan), `index_entries` (what the scan actually visited, which is the number the security half
of decision 2 turns on), `index_cond` and `ms`.
"""
import json, sys, re

cfg = sys.argv[1]
text = sys.stdin.read()
blocks = text.split('###MEASURE ')[1:]
for b in blocks:
    header = b.split('\n', 1)[0].strip()
    shape = re.search(r'shape=(\S+)', header).group(1)
    box = re.search(r'box=(\S+)', header).group(1)
    after = b.split('###PLAN', 1)[1]
    start = after.index('[')
    depth = 0
    for i in range(start, len(after)):
        if after[i] == '[':
            depth += 1
        elif after[i] == ']':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    plan = json.loads(after[start:end])[0]
    root = plan['Plan']

    nodes = []

    def walk(n):
        nodes.append(n)
        for c in n.get('Plans', []):
            walk(c)

    walk(root)

    def tot(n, *keys):
        return round(sum(float(n.get(k, 0)) for k in keys) * n.get('Actual Loops', 1))

    scans = ('Seq Scan', 'Parallel Seq Scan', 'Index Scan', 'Index Only Scan', 'Bitmap Heap Scan')
    scan = next((n for n in nodes if n['Node Type'] in scans + ('Bitmap Index Scan',)), None)
    idxnodes = [n for n in nodes if n['Node Type'] == 'Bitmap Index Scan']
    plantypes = ' > '.join(n['Node Type'] for n in nodes if n['Node Type'] != 'Aggregate')

    entries = None
    if idxnodes:
        entries = sum(tot(n, 'Actual Rows') for n in idxnodes)
    elif scan and scan['Node Type'] in ('Index Scan', 'Index Only Scan'):
        entries = tot(scan, 'Actual Rows', 'Rows Removed by Filter')

    heap = next((n for n in nodes if n['Node Type'] in scans), None)
    heap_rows = tot(heap, 'Actual Rows', 'Rows Removed by Filter', 'Rows Removed by Index Recheck') if heap else None
    out_rows = tot(heap, 'Actual Rows') if heap else None

    def first(key):
        return next((n[key] for n in nodes if key in n and n['Node Type'] != 'Aggregate'), None)

    print(json.dumps({
        'cfg': cfg, 'shape': shape, 'box': box, 'plan': plantypes,
        'index': first('Index Name'), 'index_cond': first('Index Cond'),
        'filter': (first('Filter') or '')[:110] or None,
        'index_entries': entries, 'heap_rows_examined': heap_rows, 'rows_out': out_rows,
        'buffers': int(root.get('Shared Hit Blocks', 0)) + int(root.get('Shared Read Blocks', 0)),
        'ms': round(plan['Execution Time'], 3)}))
