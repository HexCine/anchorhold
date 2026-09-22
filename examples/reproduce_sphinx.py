"""Optional independent-generator reproduction. Install Sphinx==9.1.0 first.

Usage: python examples/reproduce_sphinx.py NEW_OUTPUT_DIRECTORY
Only original minimal RST/conf.py created here is executed. Existing dirs refused.
"""
import json
from pathlib import Path
import subprocess
import sys

from anchorhold.core import compare, scan_site


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Expected one new output directory.')
    root = Path(sys.argv[1])
    root.mkdir(parents=True, exist_ok=False)
    for name, titles in [('before', ['3.2.0', '3.1.0', '3.0.0']), ('after', ['3.3.0', '3.2.0', '3.1.0', '3.0.0'])]:
        source = root / name / 'source'
        source.mkdir(parents=True)
        (source / 'conf.py').write_text("project = 'AnchorHold example'\nhtml_theme = 'alabaster'\n", encoding='utf-8')
        text = 'Release history\n===============\n\n' + '\n\n'.join(title + '\n' + '-' * len(title) + '\n\nRelease notes.' for title in titles) + '\n'
        (source / 'index.rst').write_text(text, encoding='utf-8')
        subprocess.run([sys.executable, '-m', 'sphinx', '-q', '-b', 'html', str(source), str(root / name / 'html')], check=True)
    report = compare(scan_site(root / 'before/html'), scan_site(root / 'after/html'))
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0 if sum(item['code'] == 'heading_retargeted' for item in report['findings']) == 3 and not report['unknowns'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
