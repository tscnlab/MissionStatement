# Mission statement

The principles of the Translational Sensory & Circadian Neuroscience Unit
(MPS/TUM/TUMCREATE), revised at the lab retreat in Milan on 10 September 2026.

## Source and version convention

- `MissionStatement_Current.md` is the current statement.
- `MissionStatement_YYYY.MM.DD_vX.Y.md` is a dated snapshot, following the
  existing convention. The latest is `MissionStatement_2026.09.10_v1.5.md`.
- The current file and latest snapshot must be byte-for-byte identical.
- Preserve historical snapshots. The comparison page discovers dated files
  automatically; it does not need a manually maintained version list.

The 2026 revision adds the roadshow and concrete open-science practices,
acknowledges the resources needed for replication and past wellbeing challenges,
includes chronotype-friendly work, replaces the one-in-five student-project
target with intentional resource use, and removes the privacy sentence.
The principles are ordered: culture, meaningful science, wellbeing, open science,
reproducibility, sustainability.

## Reproduce the website

The main outputs are two reproducible Quarto notebooks and their rendered HTML:

| Source | Rendered output | Purpose |
| --- | --- | --- |
| `index.qmd` | `_site/index.html` | Current statement |
| `compare.qmd` | `_site/compare.html` | Compare any two available versions |

Use Quarto **1.6.43** and Python **3.12 or newer**. The GitHub workflow pins
Quarto and the direct notebook dependencies; Python comparison code uses only
the standard library. Pandoc is supplied by Quarto.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
quarto render
python scripts/check_site.py
node tests/check_controls.cjs
quarto preview
```

If Quarto selects a different Python installation, set `QUARTO_PYTHON` to the
interpreter containing the installed notebook dependencies. This checkout was
rendered with `QUARTO_PYTHON="$PWD/.venv/bin/python" quarto render`.

Both HTML pages embed their scripts, styles and logo, so they can be opened
directly or emailed. Share the full `_site/` folder to retain navigation between
pages and the Markdown download links. A comparison URL can specify its versions,
for example `compare.html?from=v1.4&to=v1.5`.

## How comparisons work

`compare.qmd` reads the dated Markdown snapshots using `scripts/mission_site.py`.
Python's `difflib.SequenceMatcher` compares visible words within matching section
headings. Pandoc preserves links, emphasis, paragraphs and subscripts. Removed
words are struck through and additions are underlined, with background colours
as a second cue. Section positions are reported independently of wording.

The expandable exact Markdown diffs also show changes to link destinations,
formatting and whitespace. The full Markdown diff includes section reordering.
Changing a heading is treated as removing one section and adding another.
The default comparison is the latest snapshot against its predecessor. The page
embeds every version pair; it requires no service, API or external JavaScript
library. Without JavaScript the default comparison remains readable.

## Shared design

The logo, colours, fonts, spacing and layout follow
[tscnlab/Projects](https://github.com/tscnlab/Projects). The original stylesheet is
vendored in `assets/projects.css`; mission-specific additions live in
`assets/mission.css`. See `assets/PROVENANCE.md` for source identifiers and the logo
checksum. Links use relative paths to work under a GitHub project site URL.

## Publish on GitHub Pages

The workflow in `.github/workflows/pages.yml` renders and checks pull requests.
Pushes to the repository's **main** branch render, check and deploy the site.
The working branch does not deploy until its changes reach main.

One-time setup in the repository's **Settings → Pages → Build and deployment**:
select **GitHub Actions** as the source. Ensure Pages is enabled before running
the deployment. Then merge the reviewed changes into main, or manually run the
workflow on main. The expected project URL is
<https://tscnlab.github.io/MissionStatement/>; this is a configuration target,
not a statement that deployment has already happened.

See [Quarto's GitHub Pages guide](https://quarto.org/docs/publishing/github-pages.html)
and [GitHub's custom workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
Only `_site/` is uploaded. Rendered output and execution caches are ignored by Git.

## Future revisions

1. Edit `MissionStatement_Current.md`, including its version/date and retreat history.
2. Copy it to the new dated snapshot using the existing filename convention.
3. Render and check the site, review the comparison, and merge the revision into main.

The statement retains its existing license declaration. The branding and
institutional marks remain subject to their owners' rights.
