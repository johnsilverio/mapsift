"""Render the ADR-0013 tables out of one or more sweep jsonl files.

  report.py law     <jsonl> [cfg]   the prefix law and the buffers-per-prefix-row fit
  report.py box     <jsonl> [cfg]   the same prefix across every box, which is the independence claim
  report.py compare <a.jsonl> <b.jsonl> [cfgA] [cfgB]   buffers side by side, with the ratio
  report.py check   <jsonl> <heap>  a fresh run against baseline.jsonl; <heap> is clustered|scattered

`check` is the only one that grades rather than reports, and it deliberately ignores milliseconds:
buffers, index entries and the index condition are what transfer between machines (README, "Before
trusting a number from this"), and a run whose timings drift is a machine, while a run whose buffers
or plan shape drift is a finding.
"""
import json, os, sys
from collections import OrderedDict

PREFIX_ROWS = OrderedDict([
    ('tenant', 1044000), ('proj', 261000), ('lany', 261000),
    ('l200k', 200000), ('l50k', 50000), ('l10k', 10000), ('l1k', 1000)])


def load(path, cfg=None):
    rows = [json.loads(l) for l in open(path)]
    if cfg:
        rows = [r for r in rows if r['cfg'] == cfg]
    return rows


def law(path, cfg=None, box='b12'):
    rows = [r for r in load(path, cfg) if r['box'] == box]
    print(f"{'cfg':24} {'prefix':7} {'rows':>9} {'entries':>9} {'buffers':>9} {'ms':>9}  buf/row")
    for r in sorted(rows, key=lambda r: -PREFIX_ROWS.get(r['shape'], 0)):
        n = PREFIX_ROWS.get(r['shape'], 0)
        print(f"{r['cfg']:24} {r['shape']:7} {n:>9} {str(r['index_entries']):>9} "
              f"{r['buffers']:>9} {r['ms']:>9}  {r['buffers']/n if n else 0:.4f}")


def box(path, cfg=None):
    rows = load(path, cfg)
    shapes = sorted({r['shape'] for r in rows}, key=lambda s: -PREFIX_ROWS.get(s, 0))
    boxes = ['b12', 'b10', 'b8', 'b6']
    print(f"{'prefix':7} " + ' '.join(f'{b:>12}' for b in boxes) + '   (buffers)')
    for s in shapes:
        cells = []
        for b in boxes:
            m = [r for r in rows if r['shape'] == s and r['box'] == b]
            cells.append(f"{m[0]['buffers']:>12}" if m else f"{'-':>12}")
        print(f"{s:7} " + ' '.join(cells))


def compare(a, b, cfga=None, cfgb=None):
    A = {(r['shape'], r['box']): r for r in load(a, cfga)}
    B = {(r['shape'], r['box']): r for r in load(b, cfgb)}
    print(f"{'prefix':7} {'box':4} {'A buffers':>11} {'B buffers':>11} {'B/A':>7} {'A ms':>10} {'B ms':>10}")
    for k in sorted(A, key=lambda k: (-PREFIX_ROWS.get(k[0], 0), k[1])):
        if k not in B:
            continue
        x, y = A[k]['buffers'], B[k]['buffers']
        print(f"{k[0]:7} {k[1]:4} {x:>11} {y:>11} {y/x if x else 0:>7.1f} {A[k]['ms']:>10} {B[k]['ms']:>10}")


def fixture_scale(rows):
    """The tenant prefix the run was taken on, which is what tells two fixture generations apart."""
    seen = [r['index_entries'] for r in rows if r.get('index_entries')]
    return max(seen) if seen else None


def check(path, heap):
    base = [r for r in (json.loads(l) for l in
                        open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'baseline.jsonl')))
            if r['heap'] == heap]
    run = load(path)

    # TRAP, and it is why this guard runs before anything is compared. The key (cfg, shape, box) is
    # NOT unique across fixture generations: the round's own pre-v2 files carry cfg5_gist_tl cells
    # whose keys collide with this baseline's while their tenant prefix is 200,000 rows against
    # 1,044,000. Keyed alone, sixteen of them pair up and report as differences that are a different
    # fixture rather than a finding.
    b_scale, n_scale = fixture_scale(base), fixture_scale(run)
    if b_scale and n_scale and b_scale != n_scale:
        print(f"REFUSED: this run was taken on a different fixture. Its largest prefix is "
              f"{n_scale} rows; the baseline's is {b_scale}. Rebuild with this directory's "
              f"build.sql, which makes a 2,088,000-row fixture with a 1,044,000-row tenant prefix.")
        return 2

    B = {(r['cfg'], r['shape'], r['box']): r for r in base}
    N = {(r['cfg'], r['shape'], r['box']): r for r in run}
    keys = sorted(set(B) & set(N))
    missing = sorted(set(N) - set(B))
    fields = ('buffers', 'index_entries', 'plan', 'index', 'index_cond')
    bad = 0
    for k in keys:
        for f in fields:
            b, n = B[k][f], N[k][f]
            if f == 'index_cond' and n:
                import re
                n = re.sub(r"'[0-9A-F]{20,}'", "'<geom>'", n)
            if b != n:
                bad += 1
                print(f"DIFF {'/'.join(k):45} {f:13} baseline={b!r} run={n!r}")
    print(f"compared {len(keys)} cells against baseline heap={heap}: "
          f"{'all identical' if not bad else str(bad) + ' DIFFERENCES'}")
    if missing:
        print(f"not in the baseline, so not graded: {len(missing)} cells "
              f"({', '.join(sorted({k[0] for k in missing}))})")
    return 1 if bad else 0


if __name__ == '__main__':
    cmd, args = sys.argv[1], sys.argv[2:]
    sys.exit({'law': law, 'box': box, 'compare': compare, 'check': check}[cmd](*args) or 0)
