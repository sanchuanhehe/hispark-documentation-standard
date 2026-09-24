"""Editorial safeguards: bilingual wording must not reverse BCP 14 meaning."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_structure import BCP14_DECLARATION, KEYWORD_ZH, keyword_style_errors
from profile_transform import apply_manifest, load_manifest, read_documents
from build_basics import reading_extract

ROOT = Path(__file__).resolve().parents[1]


class KeywordStyleTests(unittest.TestCase):
    def test_all_keyword_pairs(self):
        for word, chinese in KEYWORD_ZH.items():
            with self.subTest(word=word):
                self.assertEqual(keyword_style_errors(f"要求{chinese}（{word}）满足。", "test"), [])

    def test_bare_and_mismatched_keywords_fail(self):
        for text in ("文档 MUST 验证。", "可以（MUST）", "必须（MUST NOT）",
                     "推荐（NOT RECOMMENDED）", "必须(MUST)", "必须（MUST",
                     "必须（MUST）NOT", "应当（SHOULD NOT）"):
            with self.subTest(text=text):
                self.assertTrue(keyword_style_errors(text, "test"))

    def test_negative_keywords_are_indivisible(self):
        for text in ("不得（MUST NOT）", "不得（SHALL NOT）", "不应（SHOULD NOT）",
                     "不推荐（NOT RECOMMENDED）"):
            self.assertEqual(keyword_style_errors(text, "test"), [])

    def test_code_and_identifiers_are_literal(self):
        text = "`MUST`、``SHOULD``、MUST_FIELD\n```text\nMUST\n```\n~~~\nSHOULD\n~~~\n"
        self.assertEqual(keyword_style_errors(text, "test"), [])
        self.assertTrue(keyword_style_errors("`MUST` 后 SHOULD 校验", "test"))

    def test_only_exact_declaration_is_exempt(self):
        self.assertEqual(keyword_style_errors(BCP14_DECLARATION, "test"), [])
        self.assertTrue(keyword_style_errors(BCP14_DECLARATION + " MUST", "test"))

    def test_diagnostics_keep_original_line_numbers(self):
        errors = keyword_style_errors("```\nMUST\n```\n文档 MUST 验证。", "docs/test.md")
        self.assertEqual(len(errors), 1)
        self.assertIn("docs/test.md:4:4:", errors[0])

    def test_unclosed_fences_fail(self):
        self.assertTrue(keyword_style_errors("~~~\nMUST", "test"))

    def test_profiles_and_reading_extract(self):
        documents = read_documents(ROOT)
        core, _ = apply_manifest(documents, load_manifest(ROOT, "core"))
        for profile in (documents, core):
            for path, text in profile.items():
                with self.subTest(path=path):
                    self.assertEqual(keyword_style_errors(text, path), [])
            language = profile["docs/part-1-foundations/02-normative-language.md"]
            self.assertEqual(language.count(BCP14_DECLARATION), 1)
        self.assertEqual(keyword_style_errors(reading_extract(), "reading-extract"), [])


if __name__ == "__main__":
    unittest.main()
