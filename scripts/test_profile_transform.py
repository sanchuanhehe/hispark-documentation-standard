from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
import re
import sys
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from profile_transform import (  # noqa: E402
    ProfileError,
    apply_manifest,
    apply_selector,
    load_manifest,
    read_documents,
    strip_fenced_code_blocks,
)


class SelectorTests(unittest.TestCase):
    def test_removes_one_exact_line_and_preserves_final_newline(self) -> None:
        text = "alpha\nremove me\nomega\n"
        result = apply_selector(
            text,
            {"kind": "line", "text": "remove me", "path": "docs/test.md"},
            "docs/test.md",
        )
        self.assertEqual(result, "alpha\nomega\n")

    def test_exact_line_selector_fails_on_missing_or_duplicate_text(self) -> None:
        selector = {"kind": "line", "text": "remove me", "path": "docs/test.md"}
        with self.assertRaisesRegex(ProfileError, "matches=0"):
            apply_selector("alpha\n", selector, "docs/test.md")
        with self.assertRaisesRegex(ProfileError, "matches=2"):
            apply_selector("remove me\nremove me\n", selector, "docs/test.md")

    def test_section_stops_at_next_same_level_heading(self) -> None:
        text = "# Chapter\n\n## Keep\nA\n\n## Remove\nB\n### Child\nC\n\n## Keep too\nD\n"
        result = apply_selector(
            text,
            {"kind": "section", "heading": "## Remove", "path": "docs/test.md"},
            "docs/test.md",
        )
        self.assertEqual(result, "# Chapter\n\n## Keep\nA\n\n## Keep too\nD\n")

    def test_admonition_selector_handles_nested_directives(self) -> None:
        text = (
            "before\n"
            ":::{admonition} Optional\n"
            "body\n"
            ":::{note}\n"
            "nested\n"
            ":::\n"
            ":::\n"
            "after\n"
        )
        result = apply_selector(
            text,
            {"kind": "admonition", "title": "Optional", "path": "docs/test.md"},
            "docs/test.md",
        )
        self.assertEqual(result, "before\nafter\n")

    def test_admonition_selector_ignores_closing_marker_inside_tilde_fence(self) -> None:
        text = (
            "before\n"
            ":::{admonition} Optional\n"
            "~~~text\n"
            ":::\n"
            "~~~\n"
            "body\n"
            ":::\n"
            "after\n"
        )
        result = apply_selector(
            text,
            {"kind": "admonition", "title": "Optional", "path": "docs/test.md"},
            "docs/test.md",
        )
        self.assertEqual(result, "before\nafter\n")

    def test_fence_parser_rejects_unclosed_tilde_fence(self) -> None:
        with self.assertRaisesRegex(ProfileError, "unclosed fenced code block"):
            strip_fenced_code_blocks("~~~text\nbody\n", "docs/test.md")

    def test_admonition_selector_fails_closed_on_unclosed_block(self) -> None:
        with self.assertRaisesRegex(ProfileError, "unclosed admonition"):
            apply_selector(
                ":::{admonition} Optional\nbody\n",
                {"kind": "admonition", "title": "Optional", "path": "docs/test.md"},
                "docs/test.md",
            )


class RepositoryProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load_manifest(ROOT, "core")
        cls.annotated = read_documents(ROOT)
        cls.before_hashes = {
            path: hashlib.sha256(text.encode("utf-8")).hexdigest()
            for path, text in cls.annotated.items()
        }
        cls.core, cls.summary = apply_manifest(cls.annotated, cls.manifest)

    def test_manifest_shape_is_deliberate(self) -> None:
        kinds = Counter(selector["kind"] for selector in self.manifest["selectors"])
        self.assertEqual(kinds, {"section": 1, "admonition": 10, "line": 4})
        self.assertEqual(self.summary.selector_count, 15)
        self.assertEqual(len(self.summary.changed_files), 12)

    def test_transform_does_not_mutate_annotated_documents(self) -> None:
        after_hashes = {
            path: hashlib.sha256(text.encode("utf-8")).hexdigest()
            for path, text in self.annotated.items()
        }
        self.assertEqual(after_hashes, self.before_hashes)

    def test_core_removes_only_declared_explanatory_layer(self) -> None:
        combined = "\n".join(self.core.values())
        self.assertNotIn("## 2.2 规范性条款与非规范性说明", combined)
        self.assertNotIn("背景与解决思路：", combined)
        self.assertNotIn("（非规范性）", combined)
        self.assertNotIn("删除测试", combined)
        self.assertNotIn("RISC-V Instruction Set Manual", combined)
        self.assertNotIn("RISC-V ISA Manual：规范性规则标记方法", combined)
        self.assertIn(
            "title: HiSpark 文档规范（Core Profile）", self.core["docs/index.md"]
        )

    def test_core_keeps_unrelated_explanation_content_and_document_status(self) -> None:
        combined = "\n".join(self.core.values())
        self.assertIn("解释说明", combined)
        self.assertIn(":::{admonition} 文档状态", self.core["docs/index.md"])

    def test_core_keeps_document_set_labels_and_references(self) -> None:
        self.assertEqual(set(self.core), set(self.annotated))

        def labels_and_targets(documents: dict[str, str]) -> tuple[Counter[str], Counter[str]]:
            combined = "\n".join(documents.values())
            labels = Counter(re.findall(r"(?m)^\(([-a-z0-9]+)\)=$", combined))
            targets = Counter(re.findall(r"\]\(#([-a-z0-9]+)\)", combined))
            return labels, targets

        annotated_labels, annotated_targets = labels_and_targets(self.annotated)
        core_labels, core_targets = labels_and_targets(self.core)
        self.assertEqual(core_labels, annotated_labels)
        self.assertEqual(core_targets, annotated_targets)
        self.assertEqual(len(core_labels), 5)
        self.assertEqual(sum(core_targets.values()), 5)


if __name__ == "__main__":
    unittest.main()
