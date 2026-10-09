"""Seed a few climbing routes with topo images (run after schema update).

Usage:
    python seed.py climbing
"""
from __future__ import annotations

import sys
from pathlib import Path

import pixeltable as pxt

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'


def main(catalog: str = 'climbing') -> None:
    t = pxt.get_table(f'{catalog}/routes')
    rows = [
        dict(
            name='Sunset Arete',
            crag='Red Rocks',
            grade='5.10a',
            style='sport',
            bolts=9,
            length_m=28.0,
            topo=str(DATA / 'arete-sunset.png'),
        ),
        dict(
            name='Morning Slab',
            crag='Joshua Tree',
            grade='5.8',
            style='trad',
            bolts=None,
            length_m=35.0,
            topo=str(DATA / 'slab-morning.png'),
        ),
        dict(
            name='Crux Overhang',
            crag='Red Rocks',
            grade='5.12c',
            style='sport',
            bolts=12,
            length_m=22.5,
            topo=str(DATA / 'overhang-crux.png'),
        ),
        dict(
            name='Thin Crack',
            crag='Indian Creek',
            grade='5.11b',
            style='trad',
            bolts=None,
            length_m=40.0,
            topo=str(DATA / 'crack-line.png'),
        ),
    ]
    # skip rows whose name already exists
    existing = {r['name'] for r in t.select(t.name).collect()}
    fresh = [r for r in rows if r['name'] not in existing]
    if not fresh:
        print(f'{catalog}/routes already has the sample names ({t.count()} rows)')
        return
    status = t.insert(fresh)
    print(f'inserted {len(fresh)} rows -> count={t.count()} status={status}')
    print(t.select(t.name, t.crag, t.grade, t.aspect, t.band, t.tag).collect())


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'climbing')
