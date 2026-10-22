"""Regression tests for mechanical safeguards used during prose review."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_prose_guard import compare, protected_parts

SAMPLE = """---
title: 示例
---
(stable-label)=
## 条款
文档必须（MUST）记录 `owner`，详见[依据](rules.md#scope)。
```sh
echo 'MUST'
```
:::{admonition} 示例（非规范性）
:class: note
这是解释。
:::
"""


class ProseGuardTests(unittest.TestCase):
    def test_wording_and_link_label_can_change(self):
        revised = SAMPLE.replace("文档必须", "每篇文档必须").replace("[依据]", "[完整依据]")
        self.assertEqual(compare(SAMPLE, revised), [])

    def test_strength_and_negation_are_protected(self):
        for replacement in ("SHOULD", "MUST NOT", "MAY"):
            revised = SAMPLE.replace("（MUST）", f"（{replacement}）")
            self.assertIn("requirements_by_section", compare(SAMPLE, revised))

    def test_protected_content(self):
        for old, new, key in (
            ("title: 示例", "title: 新标题", "frontmatter"),
            ("## 条款", "## 新条款", "headings"),
            ("stable-label", "other-label", "explicit_labels"),
            ("`owner`", "`author`", "inline_literals"),
            ("rules.md#scope", "rules.md#other", "link_targets"),
            ("echo 'MUST'", "echo 'MAY'", "code_blocks"),
            (":class: note", ":class: warning", "directives"),
        ):
            with self.subTest(key=key):
                self.assertIn(key, compare(SAMPLE, SAMPLE.replace(old, new)))

    def test_keywords_cannot_move_between_sections(self):
        before = SAMPLE + "\n## 另一节\n这里只作介绍。\n"
        after = before.replace("文档必须（MUST）记录", "文档记录").replace("这里只作介绍。", "这里必须（MUST）检查。")
        self.assertIn("requirements_by_section", compare(before, after))

    def test_tilde_fence_is_protected(self):
        before = SAMPLE.replace("```", "~~~")
        self.assertIn("code_blocks", compare(before, before.replace("echo", "printf")))

    def test_unclosed_fence_fails(self):
        with self.assertRaises(ValueError):
            protected_parts(SAMPLE + "\n```sh\necho unfinished\n")

    def test_does_not_claim_semantic_equivalence(self):
        # A limitation, deliberately documented: fixed words do not protect intent.
        self.assertEqual(compare(SAMPLE, SAMPLE.replace("记录", "删除")), [])


if __name__ == "__main__":
    unittest.main()
