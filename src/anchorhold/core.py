"""Static permalink identity checks. Never fetch or execute a site."""
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from urllib.parse import quote

import html5lib

MAX_FILE = 2 * 1024 * 1024
MAX_JSON = 32 * 1024 * 1024
HEADINGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
SKIP = {'script', 'style', 'template', 'noscript'}


class InputError(ValueError):
    pass


def tag(node):
    return node.tag.rsplit('}', 1)[-1] if isinstance(node.tag, str) else ''


def label(node):
    """Normalized visible heading text, excluding common permalink decorations."""
    pieces = []
    stack = [('node', node)]
    while stack:
        kind, value = stack.pop()
        if kind == 'text':
            pieces.append(value or '')
            continue
        classes = set(value.get('class', '').split())
        if (not isinstance(value.tag, str) or tag(value) in SKIP or value.get('aria-hidden') == 'true'
                or 'hidden' in value.attrib or classes & {'headerlink', 'anchor-link'}):
            continue
        if tag(value) == 'br':
            pieces.append(' ')
        children = list(value)
        for child in reversed(children):
            stack.append(('text', child.tail))
            stack.append(('node', child))
        stack.append(('text', value.text))
    return ' '.join(''.join(pieces).split())


def parse_page(text):
    """Return all static targets and a heading association where structurally clear."""
    document = html5lib.parse(text, namespaceHTMLElements=False, scripting=True)
    nodes, parents, issues = [], {}, []
    stack = [(document, None, 0)]
    while stack:
        node, parent, depth = stack.pop()
        if depth > 150 or len(nodes) >= 200000:
            raise InputError('HTML node/depth limit exceeded.')
        if tag(node) in SKIP:
            continue
        nodes.append(node)
        parents[node] = parent
        for child in reversed(list(node)):
            stack.append((child, node, depth + 1))
    # First heading for section-like containers, matching generated Sphinx HTML.
    first_heading = {}
    for node in reversed(nodes):
        heading = node if tag(node) in HEADINGS else first_heading.get(node)
        if heading is not None and parents[node] is not None:
            first_heading[parents[node]] = heading
    headings = {node: label(node) for node in nodes if tag(node) in HEADINGS}
    anchors, owners = {}, {}
    for node in nodes:
        if tag(node) == 'meta' and node.get('http-equiv', '').lower() == 'refresh':
            issues.append({'code': 'meta_refresh', 'message': 'Client redirect requires browser/deployment verification.'})
        names = []
        if node.get('id'):
            names.append(node.get('id'))
        if tag(node) == 'a' and node.get('name') and node.get('name') not in names:
            names.append(node.get('name'))
        heading = node if node in headings else None
        parent = parents[node]
        while heading is None and parent is not None:
            if parent in headings:
                heading = parent
                break
            parent = parents[parent]
        if heading is None and tag(node) in {'section', 'div'}:
            heading = first_heading.get(node)
        for name in names:
            if len(name) > 4096 or any(ord(c) < 32 for c in name):
                raise InputError('Anchor is too long or contains control characters.')
            value = {'label': headings.get(heading) if heading is not None else None}
            if name in owners and owners[name] is not node:
                issues.append({'code': 'duplicate_anchor', 'anchor': name, 'message': 'Multiple static elements expose this target.'})
                continue
            owners[name] = node
            anchors[name] = value
    return {'anchors': dict(sorted(anchors.items())), 'heading_count': len(headings)}, issues


def is_link(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def scan_site(root, scope='headings'):
    if scope not in ('headings', 'all'):
        raise InputError('Unsupported anchor scope.')
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise InputError('Site must be a directory containing generated HTML.')
    pages, unknowns = {}, []
    total = entries = 0
    pending = [root]
    while pending:
        directory = pending.pop()
        for path in sorted(directory.iterdir()):
            entries += 1
            if entries > 100000:
                raise InputError('Site exceeds 100000 filesystem entries.')
            if is_link(path):
                raise InputError('Symlinks/junctions are unsupported in site trees.')
            if path.is_dir():
                pending.append(path)
                continue
            if path.suffix.lower() not in ('.html', '.htm'):
                continue
            if not path.is_file() or not path.resolve().is_relative_to(root):
                raise InputError('HTML must be a regular file inside the site root.')
            if len(pages) >= 10000:
                raise InputError('Site exceeds 10000 HTML files.')
            with path.open('rb') as stream:
                raw = stream.read(MAX_FILE + 1)
            total += len(raw)
            if len(raw) > MAX_FILE or total > 100 * 1024 * 1024:
                raise InputError('HTML exceeds 2 MiB/file or 100 MiB/site.')
            relative = path.relative_to(root).as_posix()
            try:
                page, issues = parse_page(raw.decode('utf-8-sig'))
            except UnicodeDecodeError as exc:
                raise InputError('Only UTF-8 HTML is supported: ' + relative) from exc
            page['sha256'] = hashlib.sha256(raw).hexdigest()
            pages[relative] = page
            unknowns.extend(dict(issue, page=relative) for issue in issues)
    if not pages:
        raise InputError('No HTML files found in site root.')
    return {'schema_version': 1, 'tool': 'anchorhold', 'scope': scope,
            'pages': dict(sorted(pages.items())), 'unknowns': unknowns}


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError('Duplicate JSON key.')
        result[key] = value
    return result


def read_json(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_JSON + 1)
    if len(raw) > MAX_JSON:
        raise InputError('JSON exceeds 32 MiB.')
    try:
        return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=_unique,
                          parse_constant=lambda value: (_ for _ in ()).throw(InputError('Non-finite JSON number.')))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise InputError('Invalid JSON input.') from exc


def validate_snapshot(data):
    if (not isinstance(data, dict) or type(data.get('schema_version')) is not int or data.get('schema_version') != 1
            or data.get('tool') != 'anchorhold' or data.get('scope') not in ('headings', 'all')
            or data.get('unknowns') != [] or not isinstance(data.get('pages'), dict)
            or not 1 <= len(data['pages']) <= 10000):
        raise InputError('Invalid, unsupported or incomplete baseline snapshot.')
    count = 0
    for path, page in data['pages'].items():
        if (not isinstance(path, str) or not path or path.startswith('/') or '\\' in path
                or any(part in ('', '.', '..') for part in path.split('/'))
                or not isinstance(page, dict) or not isinstance(page.get('anchors'), dict)
                or type(page.get('heading_count')) is not int or page['heading_count'] < 0
                or not re.fullmatch('[0-9a-f]{64}', str(page.get('sha256', '')))):
            raise InputError('Invalid baseline page.')
        for name, entry in page['anchors'].items():
            count += 1
            if (count > 500000 or not isinstance(name, str) or not name or len(name) > 4096
                    or any(ord(c) < 32 for c in name) or not isinstance(entry, dict)
                    or 'label' not in entry or entry['label'] is not None and not isinstance(entry['label'], str)):
                raise InputError('Invalid baseline anchor.')
    if data['scope'] == 'headings' and not any(entry['label'] for page in data['pages'].values() for entry in page['anchors'].values()):
        raise InputError('No anchored headings found; use --all-anchors for page/target existence checks.')
    return data


def url(path, anchor=None):
    return '/' + quote(path, safe='/') + (('#' + quote(anchor, safe='')) if anchor is not None else '')


def compare(before, after):
    validate_snapshot(before)
    findings = []
    candidates = defaultdict(list)
    for page, value in after['pages'].items():
        for anchor, entry in value['anchors'].items():
            if entry['label']:
                candidates[entry['label']].append(url(page, anchor))

    def add(code, page, anchor=None, old=None, new=None, suggestions=()):
        finding = {'code': code, 'url': url(page, anchor), 'before': old, 'after': new,
                   'candidates': sorted(suggestions)[:20]}
        # Exact observed change, independent of unrelated candidate additions.
        evidence = {key: finding[key] for key in ('code', 'url', 'before', 'after')}
        finding['fingerprint'] = hashlib.sha256(json.dumps(evidence, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
        findings.append(finding)

    checked = 0
    for page, previous in before['pages'].items():
        if page not in after['pages']:
            add('page_removed', page)
            continue
        current = after['pages'][page]['anchors']
        for anchor, entry in previous['anchors'].items():
            old = entry['label']
            if before['scope'] == 'headings' and not old:
                continue
            checked += 1
            if anchor not in current:
                add('anchor_removed', page, anchor, old, suggestions=candidates.get(old, []))
                continue
            new = current[anchor]['label']
            if old is not None and old != new:
                other_targets = [target for target in candidates.get(old, []) if target != url(page, anchor)]
                code = 'heading_retargeted' if other_targets and new else 'heading_changed' if new else 'heading_unresolved'
                add(code, page, anchor, old, new, other_targets)
    return {'schema_version': 1, 'tool': 'anchorhold', 'scope': before['scope'],
            'checked_pages': len(before['pages']), 'checked_anchors': checked,
            'findings': findings, 'accepted': [], 'unknowns': list(after['unknowns']),
            'complete': not after['unknowns']}


def apply_acceptances(report, document):
    if not isinstance(document, dict) or set(document) != {'schema_version', 'accept'} or type(document['schema_version']) is not int or document['schema_version'] != 1 or not isinstance(document['accept'], list):
        raise InputError('Acceptance file requires schema_version=1 and accept list.')
    known = {item['fingerprint']: item for item in report['findings']}
    used = set()
    for entry in document['accept']:
        if (not isinstance(entry, dict) or set(entry) != {'fingerprint', 'reason'}
                or not isinstance(entry['reason'], str) or not entry['reason'].strip()
                or not isinstance(entry['fingerprint'], str)
                or not re.fullmatch('[0-9a-f]{64}', entry['fingerprint']) or entry['fingerprint'] in used):
            raise InputError('Each acceptance needs a unique fingerprint and nonempty review reason.')
        fingerprint = entry['fingerprint']
        used.add(fingerprint)
        if fingerprint not in known:
            report['unknowns'].append({'code': 'stale_acceptance', 'fingerprint': fingerprint})
        else:
            report['accepted'].append(dict(known[fingerprint], reason=entry['reason']))
    report['findings'] = [item for item in report['findings'] if item['fingerprint'] not in used]
    report['complete'] = not report['unknowns']
    return report


def exit_code(report):
    return 2 if report['unknowns'] else 1 if report['findings'] else 0


def write_new_snapshot(path, snapshot):
    validate_snapshot(snapshot)
    # Exclusive create prevents accidental replacement of the historical baseline.
    payload = json.dumps(snapshot, indent=2, ensure_ascii=True) + '\n'
    if len(payload.encode('utf-8')) > MAX_JSON:
        raise InputError('Snapshot exceeds the 32 MiB JSON limit; scan a smaller site subtree.')
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(payload)
