"""Compare protected Markdown structure before and after a prose-only edit.

This catches accidental changes to literals and requirement strength, not changes
in meaning. Passing it does not replace a clause-by-clause editorial review.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess

from profile_transform import _next_fence_state
from validate_structure import KEYWORDS

ROOT = Path(__file__).resolve().parents[1]


def protected_parts(text: str) -> dict:
    frontmatter = re.match(r"\A---\n.*?\n---\n", text, re.S)
    if not frontmatter:
        raise ValueError("missing frontmatter")
    body = text[frontmatter.end():]
    fences, prose, block = [], [], []
    state = None
    for line in body.splitlines(keepends=True):
        before = state
        state = _next_fence_state(line.rstrip("\n"), state)
        if before is not None or state is not None:
            block.append(line)
            if state is None:
                fences.append("".join(block))
                block = []
        else:
            prose.append(line)
    if state is not None:
        raise ValueError("unclosed code fence")
    body = "".join(prose)
    # Keep normative keywords scoped to their existing heading, not just totals.
    requirements = []
    heading = "<introduction>"
    words = []
    for line in body.splitlines():
        if re.match(r"^#{1,6} ", line):
            requirements.append((heading, words))
            heading, words = line, []
        else:
            words.extend(KEYWORDS.findall(line))
    requirements.append((heading, words))
    return {
        "frontmatter": frontmatter.group(),
        "headings": re.findall(r"(?m)^#{1,6} .+$", body),
        "explicit_labels": re.findall(r"(?m)^\([^)]+\)=$", body),
        "directives": re.findall(r"(?m)^:::+.*$|^:class:.*$", body),
        "code_blocks": fences,
        "inline_literals": re.findall(r"(`+)(?!`)(.*?)(?<!`)\1(?!`)", body),
        "link_targets": re.findall(r"\]\(([^\s)]+)\)", body),
        "requirements_by_section": requirements,
    }


def compare(before: str, after: str) -> list[str]:
    old, new = protected_parts(before), protected_parts(after)
    return [key for key in old if old[key] != new[key]]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", default="HEAD")
    args = parser.parse_args()
    # Resolve to an object id before constructing any git object:path arguments.
    revision = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"{args.base_ref}^{{commit}}"],
        cwd=ROOT, text=True,
    ).strip()
    tracked = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", revision, "--", "docs"],
        cwd=ROOT, text=True,
    ).splitlines()
    paths = sorted(path for path in tracked if path.endswith(".md"))
    current = sorted(str(path.relative_to(ROOT)) for path in (ROOT / "docs").rglob("*.md"))
    errors = []
    if paths != current:
        errors.append({"path": "docs/", "changed_protected_parts": ["document_inventory"]})
    results = []
    for path in paths:
        if not (ROOT / path).is_file():
            continue
        before = subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT, text=True)
        after = (ROOT / path).read_text(encoding="utf-8")
        try:
            changes = compare(before, after)
        except ValueError as error:
            changes = [str(error)]
        results.append({"path": path, "edited": before != after, "changed_protected_parts": changes})
        if changes:
            errors.append(results[-1])
    counts = Counter()
    for path in paths:
        if (ROOT / path).is_file():
            counts.update(KEYWORDS.findall((ROOT / path).read_text(encoding="utf-8")))
    print(json.dumps({
        "base_commit": revision,
        "boundary": "Protected structure and keyword sequences only; semantic review is separate.",
        "documents": results,
        "keyword_counts": dict(counts),
        "errors": errors,
        "status": "failed" if errors else "passed",
    }, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
