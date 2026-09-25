#!/usr/bin/env python3
"""Render the HTML social card; the canonical logo image is embedded unchanged."""
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def render():
    target = ROOT / 'assets/social-preview.png'
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE') or None)
        page = browser.new_page(viewport={'width': 1200, 'height': 630}, device_scale_factor=1, color_scheme='light')
        page.goto((ROOT / 'templates/social-preview.html').as_uri(), wait_until='networkidle')
        page.evaluate('document.fonts.ready')
        assert page.locator('img').evaluate('(img) => img.complete && img.naturalWidth > 0'), 'Logo did not load'
        assert page.evaluate('document.documentElement.scrollWidth === 1200 && document.documentElement.scrollHeight === 630'), 'Social card overflows'
        page.screenshot(path=str(target))
        browser.close()
    print(f'Rendered {target.relative_to(ROOT)} (1200 × 630).')


if __name__ == '__main__':
    render()
