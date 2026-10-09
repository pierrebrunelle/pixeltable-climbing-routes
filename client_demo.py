"""Call every route of the climbing-route topo API.

Usage:
    python client_demo.py                             # local service (pxt service run ... --port 8000)
    python client_demo.py https://<your-service-url>  # hosted service; set PIXELTABLE_API_KEY first

Uses only the Python standard library. The API key, if any, is read from the
PIXELTABLE_API_KEY environment variable and sent as the X-api-key header.
"""
from __future__ import annotations

import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8000').rstrip('/')
API_KEY = os.environ.get('PIXELTABLE_API_KEY')
DATA = Path(__file__).resolve().parent / 'data'


def _headers(extra: dict | None = None) -> dict:
    h = dict(extra or {})
    if API_KEY:
        h['X-api-key'] = API_KEY
    return h


def get_json(path: str, params: dict) -> object:
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f'{BASE}{path}?{qs}', headers=_headers())
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def get_bytes(path: str, params: dict) -> tuple[bytes, str]:
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f'{BASE}{path}?{qs}', headers=_headers())
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read(), resp.headers.get('Content-Type', '')


def post_multipart(path: str, fields: dict[str, str], files: dict[str, Path]) -> object:
    boundary = '----PixeltableClimbingDemoBoundary'
    body = bytearray()
    for name, value in fields.items():
        body.extend(f'--{boundary}\r\n'.encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(f'{value}\r\n'.encode())
    for name, path in files.items():
        data = path.read_bytes()
        ctype = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        body.extend(f'--{boundary}\r\n'.encode())
        body.extend(
            f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'.encode()
        )
        body.extend(f'Content-Type: {ctype}\r\n\r\n'.encode())
        body.extend(data)
        body.extend(b'\r\n')
    body.extend(f'--{boundary}--\r\n'.encode())
    req = urllib.request.Request(
        f'{BASE}{path}',
        data=bytes(body),
        headers=_headers({'Content-Type': f'multipart/form-data; boundary={boundary}'}),
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def main() -> None:
    print('by-crag', get_json('/routes/by-crag', {'crag': 'Red Rocks'}))
    print('by-band', get_json('/routes/by-band', {'band': 'hard', 'style': 'sport'}))
    print('detail', get_json('/routes/detail', {'name': 'Sunset Arete'}))
    blob, ctype = get_bytes('/routes/thumb', {'name': 'Sunset Arete'})
    print('thumb bytes', len(blob), 'content-type', ctype)
    print(
        'analyze',
        post_multipart(
            '/analyze',
            {'grade': '5.9', 'style': 'boulder'},
            {'topo': DATA / 'slab-morning.png'},
        ),
    )
    print(
        'insert',
        post_multipart(
            '/routes',
            {
                'name': 'Demo Boulder',
                'crag': 'Bishop',
                'grade': '5.10b',
                'style': 'boulder',
                'bolts': '',
                'length_m': '4.0',
            },
            {'topo': DATA / 'crack-line.png'},
        ),
    )


if __name__ == '__main__':
    main()
