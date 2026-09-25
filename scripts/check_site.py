"""Validate rendered pages, embedded comparison data and local links."""
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'


class Links(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.ids = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'id' in values:
            self.ids.append(values['id'])
        for attr in ('src', 'href'):
            if attr in values:
                self.links.append(values[attr])


for filename in ('index.html', 'compare.html'):
    page = SITE / filename
    html = page.read_text(encoding='utf-8')
    parsed = Links(html)
    assert len(parsed.ids) == len(set(parsed.ids)), f'Duplicate element IDs in {filename}'
    assert '{{<' not in html, f'Unexpanded shortcode in {filename}'
    assert 'data:image/png;base64,' in html, f'Logo is not embedded in {filename}'
    for href in parsed.links:
        target = urlsplit(href)
        if target.scheme or target.netloc or not target.path:
            continue
        assert not target.path.startswith('/'), f'Root-relative path breaks project Pages: {href}'
        assert (page.parent / unquote(target.path)).exists(), f'Broken local link: {filename}: {href}'

comparison = (SITE / 'compare.html').read_text(encoding='utf-8')
match = re.search(r'<script[^>]*id="comparison-data"[^>]*>(.*?)</script>', comparison, flags=re.S)
assert match, 'Missing embedded comparison data'
data = json.loads(match[1])
assert len(data['comparisons']) == len(data['versions']) ** 2
assert data['defaultTo'] == data['versions'][-1]['id']
assert data['comparisons']['v1.4:v1.5']['moved'] == 5
assert '<time datetime="2026-09-10">' in data['comparisons']['v1.4:v1.5']['html']
assert 'class="change-notes"' in data['comparisons']['v1.4:v1.5']['html']
for version, stamp in [('v1.0', '2022-10-16'), ('v1.1', '2023-01-16'),
                       ('v1.2', '2023-02-24'), ('v1.3', '2023-07-27'),
                       ('v1.4', '2024-09-02'), ('v1.5', '2026-09-10')]:
    assert f'id="revision-{version.replace(".", "-")}"' in comparison
    assert f'<time datetime="{stamp}">' in comparison
assert 'nachtmensch-oder-fruehaufsteher.de' in (SITE / 'index.html').read_text(encoding='utf-8')
digest = sha256((ROOT / 'assets/tscn-logo.png').read_bytes()).hexdigest()
assert digest == 'ad721549a8fd502f376ead0afa3426265bca46491607bfea3043db5e7dbb6ee3'
print(f'Validated both pages, local links, logo, dated change notes and {len(data["comparisons"])} comparisons.')
