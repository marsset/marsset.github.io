"""Refresh the blog's same-origin DVOL snapshot. Public API only; stdlib, Python >=3.9."""
import json
import math
from pathlib import Path
import time
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'assets/data/btc-dvol.json'
API = 'https://www.deribit.com/api/v2/public/'


def get(method):
    for attempt in range(3):
        try:
            request = urllib.request.Request(API + method, headers={'User-Agent': 'marsset-blog-dvol/1.0'})
            with urllib.request.urlopen(request, timeout=15) as response:
                body = json.load(response)
            if body.get('error') or not isinstance(body.get('result'), dict):
                raise ValueError('Deribit returned no usable result')
            return body['result']
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def refresh():
    end = int(time.time() * 1000)
    start = end - 30 * 86400000
    result = get(f'get_volatility_index_data?currency=BTC&resolution=3600&start_timestamp={start}&end_timestamp={end}')
    points = {}
    for row in result.get('data', []):
        if isinstance(row, list) and len(row) >= 5 and positive(row[0]) and positive(row[4]):
            if start - 3600000 <= row[0] <= end:
                points[int(row[0])] = row[4]
    series = sorted(points.items())
    if len(series) < 2 or series[-1][0] < end - 2 * 3600000:
        raise ValueError('DVOL history is empty or stale; preserving the previous snapshot')
    updated = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    btc = None
    try:
        value = get('get_index_price?index_name=btc_usd').get('index_price')
        if positive(value):
            btc = {'price': value, 'updated_at': datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')}
    except Exception as error:
        print(f'BTC price unavailable; publishing DVOL without a dollar estimate: {error}')
    snapshot = {'currency': 'BTC', 'resolution_seconds': 3600, 'updated_at': updated, 'series': series, 'btc': btc}
    DEST.parent.mkdir(parents=True, exist_ok=True)
    temporary = DEST.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(snapshot, separators=(',', ':'), allow_nan=False) + '\n')
    temporary.replace(DEST)
    print(f'Updated {DEST.name}: {len(series)} hourly points; latest DVOL {series[-1][1]}%')


if __name__ == '__main__':
    refresh()
