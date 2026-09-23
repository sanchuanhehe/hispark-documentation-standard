from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_pages import audit_site, validate_base_url
from build_profile import remove_exports_and_downloads, ROOT


class PagesTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
