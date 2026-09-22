import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from anchorhold.cli import main, html_report
from anchorhold.core import (InputError, apply_acceptances, compare, exit_code,
    parse_page, read_json, scan_site, url, validate_snapshot, write_new_snapshot)


class ParsingTests(unittest.TestCase):
    def anchors(self, html):
        return parse_page(html)[0]['anchors']

    def test_direct_heading_and_inline_markup(self):
        self.assertEqual(self.anchors('<h2 id="api">Use <code>foo</code> now</h2>')['api']['label'], 'Use foo now')

    def test_sphinx_section_parent(self):
        self.assertEqual(self.anchors('<section id="id1"><h2>1.2.0<a class="headerlink">¶</a></h2></section>')['id1']['label'], '1.2.0')

    def test_nested_sections_use_their_first_heading(self):
        anchors = self.anchors('<section id="top"><h1>Main</h1><section id="child"><h2>Child</h2></section></section>')
        self.assertEqual([anchors[x]['label'] for x in ('top', 'child')], ['Main', 'Child'])

    def test_multiple_sibling_headings(self):
        self.assertEqual(self.anchors('<div id="wrap"><h2>First</h2><h2>Second</h2></div>')['wrap']['label'], 'First')

    def test_permalinks_hidden_labels_entities(self):
        actual = self.anchors('<h2 id="x"> A &amp; B <a class="anchor-link">#</a><span aria-hidden="true">Copy</span><span hidden>hidden</span></h2>')
        self.assertEqual(actual['x']['label'], 'A & B')

    def test_heading_child_alias(self):
        self.assertEqual(self.anchors('<h2 id="new"><span id="old"></span>Hello</h2>')['old']['label'], 'Hello')

    def test_legacy_named_anchor(self):
        self.assertIsNone(self.anchors('<a name="legacy"></a>')['legacy']['label'])

    def test_duplicate_target_unknown(self):
        _, issues = parse_page('<h2 id="same">One</h2><a name="same">Two</a>')
        self.assertEqual(issues[0]['code'], 'duplicate_anchor')

    def test_same_element_id_name_is_one_target(self):
        self.assertEqual(parse_page('<a id="x" name="x">x</a>')[1], [])

    def test_inert_content_not_targets(self):
        anchors = self.anchors('<template><h2 id="fake">Fake</h2></template><script>"<h2 id=evil>x</h2>"</script><h2 id="real">Real</h2>')
        self.assertEqual(list(anchors), ['real'])

    def test_refresh_is_unknown(self):
        _, issues = parse_page('<meta http-equiv="Refresh" content="0;url=other.html">')
        self.assertEqual(issues[0]['code'], 'meta_refresh')

    def test_html5_optional_closing_tags(self):
        anchors = self.anchors('<h2 id="one">One<h2 id="two">Two')
        self.assertEqual([anchors[x]['label'] for x in ('one', 'two')], ['One', 'Two'])

    def test_unicode_anchor_url(self):
        self.assertEqual(url('dir/a b.html', '你好#%'), '/dir/a%20b.html#%E4%BD%A0%E5%A5%BD%23%25')

    def test_no_text_normalization_beyond_whitespace(self):
        self.assertEqual(self.anchors('<h2 id="x">  API\n Case  </h2>')['x']['label'], 'API Case')


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.before = self.root / 'before'
        self.after = self.root / 'after'
        self.before.mkdir()
        self.after.mkdir()

    def page(self, directory, text, name='index.html'):
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def report(self, old, new, scope='headings'):
        self.page(self.before, old)
        self.page(self.after, new)
        return compare(scan_site(self.before, scope), scan_site(self.after, scope))

    def test_stable_site(self):
        report = self.report('<h2 id="v1">1.0</h2>', '<h2 id="v2">2.0</h2><h2 id="v1">1.0</h2>')
        self.assertEqual(exit_code(report), 0)

    def test_numeric_changelog_silent_retarget(self):
        report = self.report('<h2 id="id1">1.2.0</h2><h2 id="id2">1.1.0</h2>', '<h2 id="id1">1.3.0</h2><h2 id="id2">1.2.0</h2><h2 id="id3">1.1.0</h2>')
        self.assertEqual([f['code'] for f in report['findings']], ['heading_retargeted'] * 2)
        self.assertEqual(report['findings'][0]['candidates'], ['/index.html#id2'])
        self.assertEqual(exit_code(report), 1)

    def test_cosmetic_edit_is_review_not_proven_retarget(self):
        report = self.report('<h2 id="a">Install</h2>', '<h2 id="a">Installation</h2>')
        self.assertEqual(report['findings'][0]['code'], 'heading_changed')

    def test_anchor_removed(self):
        report = self.report('<h2 id="a">Install</h2>', '<h2 id="b">Install</h2>')
        self.assertEqual(report['findings'][0]['code'], 'anchor_removed')
        self.assertEqual(report['findings'][0]['candidates'], ['/index.html#b'])

    def test_page_removed(self):
        self.page(self.before, '<h2 id="a">Install</h2>', 'old.html')
        self.page(self.after, '<h2 id="a">Install</h2>', 'new.html')
        report = compare(scan_site(self.before), scan_site(self.after))
        self.assertEqual(report['findings'][0]['code'], 'page_removed')

    def test_heading_association_lost(self):
        report = self.report('<h2 id="a">Install</h2>', '<p id="a">Install</p>')
        self.assertEqual(report['findings'][0]['code'], 'heading_unresolved')

    def test_default_ignores_nonheading_target_removal(self):
        report = self.report('<h2 id="a">Title</h2><p id="css">Text</p>', '<h2 id="a">Title</h2>')
        self.assertEqual(exit_code(report), 0)

    def test_all_scope_checks_nonheading_target(self):
        report = self.report('<p id="css">Text</p>', '<p>Text</p>', 'all')
        self.assertEqual(report['findings'][0]['code'], 'anchor_removed')

    def test_unknown_precedes_known_failure(self):
        report = self.report('<h2 id="a">A</h2>', '<h2 id="b">B</h2><h2 id="b">Other</h2>')
        self.assertEqual(exit_code(report), 2)
        self.assertTrue(report['findings'])

    def test_never_follow_meta_redirect(self):
        report = self.report('<h2 id="a">A</h2>', '<meta http-equiv="refresh" content="0;url=https://example.invalid"><h2 id="a">A</h2>')
        self.assertEqual(exit_code(report), 2)

    def test_baseline_with_duplicates_is_rejected(self):
        self.page(self.before, '<h2 id="a">A</h2><h2 id="a">A</h2>')
        with self.assertRaises(InputError):
            validate_snapshot(scan_site(self.before))

    def test_no_anchored_headings_rejected_by_default(self):
        self.page(self.before, '<h2>Title</h2>')
        with self.assertRaises(InputError):
            validate_snapshot(scan_site(self.before))

    def test_missing_site_and_empty_site(self):
        with self.assertRaises(FileNotFoundError):
            scan_site(self.root / 'missing')
        with self.assertRaises(InputError):
            scan_site(self.before)

    def test_non_utf8_rejected(self):
        (self.before / 'x.html').write_bytes(b'\xff\xff')
        with self.assertRaises(InputError):
            scan_site(self.before)

    def test_size_bound(self):
        self.page(self.before, 'abcdef')
        with patch('anchorhold.core.MAX_FILE', 5), self.assertRaises(InputError):
            scan_site(self.before)

    def test_link_boundary(self):
        self.page(self.before, '<h2 id="a">A</h2>')
        with patch('anchorhold.core.is_link', return_value=True), self.assertRaises(InputError):
            scan_site(self.before)

    def test_accept_exact_change_and_keep_evidence(self):
        report = self.report('<h2 id="a">Title</h2>', '<h2 id="a">New title</h2>')
        fingerprint = report['findings'][0]['fingerprint']
        accepted = apply_acceptances(report, {'schema_version': 1, 'accept': [{'fingerprint': fingerprint, 'reason': 'Reviewed wording change.'}]})
        self.assertEqual(exit_code(accepted), 0)
        self.assertEqual(accepted['accepted'][0]['before'], 'Title')

    def test_stale_acceptance_never_hides_new_change(self):
        report = self.report('<h2 id="a">Title</h2>', '<h2 id="a">New title</h2>')
        result = apply_acceptances(report, {'schema_version': 1, 'accept': [{'fingerprint': 'a' * 64, 'reason': 'Earlier change'}]})
        self.assertEqual(exit_code(result), 2)
        self.assertEqual(len(result['findings']), 1)

    def test_acceptance_requires_reason_and_no_duplicates(self):
        for entries in ([{'fingerprint': 'a' * 64, 'reason': ''}], [{'fingerprint': 'a' * 64, 'reason': 'OK'}] * 2):
            report = self.report('<h2 id="a">Title</h2>', '<h2 id="a">New title</h2>')
            with self.assertRaises(InputError):
                apply_acceptances(report, {'schema_version': 1, 'accept': entries})

    def test_snapshot_never_overwrites_file(self):
        self.page(self.before, '<h2 id="a">Title</h2>')
        dest = self.root / 'baseline.json'
        snapshot = scan_site(self.before)
        write_new_snapshot(dest, snapshot)
        original = dest.read_bytes()
        with self.assertRaises(FileExistsError):
            write_new_snapshot(dest, snapshot)
        self.assertEqual(dest.read_bytes(), original)

    def test_invalid_baseline_shape_and_traversal(self):
        self.page(self.before, '<h2 id="a">Title</h2>')
        good = scan_site(self.before)
        bad = copy.deepcopy(good)
        bad['pages']['../outside.html'] = bad['pages'].pop('index.html')
        for data in ({}, [], bad):
            with self.assertRaises(InputError):
                validate_snapshot(data)

    def test_json_duplicate_keys_rejected(self):
        path = self.root / 'bad.json'
        path.write_text('{"a": 1, "a": 2}')
        with self.assertRaises(InputError):
            read_json(path)

    def test_boolean_schema_version_rejected(self):
        self.page(self.before, '<h2 id="a">Title</h2>')
        snapshot = scan_site(self.before)
        snapshot['schema_version'] = True
        with self.assertRaises(InputError):
            validate_snapshot(snapshot)

    def test_oversize_snapshot_does_not_leave_file(self):
        self.page(self.before, '<h2 id="a">Title</h2>')
        snapshot = scan_site(self.before)
        target = self.root / 'new.json'
        with patch('anchorhold.core.MAX_JSON', 10), self.assertRaises(InputError):
            write_new_snapshot(target, snapshot)
        self.assertFalse(target.exists())

    def test_html_report_escapes_untrusted_labels(self):
        report = self.report('<h2 id="a">&lt;script&gt;alert(1)&lt;/script&gt;</h2>', '<h2 id="a">New title</h2>')
        rendered = html_report(report)
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;', rendered)

    def test_cli_snapshot_json_and_exit_codes(self):
        self.page(self.before, '<h2 id="a">Title</h2>')
        self.page(self.after, '<h2 id="a">Changed</h2>')
        baseline = self.root / 'baseline.json'
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(['snapshot', str(self.before), '--output', str(baseline)]), 0)
        for site, code in ((self.before, 0), (self.after, 1)):
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(['check', str(baseline), str(site), '--format', 'json']), code)
                self.assertEqual(json.loads(output.getvalue())['schema_version'], 1)
        with redirect_stderr(io.StringIO()) as error:
            self.assertEqual(main(['check', 'missing.json', str(self.after)]), 2)
            self.assertIn('error', json.loads(error.getvalue()))


if __name__ == '__main__':
    unittest.main()
