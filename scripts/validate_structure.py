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


def strip_code_fences(text: str) -> str:
    return re.sub(r"(?ms)^```[^\n]*\n.*?^```[ \t]*$", "", text)


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
    for label in re.findall(r"(?m)^\(([-a-z0-9]+)\)=$", strip_code_fences(text)):
        labels[label] += 1

duplicates = [label for label, count in labels.items() if count > 1]
if duplicates:
    fail(f"duplicate explicit labels: {duplicates}")

combined = "\n".join(all_text)
combined_without_code = strip_code_fences(combined)

informative_blocks = re.findall(
    r"(?ms)^:::\{admonition\} ([^\n]*非规范性[^\n]*)\n.*?^:::$",
    combined_without_code,
)
informative_title_pattern = re.compile(
    r"^(背景与解决思路|实施提示|示例|反例)：[^（）\n]+（非规范性）$"
)
unknown_titles = sorted(
    title for title in set(informative_blocks)
    if not informative_title_pattern.fullmatch(title)
)
if unknown_titles:
    fail(f"unknown informative admonition titles: {unknown_titles}")
if len(informative_blocks) < 10:
    fail(f"expected at least 10 informative blocks, found {len(informative_blocks)}")

for match in re.finditer(
    r"(?ms)^:::\{admonition\} ([^\n]*非规范性[^\n]*)\n(.*?)^:::$",
    combined_without_code,
):
    title = match.group(1)
    body = match.group(2)
    if title.startswith("背景与解决思路："):
        missing_sections = [
            section
            for section in ("**问题背景。**", "**解决机制。**", "**预期效果。**")
            if section not in body
        ]
        if missing_sections:
            fail(
                f"informative block '{title}' lacks required explanatory sections: "
                f"{missing_sections}"
            )
    keyword = re.search(
        r"\b(MUST(?: NOT)?|SHALL(?: NOT)?|SHOULD(?: NOT)?|REQUIRED|RECOMMENDED|NOT RECOMMENDED|MAY|OPTIONAL)\b",
        body,
    )
    if keyword:
        fail(
            f"informative block '{title}' contains normative keyword: "
            f"{keyword.group(1)}"
        )

for target in re.findall(r"\]\(#([-a-z0-9]+)\)", combined_without_code):
    if labels[target] != 1:
        fail(f"cross-reference target must exist exactly once: {target}")

paragraphs = [
    re.sub(r"\s+", " ", paragraph.strip())
    for paragraph in re.split(r"\n\s*\n", combined_without_code)
    if len(paragraph.strip()) > 80
    and not paragraph.lstrip().startswith(("---", "|", "```", "- "))
]
repeated = [paragraph for paragraph, count in Counter(paragraphs).items() if count > 1]
if repeated:
    fail(f"duplicate long paragraphs detected: {repeated[:3]}")

print(
    f"Validated {len(EXPECTED)} MyST pages, {len(labels)} explicit labels, "
    f"{len(informative_blocks)} informative blocks, and balanced code fences."
)
