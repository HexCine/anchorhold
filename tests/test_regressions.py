import unittest
from anchorhold.core import apply_acceptances, compare, parse_page


class RegressionTests(unittest.TestCase):
    def test_comments_do_not_change_visible_heading_text(self):
        page, _ = parse_page('<h2 id="api">API<!-- internal note --> reference</h2>')
        self.assertEqual(page['anchors']['api']['label'], 'API reference')

    def test_line_break_separates_words(self):
        page, _ = parse_page('<h2 id="api">API<br>reference</h2>')
        self.assertEqual(page['anchors']['api']['label'], 'API reference')

    def test_acceptance_does_not_pollute_source_snapshot(self):
        page, _ = parse_page('<h2 id="api">API</h2>')
        page['sha256'] = '0' * 64
        snapshot = {'schema_version': 1, 'tool': 'anchorhold', 'scope': 'headings',
                    'pages': {'index.html': page}, 'unknowns': []}
        report = compare(snapshot, snapshot)
        apply_acceptances(report, {'schema_version': 1, 'accept': [{'fingerprint': '0' * 64, 'reason': 'Old review'}]})
        self.assertEqual(snapshot['unknowns'], [])
        self.assertTrue(compare(snapshot, snapshot)['complete'])
