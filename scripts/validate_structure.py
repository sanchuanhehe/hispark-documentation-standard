from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from profile_transform import (  # noqa: E402
    ProfileError,
    apply_manifest,
    load_manifest,
    read_documents,
    strip_fenced_code_blocks,
)


EXPECTED = [
    "docs/index.md",
    "docs/preface.md",
    "docs/handbook/write-a-page.md",
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


def validate(profile: str) -> None:
    documents = read_documents(ROOT)
    actual = sorted(documents)
    if actual != sorted(EXPECTED):
        fail(f"unexpected document set: expected={sorted(EXPECTED)}, actual={actual}")

    labels = Counter()
    for relative in EXPECTED:
        text = documents[relative]
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            fail(f"missing frontmatter: {relative}")
        if not re.search(r"(?m)^title:\s*.+$", text.split("---", 2)[1]):
            fail(f"missing title in frontmatter: {relative}")
        try:
            text_without_code = strip_fenced_code_blocks(text, relative)
        except ProfileError as error:
            fail(str(error))
        for label in re.findall(r"(?m)^\(([-a-z0-9]+)\)=$", text_without_code):
            labels[label] += 1

    duplicates = [label for label, count in labels.items() if count > 1]
    if duplicates:
        fail(f"duplicate explicit labels: {duplicates}")

    # Editorial additions may change heading and reference counts. Validate
    # actual destinations and navigation membership instead of frozen totals.
    config = (ROOT / "myst.yml").read_text(encoding="utf-8")
    toc = config.split("  toc:\n", 1)[1].split("  exports:\n", 1)[0]
    toc_files = re.findall(r"(?m)^\s+- file: (docs/\S+\.md)$", toc)
    if Counter(toc_files) != Counter(EXPECTED):
        fail("navigation must include every document exactly once")
    for relative, text in documents.items():
        text = strip_fenced_code_blocks(text, relative)
        for destination in re.findall(r"\]\(([^\s)]+)\)", text):
            url = urlsplit(destination)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (ROOT / relative).parent / unquote(url.path)
            if not target.is_file():
                fail(f"missing local link in {relative}: {destination}")

    combined = "\n".join(documents[relative] for relative in EXPECTED)
    try:
        combined_without_code = strip_fenced_code_blocks(combined, "combined documents")
    except ProfileError as error:
        fail(str(error))
    informative_blocks = re.findall(
        r"(?ms)^:::\{admonition\} ([^\n]*非规范性[^\n]*)\n.*?^:::$",
        combined_without_code,
    )
    expected_blocks = 11 if profile == "annotated" else 0
    if len(informative_blocks) != expected_blocks:
        fail(
            f"{profile} profile requires {expected_blocks} informative blocks, "
            f"found {len(informative_blocks)}"
        )

    informative_title_pattern = re.compile(
        r"^(背景与解决思路|实施提示|示例|反例)：[^（）\n]+（非规范性）$"
    )
    unknown_titles = sorted(
        title
        for title in set(informative_blocks)
        if not informative_title_pattern.fullmatch(title)
    )
    if unknown_titles:
        fail(f"unknown informative admonition titles: {unknown_titles}")

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
            r"\b(MUST(?: NOT)?|SHALL(?: NOT)?|SHOULD(?: NOT)?|REQUIRED|"
            r"RECOMMENDED|NOT RECOMMENDED|MAY|OPTIONAL)\b",
            body,
        )
        if keyword:
            fail(
                f"informative block '{title}' contains normative keyword: "
                f"{keyword.group(1)}"
            )

    targets = re.findall(r"\]\(#([-a-z0-9]+)\)", combined_without_code)
    for target in targets:
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

    basics = documents["docs/part-1-foundations/04-core-principles.md"]
    requirements = re.findall(r"(?m)^## 4\.(\d+) ", basics)
    if requirements != [str(number) for number in range(1, 11)]:
        fail("the basic reading entry must contain the ten ordered requirements")

    manifest = load_manifest(ROOT, "core")
    if profile == "annotated":
        if combined_without_code.count("## 2.2 规范性条款与非规范性说明") != 1:
            fail("annotated profile must contain section 2.2 exactly once")
        if "hispark-profile:" in combined_without_code:
            fail("profile markers must not be embedded in source documents")
        _, summary = apply_manifest(documents, manifest)
        if summary.selector_count != 16:
            fail(f"core profile selector count changed unexpectedly: {summary.selector_count}")
    else:
        forbidden = (
            "## 2.2 规范性条款与非规范性说明",
            "背景与解决思路：",
            "（非规范性）",
            "删除测试",
            "RISC-V Instruction Set Manual",
            "RISC-V ISA Manual：规范性规则标记方法",
        )
        leaked = [token for token in forbidden if token in combined_without_code]
        if leaked:
            fail(f"core profile contains annotated-only content: {leaked}")
        if ":::{admonition} 文档状态" not in documents["docs/index.md"]:
            fail("core profile must retain the document-status admonition")
        if "title: HiSpark 文档规范（Core Profile）" not in documents["docs/index.md"]:
            fail("core profile home page must identify itself as Core")
        if "解释说明" not in combined_without_code:
            fail("core profile must retain the Diátaxis explanation document type")

    required_labels = {
        "sample-test-coverage", "sample-execution-levels",
        "sample-maintenance-contract", "review-requirements", "definition-of-done",
    }
    if not required_labels.issubset(labels):
        fail("a published semantic reference label was removed")

    print(
        f"Validated {profile} profile: {len(EXPECTED)} pages, {len(labels)} labels, "
        f"{len(targets)} references, {len(informative_blocks)} informative blocks, "
        f"and balanced code fences."
    )


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--profile", choices=("annotated", "core"), default="annotated")
    args = parser.parse_args()
    validate(args.profile)


if __name__ == "__main__":
    main()
