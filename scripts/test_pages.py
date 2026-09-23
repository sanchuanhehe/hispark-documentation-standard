from pathlib import Path
import hashlib
import json
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_pages import audit_site, publish_markdown, validate_base_url
from build_profile import remove_exports_and_downloads, ROOT


class PagesTests(unittest.TestCase):
    def test_preface_and_first_chapters_are_top_level_and_first(self):
        config = (ROOT / "myst.yml").read_text(encoding="utf-8")
        toc = config.split("  toc:\n")[1].split("  exports:\n")[0]
        expected = [
            "docs/index.md",
            "docs/preface.md",
            "docs/part-1-foundations/01-scope-and-purpose.md",
            "docs/part-1-foundations/02-normative-language.md",
            "docs/part-1-foundations/03-terminology.md",
            "docs/part-1-foundations/04-core-principles.md",
        ]
        top_level = re.findall(r"^    - file: (.+)$", toc, re.MULTILINE)
        self.assertEqual(top_level[:len(expected)], expected)
        for page in expected:
            self.assertEqual(toc.count(f"file: {page}\n"), 1)

    def test_repository_and_root_base_paths(self):
        for value in ("", "/hispark-documentation-standard", "/nested/repo"):
            self.assertEqual(validate_base_url(value), value)

    def test_invalid_base_paths_fail(self):
        for value in ("https://example.com", "repo", "/repo/", "/../repo", "//repo", "/a b"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_base_url(value)

    def test_web_config_preserves_content_but_has_no_unbuilt_downloads(self):
        original = (ROOT / "myst.yml").read_text(encoding="utf-8")
        web = remove_exports_and_downloads(original)
        self.assertNotIn("  exports:", web)
        self.assertNotIn("  downloads:", web)
        self.assertEqual(original.split("  toc:\n")[1].split("  exports:\n")[0],
                         web.split("  toc:\n")[1].split("site:\n")[0])
        self.assertEqual(original.split("site:\n")[1], web.split("site:\n")[1])

    def test_manifest_hashes_actual_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "index.html").write_text('HiSpark <a href="/repo/authoring">page</a>')
            files = audit_site(root, "/repo")
            self.assertGreater(files["index.html"]["size"], 0)
            self.assertEqual(len(files["index.html"]["sha256"]), 64)

    def test_missing_wrong_or_unprefixed_export_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(ValueError):
                audit_site(root, "/repo")
            for html in ("", "Wrong website", "HiSpark without base path"):
                (root / "index.html").write_text(html)
                with self.subTest(html=html), self.assertRaises(ValueError):
                    audit_site(root, "/repo")

    def test_symlink_is_not_deployable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "index.html").write_text("HiSpark /repo/")
            (root / "linked.html").symlink_to(root / "index.html")
            with self.assertRaisesRegex(ValueError, "symbolic"):
                audit_site(root, "/repo")


class MarkdownPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.site = self.root / "site"
        (self.source / "docs").mkdir(parents=True)
        self.site.mkdir()
        self.original = '---\ntitle: 前言\n---\n\n原文 [正文](part/chapter.md)\n'.encode()
        (self.source / "docs/preface.md").write_bytes(self.original)
        (self.site / "preface").mkdir()
        (self.site / "preface/index.html").write_text("HiSpark /repo/")
        self.article = {"kind": "Article", "slug": "preface", "location": "/docs/preface.md"}
        self.metadata = self.site / "preface.json"
        self.write_metadata()

    def write_metadata(self):
        self.metadata.write_text(json.dumps(self.article))

    def test_raw_alias_and_original_path_are_byte_identical(self):
        records = publish_markdown(self.source, self.site)
        self.assertEqual(len(records), 1)
        for path in records[0]["paths"]:
            self.assertEqual((self.site / path).read_bytes(), self.original)
        self.assertEqual(records[0]["sha256"], hashlib.sha256(self.original).hexdigest())

    def test_index_and_nested_source_mapping(self):
        self.article.update(slug="index")
        self.write_metadata()
        (self.site / "index.html").write_text("HiSpark /repo/")
        (self.source / "docs/part").mkdir()
        (self.source / "docs/part/chapter.md").write_text("# Chapter")
        (self.site / "chapter").mkdir()
        (self.site / "chapter/index.html").write_text("HiSpark /repo/")
        (self.site / "chapter.json").write_text(json.dumps(
            {"kind": "Article", "slug": "chapter", "location": "/docs/part/chapter.md"}))
        records = publish_markdown(self.source, self.site)
        self.assertEqual(len(records), 2)
        self.assertEqual((self.site / "index.md").read_bytes(), self.original)
        self.assertEqual((self.site / "docs/part/chapter.md").read_text(), "# Chapter")

    def test_unrendered_source_blocks_publication(self):
        (self.source / "docs/hidden.md").write_text("not rendered")
        with self.assertRaisesRegex(ValueError, "coverage"):
            publish_markdown(self.source, self.site)
        self.assertFalse((self.site / "preface.md").exists())

    def test_missing_html_or_source_blocks_publication(self):
        for victim in (self.site / "preface/index.html", self.source / "docs/preface.md"):
            original = victim.read_bytes()
            victim.unlink()
            with self.assertRaises(ValueError):
                publish_markdown(self.source, self.site)
            victim.write_bytes(original)

    def test_traversal_and_non_docs_sources_are_rejected(self):
        for location in ("/README.md", "/docs/../README.md", "/docs/./preface.md",
                         "/docs//preface.md", "/docs/preface.txt"):
            self.article["location"] = location
            self.write_metadata()
            with self.subTest(location=location), self.assertRaises(ValueError):
                publish_markdown(self.source, self.site)

    def test_unsafe_route_is_rejected(self):
        self.article["slug"] = "../preface"
        self.write_metadata()
        with self.assertRaises(ValueError):
            publish_markdown(self.source, self.site)

    def test_existing_destination_is_not_overwritten(self):
        (self.site / "preface.md").write_text("existing")
        with self.assertRaisesRegex(ValueError, "collision"):
            publish_markdown(self.source, self.site)
        self.assertEqual((self.site / "preface.md").read_text(), "existing")

    def test_duplicate_source_is_rejected(self):
        (self.site / "duplicate.json").write_text(json.dumps(self.article))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            publish_markdown(self.source, self.site)

    def test_symlink_source_and_destination_are_rejected(self):
        path = self.source / "docs/preface.md"
        path.unlink()
        outside = self.root / "outside.md"
        outside.write_bytes(self.original)
        path.symlink_to(outside)
        with self.assertRaises(ValueError):
            publish_markdown(self.source, self.site)
        path.unlink()
        path.write_bytes(self.original)
        (self.site / "docs").symlink_to(self.source / "docs", target_is_directory=True)
        with self.assertRaises(ValueError):
            publish_markdown(self.source, self.site)
        self.assertEqual(path.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
