from collections import Counter
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

EXPECTED = [
    "docs/index.md",
    "docs/preface.md",
    "docs/part-1-foundations/01-scope-and-purpose.md",
    "docs/part-1-foundations/02-normative-language.md",
    "docs/part-1-foundations/03-terminology.md",
    "docs/part-1-foundations/04-core-principles.md",
    "docs/part-2-authoring/05-information-architecture.md",
    "docs/part-2-authoring/06-authoring.md",
    "docs/part-2-authoring/07-upstream-downstream.md",
    "docs/part-2-authoring/08-specialized-content.md",
    "docs/part-3-quality/09-validation-and-testing.md",
    "docs/part-3-quality/10-review-and-merge.md",
    "docs/part-3-quality/11-daily-ci.md",
    "docs/part-4-governance/12-governance-and-maintenance.md",
    "docs/part-4-governance/13-migration.md",
    "docs/part-4-governance/14-conformance-checklist.md",
    "docs/backmatter/15-references.md",
    "docs/backmatter/appendix-a-directory-mapping.md",
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


actual = sorted(str(path.relative_to(ROOT)) for path in DOCS.rglob("*.md"))
if actual != sorted(EXPECTED):
    fail(f"unexpected document set: expected={sorted(EXPECTED)}, actual={actual}")

all_text = []
labels = Counter()
for relative in EXPECTED:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    all_text.append(text)
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        fail(f"missing MyST frontmatter: {relative}")
    if not re.search(r"(?m)^title:\s*.+$", text.split("---", 2)[1]):
        fail(f"missing title in frontmatter: {relative}")
    if text.count("```") % 2:
        fail(f"unbalanced code fences: {relative}")
    for label in re.findall(r"(?m)^\(([-a-z0-9]+)\)=$", text):
        labels[label] += 1

duplicates = [label for label, count in labels.items() if count > 1]
if duplicates:
    fail(f"duplicate explicit labels: {duplicates}")

combined = "\n".join(all_text)
for target in re.findall(r"\]\(#([-a-z0-9]+)\)", combined):
    if labels[target] != 1:
        fail(f"cross-reference target must exist exactly once: {target}")

paragraphs = [
    re.sub(r"\s+", " ", paragraph.strip())
    for paragraph in re.split(r"\n\s*\n", combined)
    if len(paragraph.strip()) > 80
    and not paragraph.lstrip().startswith(("---", "|", "```", "- "))
]
repeated = [paragraph for paragraph, count in Counter(paragraphs).items() if count > 1]
if repeated:
    fail(f"duplicate long paragraphs detected: {repeated[:3]}")

print(f"Validated {len(EXPECTED)} MyST pages, {len(labels)} explicit labels, and balanced code fences.")
