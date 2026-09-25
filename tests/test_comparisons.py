"""Check that the review cannot lose prose or misrepresent section moves."""
from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest

from scripts.mission_site import (ROOT, Version, compare, load_versions, load_change_notes,
                                 markdown_html, prose_diff, revision_history, split_sections)


class VisibleText(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.feed(html)

    def handle_data(self, data):
        self.text.append(data)


def text(html):
    return ''.join(VisibleText(html).text)


class Comparisons(unittest.TestCase):
    def test_current_matches_latest_snapshot_and_metadata(self):
        versions = load_versions()
        milan_version = next(version for version in versions if version.id == 'v1.5')
        self.assertEqual(milan_version.order, [
            'Inclusive, diverse and collaborative lab culture',
            'Commitment to meaningful and societally relevant science',
            'Wellbeing and work-life balance',
            'Open scholarship and open science',
            'Reproducibility and scientific integrity',
            'Sustainability',
        ])

    def test_marking_preserves_both_complete_texts_and_links(self):
        before = 'A **careful** test with [a link](https://example.org/) and CO<sub>2</sub>.\n\nAnother paragraph.'
        after = 'A **documented** test with [a new link](https://example.org/new) and CO<sub>2</sub>.\n\nAnother paragraph.'
        old_html, new_html = prose_diff(before, after)
        self.assertEqual(text(old_html), text(markdown_html(before)))
        self.assertEqual(text(new_html), text(markdown_html(after)))
        self.assertIn('<del>careful</del>', old_html)
        self.assertIn('<ins>documented</ins>', new_html)
        self.assertIn('href="https://example.org/new"', new_html)
        self.assertIn('<sub>2</sub>', new_html)

    def test_moves_are_not_wording_changes(self):
        before = Version('v1', 'old', 'old.md', '', {'A': 'One.', 'B': 'Two.'})
        after = Version('v2', 'new', 'new.md', '', {'B': 'Two.', 'A': 'One.'})
        result = compare(before, after)
        self.assertEqual(result['changed'], 0)
        self.assertEqual(result['moved'], 2)
        self.assertNotIn('<ins>', result['html'])
        self.assertIn('Priority position 2 → 1', result['html'])

    def test_link_only_change_is_available_in_exact_diff(self):
        before = Version('v1', 'old', 'old.md', '', {'A': '[Resource](https://example.org/old)'})
        after = Version('v2', 'new', 'new.md', '', {'A': '[Resource](https://example.org/new)'})
        result = compare(before, after)
        self.assertEqual(result['changed'], 1)
        self.assertIn('https://example.org/old', result['html'])
        self.assertIn('https://example.org/new', result['html'])
        self.assertIn('Exact Markdown changes', result['html'])

    def test_added_removed_and_identical_sections(self):
        before = Version('v1', 'old', 'old.md', '', {'A': 'Removed text.'})
        after = Version('v2', 'new', 'new.md', '', {'B': 'Added text.'})
        result = compare(before, after)
        self.assertIn('Section added', result['html'])
        self.assertIn('Section removed', result['html'])
        self.assertEqual(compare(before, before)['changed'], 0)

    def test_all_real_section_diffs_preserve_the_sources(self):
        versions = load_versions()
        for before, after in zip(versions, versions[1:]):
            for name in set(before.sections) | set(after.sections):
                a, b = before.sections.get(name, ''), after.sections.get(name, '')
                left, right = prose_diff(a, b)
                self.assertEqual(text(left), text(markdown_html(a)))
                self.assertEqual(text(right), text(markdown_html(b)))

    def test_duplicate_headings_are_rejected(self):
        with self.assertRaises(ValueError):
            split_sections('# Mission Statement\n\n### A\nOne\n\n### A\nTwo')

    def test_historical_notes_use_original_dates(self):
        versions = load_versions()
        notes, added = load_change_notes(versions)
        self.assertEqual(str(added), '2026-09-25')
        self.assertEqual(str(notes['v1.0'].dated), '2022-10-16')
        self.assertEqual(str(notes['v1.2'].dated), '2023-02-24')
        self.assertEqual(str(notes['v1.5'].dated), '2026-09-10')
        history = revision_history(versions, notes, added)
        for note in notes.values():
            self.assertIn(note.time_html, history)
            self.assertIn(f'id="revision-{note.id.replace(".", "-")}"', history)

    def test_range_notes_include_intervening_changes_with_correct_dates(self):
        versions = load_versions()
        notes, _ = load_change_notes(versions)
        by_id = {version.id: version for version in versions}
        result = compare(by_id['v1.1'], by_id['v1.5'], notes)['html']
        self.assertIn('<time datetime="2023-02-24">', result)
        self.assertIn('<time datetime="2023-07-27">', result)
        self.assertIn('<time datetime="2024-09-02">', result)
        self.assertIn('<time datetime="2026-09-10">', result)
        self.assertNotIn('<time datetime="2023-01-16">', result)
        latest = compare(by_id['v1.4'], by_id['v1.5'], notes)['html']
        self.assertIn('CODECHECK', latest)
        self.assertIn('<time datetime="2026-09-10">', latest)
        self.assertNotIn('<time datetime="2024-09-02">', latest)

    def test_reverse_notes_explain_direction_and_identical_versions_have_no_changes(self):
        versions = load_versions()
        notes, _ = load_change_notes(versions)
        reverse = compare(versions[-1], versions[-2], notes)['html']
        self.assertIn('text comparison runs backwards in time', reverse)
        same = compare(versions[-1], versions[-1], notes)['html']
        self.assertNotIn('class="change-notes"', same)

    def test_inconsistent_dates_and_missing_section_notes_are_rejected(self):
        versions = load_versions()
        original = (ROOT / 'CHANGELOG.md').read_text()
        invalid = [original.replace('v1.5 | 10 September 2026', 'v1.5 | 11 September 2026'),
                   original.replace('### Open scholarship and open science', '### Unrelated heading')]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for content in invalid:
                (root / 'CHANGELOG.md').write_text(content)
                with self.assertRaises(ValueError):
                    load_change_notes(versions, root)


if __name__ == '__main__':
    unittest.main()
