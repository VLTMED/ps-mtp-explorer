"""Verify the pinned upstream review manifest. Uses HTTPS; writes no source files."""
import hashlib
import json
from pathlib import Path
import urllib.request

manifest = Path(__file__).resolve().parents[1] / 'docs' / 'sources.json'
entries = json.loads(manifest.read_text(encoding='utf-8'))['files']
for entry in entries:
    with urllib.request.urlopen(entry['raw_url'], timeout=30) as response:
        actual = hashlib.sha256(response.read()).hexdigest()
    if actual != entry['sha256']:
        raise SystemExit('HASH MISMATCH: ' + entry['raw_url'])
    print('Verified:', entry['repository'], entry['path'], entry['commit'])
