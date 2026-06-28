#!/usr/bin/env python3
"""
extract_timeline.py — Parse Pdx-Unlimiter EU4 info-snapshot JSONs into a tidy timeline.

Pdx-Unlimiter stores each save snapshot in its own UUID folder; the per-snapshot
summary file is `info_<hash>.json`. CRITICAL QUIRK: every snapshot's info file is
named identically (same hash), so a flat `Compress-Archive` collapses them all to
ONE file on extract. This script handles a zip whose entries share a filename by
reading entries directly (not relying on extracted filenames).

Usage:
    python extract_timeline.py <input.zip | dir-of-jsons>  [--out timeline.json]

Outputs a JSON list of per-snapshot dicts sorted by in-game date, plus prints a
compact timeline table and a war-history table to stdout.

What the info files DO contain: date, player tag, ruler/heir, ducats(value+loans),
manpower, stability, prestige, monarch powers (adm/dip/mil), development
(totalDev/autonomyDev), allies, wars (opponent tags only), mods, dlcs, version.

What they DO NOT contain (need a melted gamestate instead): HRE reforms / imperial
authority / electors, province-level data, army/navy detail, war scores, exact
war declaration & peace dates (only snapshot-bounded estimates are possible).
"""
import json, sys, zipfile, glob, os, hashlib, argparse


def load_entries(path):
    """Yield raw JSON bytes for every info file, whether path is a zip or a dir.
    Handles the same-filename-collision quirk by reading zip entries directly."""
    blobs = []
    if path.lower().endswith('.zip'):
        with zipfile.ZipFile(path) as z:
            for zi in z.infolist():
                if zi.is_dir():
                    continue
                if not zi.filename.lower().endswith('.json'):
                    continue
                blobs.append(z.read(zi))
    elif os.path.isdir(path):
        for fp in glob.glob(os.path.join(path, '**', '*.json'), recursive=True):
            if os.path.basename(fp).startswith('campaign'):
                continue
            with open(fp, 'rb') as f:
                blobs.append(f.read())
    else:
        with open(path, 'rb') as f:
            blobs.append(f.read())
    return blobs


def parse_snapshot(d):
    data = d.get('data', {}) or {}
    date = data.get('date', {}) or {}
    y, m, dy = date.get('year'), date.get('month'), date.get('day')
    if y is None:
        return None
    powers = d.get('powers', {}) or {}
    dev = d.get('development', {}) or {}
    duc = d.get('ducats', {}) or {}
    mp = d.get('manpower', {}) or {}
    ruler_o = d.get('ruler', {}) or {}
    ruler = ruler_o.get('ruler', {}) if isinstance(ruler_o, dict) else {}
    allies = (d.get('allies', {}) or {}).get('tags', []) or []
    # wars: comps = list of wars; each war has tags = list of opponent countries
    comps = (d.get('wars', {}) or {}).get('comps', []) or []
    wars = []
    for w in comps:
        tags = [t.get('tag') for t in (w.get('tags', []) or []) if isinstance(t, dict)]
        if tags:
            wars.append(tags)
    return {
        'date': [y, m, dy],
        'sortkey': y * 10000 + m * 100 + dy,
        'tag': (data.get('tag', {}) or {}).get('tag'),
        'cash': duc.get('value'),
        'loans': duc.get('loans'),
        'totalDev': dev.get('totalDev'),
        'autonomyDev': dev.get('autonomyDev'),
        'prestige': (d.get('prestige') or {}).get('prestige'),
        'stability': (d.get('stability') or {}).get('stability'),
        'adm': powers.get('adm'), 'dip': powers.get('dip'), 'mil': powers.get('mil'),
        'mp': mp.get('value'), 'mpmax': mp.get('max'),
        'ruler': ruler.get('name'),
        'rulerStats': (f"{ruler.get('adm')}/{ruler.get('dip')}/{ruler.get('mil')}"
                       if ruler else None),
        'allies': [a.get('tag') for a in allies if isinstance(a, dict)],
        'wars': wars,
    }


def build(path):
    rows, seen = [], set()
    for blob in load_entries(path):
        try:
            d = json.loads(blob.decode('utf-8', 'replace'))
        except Exception:
            continue
        r = parse_snapshot(d)
        if not r:
            continue
        # dedup on (date, dev, cash) — Pdx-U sometimes writes duplicate snapshots
        key = (tuple(r['date']), r['totalDev'], r['cash'])
        if key in seen:
            continue
        seen.add(key)
        rows.append(r)
    rows.sort(key=lambda r: r['sortkey'])
    return rows


def war_history(rows):
    """Collapse consecutive snapshots into war intervals with snapshot bounds.
    Returns list of {opponents, first_seen, prev_peace, last_seen, next_peace}."""
    all_keys = {}
    for i, s in enumerate(rows):
        for w in s['wars']:
            k = tuple(sorted(w))
            all_keys.setdefault(k, []).append(i)
    out = []
    for k, idxs in sorted(all_keys.items(), key=lambda x: x[1][0]):
        first, last = idxs[0], idxs[-1]
        out.append({
            'opponents': list(k),
            'first_seen': rows[first]['date'],
            'prev_peace': rows[first - 1]['date'] if first > 0 else None,
            'last_seen': rows[last]['date'],
            'next_peace': rows[last + 1]['date'] if last + 1 < len(rows) else None,
        })
    return out


def fmt_date(d):
    return f"{d[0]:4d}.{d[1]:02d}.{d[2]:02d}" if d else "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input', help='zip of info JSONs, a directory, or one JSON')
    ap.add_argument('--out', default='/tmp/timeline.json')
    ap.add_argument('--wars-out', default='/tmp/wars.json')
    args = ap.parse_args()

    rows = build(args.input)
    if not rows:
        print("No valid snapshots found.", file=sys.stderr)
        sys.exit(1)
    json.dump(rows, open(args.out, 'w'), ensure_ascii=False)
    wars = war_history(rows)
    json.dump(wars, open(args.wars_out, 'w'), ensure_ascii=False)

    print(f"snapshots: {len(rows)}   range: {fmt_date(rows[0]['date'])} -> {fmt_date(rows[-1]['date'])}")
    print(f"player tag: {rows[-1]['tag']}")
    print()
    print(f"{'date':>11} {'dev':>5} {'cash':>7} {'loan':>6} {'pre':>4} {'st':>3} {'ADM':>4}/{'DIP':>4}/{'MIL':>4} ruler")
    for r in rows:
        print(f"{fmt_date(r['date'])} {str(r['totalDev']):>5} {str(r['cash']):>7} "
              f"{str(r['loans']):>6} {str(r['prestige']):>4} {str(r['stability']):>3} "
              f"{str(r['adm']):>4}/{str(r['dip']):>4}/{str(r['mil']):>4} {r['ruler'] or ''}")
    print()
    print("=== war history (snapshot-bounded) ===")
    print("opponents | declared between (prev_peace, first_seen) | ended between (last_seen, next_peace)")
    for w in wars:
        print(f"{'+'.join(w['opponents']):<40} "
              f"宣战:({fmt_date(w['prev_peace'])}, {fmt_date(w['first_seen'])})  "
              f"结束:({fmt_date(w['last_seen'])}, {fmt_date(w['next_peace'])})")
    print(f"\nsaved -> {args.out} , {args.wars_out}")


if __name__ == '__main__':
    main()
