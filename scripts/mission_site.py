"""Reproducible, section-aware comparisons for the two Quarto notebooks.

No network requests or third-party Python packages are used here. Pandoc is
provided by Quarto. All version pairs are embedded in the rendered page.
"""

from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher, unified_diff
from functools import lru_cache
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import json
import os
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
FILE_PATTERN = re.compile(r"MissionStatement_(\d{4})\.(\d{2})\.(\d{2})_v(\d+(?:\.\d+)*)\.md")
METADATA = {"Introduction", "Version history", "License"}


@dataclass
class Version:
    id: str
    date: str
    filename: str
    source: str
    sections: dict[str, str]

    @property
    def label(self):
        return f"{self.id} · {self.date}"

    @property
    def order(self):
        return [name for name in self.sections if name not in METADATA]


def split_sections(source):
    """Keep metadata and introduction; match principles by exact heading."""
    parts = re.split(r"^### (.+)\s*$", source, flags=re.MULTILINE)
    intro = re.sub(r"^# Mission Statement\s*", "", parts[0]).strip()
    sections = {"Introduction": intro}
    for title, body in zip(parts[1::2], parts[2::2]):
        if title in sections:
            raise ValueError(f"Duplicate section heading: {title}")
        sections[title] = body.strip()
    return sections


def load_versions(root=ROOT):
    versions = []
    for path in sorted(root.glob("MissionStatement_*_v*.md")):
        match = FILE_PATTERN.fullmatch(path.name)
        if not match:
            raise ValueError(f"Unexpected snapshot filename: {path.name}")
        year, month, day = map(int, match.groups()[:3])
        dated = date(year, month, day)
        label = f"{dated.day} {dated.strftime('%B')} {dated.year}"
        version_id = f"v{match[4]}"
        source = path.read_text(encoding="utf-8")
        if f"Current version/date: {version_id} | {label}" not in source:
            raise ValueError(f"Filename and version/date disagree in {path.name}")
        versions.append(Version(version_id, label, path.name, source, split_sections(source)))
    if len(versions) < 2:
        raise ValueError("At least two dated snapshots are needed for comparison")
    if len({v.id for v in versions}) != len(versions):
        raise ValueError("Duplicate version identifiers")
    if (root / "MissionStatement_Current.md").read_bytes() != (root / versions[-1].filename).read_bytes():
        raise ValueError("MissionStatement_Current.md must match the latest dated snapshot exactly")
    return versions


def current_markdown(versions):
    latest = versions[-1]
    source = re.sub(r"^# Mission Statement", "# Mission statement", latest.source)
    source = re.sub(r"^### ", "## ", source, flags=re.MULTILINE)
    links = ('<div class="mission-links"><a href="compare.html">Compare versions</a>'
             '<a href="MissionStatement_Current.md" download>Download Markdown</a></div>')
    return source.replace("# Mission statement\n", f"# Mission statement\n\n{links}\n", 1)


@lru_cache(maxsize=None)
def markdown_html(source):
    quarto = os.environ.get("QUARTO_BIN_PATH", "quarto")
    if Path(quarto).is_dir():
        quarto = str(Path(quarto) / "quarto")
    return subprocess.run(
        [quarto, "pandoc", "--from=markdown-smart", "--to=html5", "--wrap=none"],
        input=source, text=True, capture_output=True, check=True,
    ).stdout.strip()


class ProseTokens(HTMLParser):
    """Keep HTML tags intact while tokenising only the visible prose."""

    def __init__(self, rendered):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.words = []
        self.feed(rendered)
        self.close()

    def handle_starttag(self, tag, attrs):
        self.parts.append(("tag", self.get_starttag_text(), None))

    def handle_startendtag(self, tag, attrs):
        self.parts.append(("tag", self.get_starttag_text(), None))

    def handle_endtag(self, tag):
        self.parts.append(("tag", f"</{tag}>", None))

    def handle_data(self, data):
        for token in re.findall(r"\s+|\w+(?:[’'-]\w+)*|[^\w\s]", data):
            if token.isspace():
                self.parts.append(("space", escape(token), None))
            else:
                self.parts.append(("word", escape(token), len(self.words)))
                self.words.append(token)

    def marked(self, changes, mark):
        output, buffer, active = [], [], False

        def flush():
            if buffer:
                content = "".join(buffer)
                output.append(f"<{mark}>{content}</{mark}>" if active else content)
                buffer.clear()

        previous_word = -1
        for kind, value, index in self.parts:
            if kind == "tag":
                flush()
                output.append(value)
                continue
            if kind == "word":
                changed = index in changes
                previous_word = index
            else:
                # Highlight spaces only inside a changed run, not its edges.
                changed = previous_word in changes and previous_word + 1 in changes
            if changed != active:
                flush()
                active = changed
            buffer.append(value)
        flush()
        return "".join(output)


def prose_diff(before, after):
    left, right = ProseTokens(markdown_html(before)), ProseTokens(markdown_html(after))
    deleted, inserted = set(), set()
    for op, a, b, c, d in SequenceMatcher(None, left.words, right.words, autojunk=False).get_opcodes():
        if op != "equal":
            deleted.update(range(a, b))
            inserted.update(range(c, d))
    return left.marked(deleted, "del"), right.marked(inserted, "ins")


def source_diff(before, after, old_name, new_name):
    return "".join(unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                fromfile=old_name, tofile=new_name))


def compare(before, after):
    names = list(after.sections) + [s for s in before.sections if s not in after.sections]
    cards, changed_count, moved_count = [], 0, 0
    for name in names:
        old, new = before.sections.get(name, ""), after.sections.get(name, "")
        changed = old != new
        old_position = before.order.index(name) + 1 if name in before.order else None
        new_position = after.order.index(name) + 1 if name in after.order else None
        moved = old_position is not None and new_position is not None and old_position != new_position
        changed_count += changed
        moved_count += moved
        status = ["Wording changed" if changed else "Wording unchanged"]
        if name not in before.sections:
            status = ["Section added"]
        elif name not in after.sections:
            status = ["Section removed"]
        if moved:
            status.append(f"Priority position {old_position} → {new_position}")
        left, right = prose_diff(old, new)
        section_diff = source_diff(old + "\n", new + "\n", before.id, after.id)
        exact = ('<details class="source-diff"><summary>Exact Markdown changes (including links and formatting)</summary>'
                 f'<pre>{escape(section_diff)}</pre></details>') if changed else ""
        cards.append(
            f'<section class="diff-section" data-unchanged="{str(not changed and not moved).lower()}">'
            f'<h2>{escape(name)}</h2><p class="diff-status">{escape(" · ".join(status))}</p>'
            '<div class="diff-columns">'
            f'<div class="diff-column"><h3>From: {escape(before.label)}</h3><div class="diff-body">{left or "<p>Section not present.</p>"}</div></div>'
            f'<div class="diff-column"><h3>To: {escape(after.label)}</h3><div class="diff-body">{right or "<p>Section not present.</p>"}</div></div>'
            f'</div>{exact}</section>'
        )
    summary = ("The same version is selected on both sides." if before.id == after.id else
               f"{changed_count} document sections changed; {moved_count} principles changed position.")
    order_note = ""
    if before.order != after.order:
        order_note = ('<p class="order-note">Principle order in the selected “To” version: '
                      + escape(" → ".join(after.order)) + '.</p>')
    full_diff = source_diff(before.source, after.source, before.filename, after.filename)
    exact_full = ('<details class="source-diff"><summary>Complete Markdown diff, including section order</summary>'
                  f'<pre>{escape(full_diff or "No changes.")}</pre></details>')
    html = (f'<div class="comparison-summary"><p>{escape(summary)}</p>{order_note}</div>'
            + ''.join(cards) + exact_full)
    return {"html": html, "summary": summary, "changed": changed_count, "moved": moved_count}


def comparison_page(versions):
    before, after = versions[-2:]
    comparisons = {f"{a.id}:{b.id}": compare(a, b) for a in versions for b in versions}
    data = {"versions": [{"id": v.id, "label": v.label} for v in versions],
            "defaultFrom": before.id, "defaultTo": after.id, "comparisons": comparisons}
    # Escape '<' so document prose can never close this inert JSON script tag.
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")

    def options(selected):
        return ''.join(f'<option value="{v.id}"{" selected" if v.id == selected else ""}>{escape(v.label)}</option>'
                       for v in reversed(versions))

    history = ''.join(f'<li><a href="{v.filename}">{escape(v.label)} — Markdown source</a></li>'
                      for v in reversed(versions))
    return ('```{=html}\n'
            '<div class="compare-controls">'
            f'<div><label for="version-from">From</label><select id="version-from">{options(before.id)}</select></div>'
            f'<div><label for="version-to">To</label><select id="version-to">{options(after.id)}</select></div></div>'
            '<div class="compare-tools"><label><input type="checkbox" id="show-unchanged" checked> Show unchanged sections</label>'
            '<a id="comparison-link" href="compare.html">Link to this comparison</a></div>'
            '<div class="compare-legend"><span><del>Removed wording</del></span><span><ins>Added wording</ins></span>'
            '<span>Position changes are labelled separately.</span></div>'
            '<noscript><p>JavaScript is disabled. The latest comparison is shown below; version selectors require JavaScript.</p></noscript>'
            f'<p id="comparison-announcement" class="visually-hidden" role="status" aria-live="polite"></p>'
            f'<div id="comparison-results">{comparisons[f"{before.id}:{after.id}"]["html"]}</div>'
            '<section class="version-history"><h2>Version archive</h2><p>Available dated snapshots, preserved as Markdown.</p>'
            f'<ul>{history}</ul></section><script type="application/json" id="comparison-data">{encoded}</script>'
            '\n```')
