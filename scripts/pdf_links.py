"""Repair MyST 1.10 TeX links using the exported source heading inventory.

Do not modify canonical Markdown or the installed exporter. Unknown targets,
ambiguous rendered references and heading drift fail before publication.
"""
from collections import Counter
import re
from urllib.parse import unquote, urlsplit

from profile_transform import strip_fenced_code_blocks


def protect_listings(text):
    saved = []
    def hide(match):
        saved.append(match.group())
        return f"HISPARKLITERAL{len(saved) - 1}END"
    text = re.sub(r"(?s)\\begin\{lstlisting\}.*?\\end\{lstlisting\}", hide, text)
    return text, saved


def restore_listings(text, saved):
    for index, block in enumerate(saved):
        text = text.replace(f"HISPARKLITERAL{index}END", block)
    return text


def group_end(text, start):
    """Find a TeX argument's end, including nested formatting commands."""
    depth = 0
    for i in range(start, len(text)):
        if i and text[i - 1] == '\\':
            continue
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError('unclosed TeX argument')


def repair_links(sources, tex):
    fixed, literals, sections, anchors = {}, {}, {}, {}
    # Source heading order and depth match the generated chapter files. Labels
    # use per-document ordinals, so Core's omitted 2.2 cannot shift another file.
    for slug, original in tex.items():
        source = strip_fenced_code_blocks(sources[slug], slug)
        text, literals[slug] = protect_listings(original)
        headings = list(re.finditer(r'(?m)^(#{2,4}) (.+)$', source))
        emitted = list(re.finditer(r'\\(section|subsection|subsubsection)\{', text))
        if len(headings) != len(emitted):
            raise ValueError(f'heading count differs for {slug}')
        sections[slug] = {}
        inserts = []
        for i, (src, out) in enumerate(zip(headings, emitted), 1):
            depth = {'section': 2, 'subsection': 3, 'subsubsection': 4}[out[1]]
            if depth != len(src[1]):
                raise ValueError(f'heading depth differs for {slug}')
            target = f'hs-{slug}-s{i}'
            number = re.match(r'(\d+(?:\.\d+)+)\s', src[2])
            if number:
                sections[slug][number[1]] = target
            previous = source[:src.start()].rstrip().splitlines()[-1:]
            label = re.fullmatch(r'\(([-a-z0-9]+)\)=', previous[0]) if previous else None
            if label:
                if label[1] in anchors:
                    raise ValueError(f'duplicate explicit anchor: {label[1]}')
                anchors[label[1]] = target
            inserts.append((group_end(text, out.end() - 1), target))
        chapter = re.search(r'\\chapter\*?\{', text)
        if not chapter:
            raise ValueError(f'chapter heading missing: {slug}')
        inserts.append((group_end(text, chapter.end() - 1), f'hs-{slug}'))
        for pos, target in sorted(inserts, reverse=True):
            text = text[:pos] + rf'\label{{{target}}}' + text[pos:]
        fixed[slug] = text

    links = []
    def link(target, title, slug):
        origin = f'hs-link-{len(links) + 1}'
        links.append({'source': origin, 'target': target, 'document': slug})
        # A marker at the start of a p-column must enter horizontal mode;
        # otherwise it inserts a blank first line before the visible link.
        return rf'\leavevmode\hypertarget{{{origin}}}{{}}\hyperref[{target}]{{{title}}}'

    for slug, text in fixed.items():
        # MyST emits explicit-label references with custom titles as plain text
        # (spaces become ~). Check occurrence counts before restoring links.
        source = strip_fenced_code_blocks(sources[slug], slug)
        refs = Counter(re.findall(r'\[([^\]]+)\]\(#([-a-z0-9]+)\)', source))
        titles = {}
        for (title, anchor), count in refs.items():
            if anchor not in anchors:
                raise ValueError(f'unknown explicit anchor: {anchor}')
            rendered = re.sub(r'\s', '~', title)
            if rendered in titles and titles[rendered] != anchor:
                raise ValueError(f'ambiguous reference title: {title}')
            titles[rendered] = anchor
            if text.count(rendered) != count:
                raise ValueError(f'explicit reference count differs for {slug}: {title}')
            text = text.replace(rendered, link(anchors[anchor], rendered, slug), 1) if count == 1 else text
            if count > 1:
                text = re.sub(re.escape(rendered), lambda _: link(anchors[anchor], rendered, slug), text)

        # Parse both arguments, preserving nested formatting in visible text.
        edits = []
        for match in re.finditer(r'\\href\{([^{}]+)\}\{', text):
            url = urlsplit(unquote(match[1]))
            if url.scheme or url.netloc:
                continue
            dest = url.path.strip('/')
            if dest not in fixed:
                raise ValueError(f'unknown PDF chapter: {match[1]}')
            end = group_end(text, match.end() - 1)
            title = text[match.end():end - 1]
            target = f'hs-{dest}'
            if url.fragment:
                if url.fragment not in anchors:
                    raise ValueError(f'unknown explicit anchor: {url.fragment}')
                target = anchors[url.fragment]
            else:
                # Existing links name sections but point to a chapter file.
                # A range/split list lands at its first named section.
                number = re.search(r'第[ ~]*(\d+(?:\.\d+)+)', title)
                if number:
                    if number[1] not in sections[dest]:
                        raise ValueError(f'unknown section {number[1]} in {dest}')
                    target = sections[dest][number[1]]
            edits.append((match.start(), end, link(target, title, slug)))
        for start, end, replacement in reversed(edits):
            text = text[:start] + replacement + text[end:]
        fixed[slug] = restore_listings(text, literals[slug])
    return fixed, links


def resolve_destinations(build, links):
    """Use hyperref's native heading anchors, above the heading rather than below."""
    labels = {}
    for path in build.glob('*.aux'):
        text = path.read_text(encoding='utf-8')
        for match in re.finditer(r'\\newlabel\{(hs-[^}]+)\}\{', text):
            pos = match.end()
            fields = []
            for _ in range(4):
                if text[pos] != '{':
                    raise ValueError(f'invalid auxiliary label: {match[1]}')
                end = group_end(text, pos)
                fields.append(text[pos+1:end-1])
                pos = end
            if match[1] in labels:
                raise ValueError(f'duplicate auxiliary label: {match[1]}')
            labels[match[1]] = fields[3]
    resolved = []
    for link in links:
        if link['target'] not in labels:
            raise ValueError(f'unresolved TeX label: {link["target"]}')
        resolved.append(dict(link, destination=labels[link['target']]))
    return resolved
