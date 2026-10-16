import argparse
import html
from pathlib import Path
import re
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+', type=Path)
    parser.add_argument('--project', default='ResolveDesk')
    args = parser.parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        for source in args.files:
            content = re.sub(r'\x1b\[[0-9;]*m', '', source.read_text())
            title = source.stem.replace('-', ' ').title()
            page.set_content('<html><head><style>body{background:#101f25;color:#e2ece8;padding:38px;font:18px system-ui}h1{font-size:28px}p{color:#a8c9be}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.55 monospace}</style></head><body><h1>' + html.escape(title) + '</h1><p>' + html.escape(args.project) + ' · Recorded command output</p><pre>' + html.escape(content) + '</pre></body></html>')
            page.screenshot(path=str(source.with_suffix('.png')), full_page=True)
        browser.close()


if __name__ == '__main__':
    main()
