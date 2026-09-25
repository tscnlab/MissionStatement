"""Validate rendered pages, embedded comparison data and local links."""
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import base64
import json
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'


class Links(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.ids = []
        self.meta = {}
        self.icons = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'meta':
            key = values.get('property', values.get('name'))
            if key:
                self.meta.setdefault(key, []).append(values.get('content', ''))
        if tag == 'link' and 'icon' in values.get('rel', '').split():
            self.icons.append(values.get('href', ''))
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
    title = 'Mission statement' if filename == 'index.html' else 'Compare versions'
    expected_image = 'https://tscnlab.github.io/MissionStatement/assets/social-preview.png'
    for prefix in ('og', 'twitter'):
        assert parsed.meta.get(f'{prefix}:image') == [expected_image], f'Wrong sharing image URL in {filename}'
        assert parsed.meta.get(f'{prefix}:title') == [f'{title} – TSCN'], f'Wrong sharing title in {filename}'
        description = parsed.meta.get(f'{prefix}:description', [])
        assert len(description) == 1 and description[0], f'Missing sharing description in {filename}'
        assert parsed.meta.get(f'{prefix}:image:alt') == [
            'Mission statement of the Translational Sensory & Circadian Neuroscience Unit (MPS/TUM/TUMCREATE).'
        ], f'Missing sharing image description in {filename}'
    assert parsed.meta.get('twitter:card') == ['summary_large_image']
    assert parsed.meta.get('og:image:width') == ['1200']
    assert parsed.meta.get('og:image:height') == ['630']
    assert len(parsed.icons) == 1, f'Missing or duplicate favicon in {filename}'
    icon = parsed.icons[0]
    if icon.startswith('data:image/png;base64,'):
        icon_bytes = base64.b64decode(icon.split(',', 1)[1])
    else:
        assert not urlsplit(icon).scheme, 'Expected a local or embedded favicon'
        icon_bytes = (page.parent / unquote(icon)).read_bytes()
    assert icon_bytes == (ROOT / 'assets/favicon.png').read_bytes(), f'Wrong favicon in {filename}'
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
assert sha256((ROOT / 'assets/favicon.png').read_bytes()).hexdigest() == '655bcfebe4c9844e7ee746e8636cafa2c3f0c63b09aa8fed60589c63bdcd8006'
for name, size in [('favicon.png', (363, 363)), ('social-preview.png', (1200, 630))]:
    source = (ROOT / 'assets' / name).read_bytes()
    assert source.startswith(b'\x89PNG\r\n\x1a\n')
    assert struct.unpack('>II', source[16:24]) == size
    assert (SITE / 'assets' / name).read_bytes() == source, f'Public asset differs from source: {name}'
print(f'Validated both pages, favicon, social metadata, assets, dated change notes and {len(data["comparisons"])} comparisons.')
