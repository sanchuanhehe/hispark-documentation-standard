"""Audit PDF actions and every source-to-destination pair emitted by the build."""
from collections import Counter
import json
from pathlib import Path


def audit_pdf(path, expected=()):
    from pypdf import PdfReader
    reader = PdfReader(path)
    names = reader.named_destinations
    counts, by_page, problems = Counter(), {}, []
    origins = [link['source'] for link in expected]
    if len(set(origins)) != len(origins):
        problems.append('duplicate source marker in link manifest')
    if set(origins) != {name for name in names if name.startswith('hs-link-')}:
        problems.append('PDF source markers differ from link manifest')
    for page_number, page in enumerate(reader.pages):
        for ref in page.get('/Annots', []):
            item = ref.get_object()
            if item.get('/Subtype') != '/Link':
                continue
            action = item.get('/A', {})
            kind = str(action.get('/S', '/GoTo' if '/Dest' in item else 'unknown'))
            counts[kind] += 1
            if kind == '/URI':
                if not str(action.get('/URI', '')).startswith(('https://', 'http://', 'mailto:')):
                    problems.append(f'page {page_number+1}: non-web URI {action}')
            elif kind == '/GoTo':
                dest = action.get('/D', item.get('/Dest'))
                if not isinstance(dest, str) or dest not in names:
                    problems.append(f'page {page_number+1}: unresolved destination {dest}')
                else:
                    by_page.setdefault(page_number, []).append((dest, item['/Rect']))
            else:
                problems.append(f'page {page_number+1}: forbidden link action {kind}')
    for name, dest in names.items():
        if reader.get_destination_page_number(dest) not in range(len(reader.pages)):
            problems.append(f'destination has no page: {name}')
    for link in expected:
        source, target = link['source'], link.get('destination', link['target'])
        if source not in names or target not in names:
            problems.append(f'missing emitted source/target: {source} -> {target}')
            continue
        origin = names[source]
        page_number = reader.get_destination_page_number(origin)
        # A wrapped link may have several rectangles. Its first rectangle must
        # be adjacent to the zero-width origin marker, not merely on this page.
        x, y = float(origin.left), float(origin.top)
        found = any(dest == target and float(rect[0])-3 <= x <= float(rect[2])+3
                    # Table struts raise markers about 4 pt above the glyph box.
                    and float(rect[1])-5 <= y <= float(rect[3])+5
                    for dest, rect in by_page.get(page_number, []))
        if not found:
            problems.append(f'no clickable link at {source} -> {target} on page {page_number+1}')
    if problems:
        raise ValueError('PDF link audit failed:\n' + '\n'.join(problems))
    return {'pages': len(reader.pages), 'actions': dict(counts), 'verified_body_links': len(expected)}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('pdf', type=Path)
    args = parser.parse_args()
    manifest = args.pdf.with_suffix('.links.json')
    if not manifest.is_file():
        parser.error(f'link manifest missing: {manifest}')
    print(json.dumps(audit_pdf(args.pdf, json.loads(manifest.read_text())), ensure_ascii=False))
