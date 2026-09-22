import argparse
from html import escape
import json
from pathlib import Path
import sys

from . import __version__
from .core import (InputError, apply_acceptances, compare, exit_code, read_json,
                   scan_site, validate_snapshot, write_new_snapshot)


def html_report(report):
    rows = []
    for finding in report['findings']:
        cells = [finding['code'], finding['url'], finding['before'] or '', finding['after'] or '', '\n'.join(finding['candidates'])]
        rows.append('<tr>' + ''.join('<td>' + escape(str(value)) + '</td>' for value in cells) + '</tr>')
    unknowns = ''.join('<li><code>' + escape(json.dumps(item, ensure_ascii=False)) + '</code></li>' for item in report['unknowns'])
    accepted = ''.join('<li>' + escape(item['url'] + ': ' + item['reason']) + '</li>' for item in report['accepted'])
    status = 'Incomplete analysis' if report['unknowns'] else 'Review required' if report['findings'] else 'No unreviewed changes'
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>AnchorHold report</title><style>
body{font:16px/1.55 system-ui,sans-serif;max-width:1200px;margin:40px auto;padding:0 24px;background:#f5f7fb;color:#14253e}
h1{font-size:38px;letter-spacing:-1px} .badge{display:inline-block;padding:6px 14px;border-radius:8px;background:#dfeafa;color:#163a6b}
table{border-collapse:collapse;width:100%;background:white;margin:24px 0}th,td{padding:14px;border-bottom:1px solid #d5deea;text-align:left;vertical-align:top;white-space:pre-wrap;overflow-wrap:anywhere}th{background:#e9eff7}
.table{overflow:auto}code{overflow-wrap:anywhere}footer{margin:30px 0;color:#506078}</style>
<main><p>ANCHORHOLD / DOCUMENTATION RELEASE CHECK</p><h1>Do old links still mean the same thing?</h1><p class="badge">''' + escape(status) + '</p><p>' + str(report['checked_pages']) + ' baseline pages · ' + str(report['checked_anchors']) + ' checked anchors</p><p>Heading text is evidence for review, not proof of semantic identity. Candidate targets are suggestions, not redirects.</p><div class="table"><table><thead><tr><th>Finding</th><th>Old URL</th><th>Before</th><th>Now</th><th>Same-text candidates</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div><h2>Incomplete checks</h2><ul>' + unknowns + '</ul><h2>Explicitly reviewed changes</h2><ul>' + accepted + '</ul></main><footer>Offline static HTML comparison. No network, JavaScript execution or deployment verification.</footer></html>'


def main(argv=None):
    parser = argparse.ArgumentParser(description='Find removed or silently retargeted documentation permalinks.')
    parser.add_argument('--version', action='version', version=__version__)
    commands = parser.add_subparsers(dest='command', required=True)
    snapshot = commands.add_parser('snapshot', help='Save an inventory from a known-good built site.')
    snapshot.add_argument('site', type=Path)
    snapshot.add_argument('--output', type=Path, required=True, help='New file; existing files are never overwritten.')
    snapshot.add_argument('--all-anchors', action='store_true', help='Protect all static targets, including targets without a heading.')
    check = commands.add_parser('check', help='Compare a baseline against a new built site.')
    check.add_argument('baseline', type=Path)
    check.add_argument('site', type=Path)
    check.add_argument('--format', choices=('text', 'json', 'html'), default='text')
    check.add_argument('--accept', type=Path, help='Exact reviewed changes with reasons; stale entries fail as incomplete.')
    args = parser.parse_args(argv)
    try:
        if args.command == 'snapshot':
            data = scan_site(args.site, 'all' if args.all_anchors else 'headings')
            validate_snapshot(data)
            write_new_snapshot(args.output, data)
            print(f"Saved {len(data['pages'])} pages. Scope: {data['scope']}.")
            return 0
        baseline = validate_snapshot(read_json(args.baseline))
        report = compare(baseline, scan_site(args.site, baseline['scope']))
        if args.accept:
            report = apply_acceptances(report, read_json(args.accept))
        if args.format == 'json':
            print(json.dumps(report, indent=2, ensure_ascii=True))
        elif args.format == 'html':
            print(html_report(report).encode('ascii', 'xmlcharrefreplace').decode('ascii'))
        else:
            print(f"anchorhold: {len(report['findings'])} changes to review, {len(report['accepted'])} accepted, {len(report['unknowns'])} incomplete checks")
            for item in report['findings']:
                print(json.dumps(item, ensure_ascii=True))
            for item in report['unknowns']:
                print('UNKNOWN ' + json.dumps(item, ensure_ascii=True))
        return exit_code(report)
    except (OSError, ValueError, RecursionError) as exc:
        message = str(exc) if isinstance(exc, InputError) else type(exc).__name__ + ': cannot read/analyze/write input.'
        print(json.dumps({'tool': 'anchorhold', 'error': message}, ensure_ascii=True), file=sys.stderr)
        return 2
