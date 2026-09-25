# Shared visual identity

`projects.css` is copied from the lab's Projects website:
https://github.com/tscnlab/Projects/blob/main/assets/site.css

Source Git blob: `152fc388ef7d1eef60c2035dea7aa93a9427b41b`.
Retrieved 25 September 2026. `mission.css` contains the additions for this site.
The shared layout is adapted from `filters/layout.lua` in the same repository.

`tscn-logo.png` is the unmodified logo used there, originally from:
https://github.com/tscnlab/Templates/blob/main/logo/logo_with_text-01.png

SHA-256: `ad721549a8fd502f376ead0afa3426265bca46491607bfea3043db5e7dbb6ee3`.
The logo and institutional marks remain subject to their owners' rights.

## Favicon

`favicon.png` is the unmodified 363 × 363 circular mark used by the Projects
site, retrieved on 25 September 2026:
https://github.com/tscnlab/Projects/blob/main/assets/favicon.png

Source Git blob: `1b88df0071ab084ab860db93afc274f26796071b`.
SHA-256: `655bcfebe4c9844e7ee746e8636cafa2c3f0c63b09aa8fed60589c63bdcd8006`.

## Social preview

`social-preview.png` is a 1200 × 630 rendering of
`templates/social-preview.html`. The template and rendering script are adapted
from the Projects repository's `templates/social-preview.html` and
`scripts/render_social_preview.py`, retrieved on 25 September 2026.

The canonical logo, colours, typography and layout are retained. The heading
is “Mission statement” and the address is `tscnlab.github.io/MissionStatement`.
The logo is embedded unchanged. The PNG is committed so regular Quarto builds
do not require a browser or depend on the build machine's font selection.

Generated PNG SHA-256: `582e6a97c022d0f27fe4db351c70b01b4ee2adc7ff7bae89db9bd73b50ddd99c`.

Regenerate with `python scripts/render_social_preview.py` after installing
`requirements-dev.txt` and a Playwright Chromium browser. The optional
`PLAYWRIGHT_CHROMIUM_EXECUTABLE` environment variable selects an existing
Chromium-based browser instead.
