from pathlib import Path
import io
import json
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release import check, release_metadata, version_key, verify_site, ROOT
from build_pages import add_version_config, version_identity, audit_site, checked_build
from assemble_pages import extract_bundle, merge_sites


class ReleaseMetadataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ("VERSION", "CHANGELOG.md", "package.json", "package-lock.json", "docs/index.md", "myst.yml"):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())
        self.version, self.date, _ = release_metadata(self.root)

    def test_actual_release_is_consistent(self):
        self.assertEqual(check(self.root, "v" + self.version)[0], self.version)

    def test_rejects_mismatched_tag_and_package(self):
        with self.assertRaisesRegex(ValueError, "tag"):
            check(self.root, "v999.999.999")
        package = self.root / "package.json"
        text = json.loads(package.read_text())
        text["version"] = "9.0.0"
        package.write_text(json.dumps(text))
        with self.assertRaisesRegex(ValueError, "package"):
            check(self.root)

    def test_rejects_missing_empty_or_duplicate_notes(self):
        path = self.root / "CHANGELOG.md"
        original = path.read_text()
        for changed in (original.replace("## [Unreleased]", "## Next"),
                        original + f"\n## [{self.version}] - {self.date}\n",
                        original.replace("### Added", "### Invalid")):
            path.write_text(changed)
            with self.assertRaises(ValueError):
                release_metadata(self.root)

    def test_rejects_homepage_and_export_drift(self):
        for name in ("docs/index.md", "myst.yml"):
            p = self.root / name
            original = p.read_text()
            p.write_text(original.replace(self.date, "2020-01-01"))
            with self.assertRaisesRegex(ValueError, "drifted"):
                check(self.root)
            p.write_text(original)

    def test_semver_numeric_sort_and_invalid_tags(self):
        self.assertGreater(version_key("v0.1.10"), version_key("v0.1.9"))
        for tag in ("v01.1.4", "0.1.4", "v0.1.4-rc.1", "../../oops", "v1.2.3\ninjected"):
            with self.assertRaises(ValueError):
                version_key(tag)


class ReleaseArtifactTests(unittest.TestCase):
    def test_zero_exit_with_reported_link_error_is_not_green(self):
        with self.assertRaisesRegex(RuntimeError, "diagnostics"):
            checked_build([sys.executable, "-c", "print('⛔ Link did not resolve')"], ROOT)
        with self.assertRaisesRegex(RuntimeError, "exit=1"):
            checked_build([sys.executable, "-c", "raise SystemExit(1)"], ROOT)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.commit = "a" * 40

    def site(self, path, version="0.1.4", base="/repo", channel="release"):
        path.mkdir(parents=True)
        (path / "index.html").write_text(f"<html><body>HiSpark {base}/</body></html>")
        (path / "version-info.json").write_text(json.dumps(version_identity(base, version, channel, self.commit)))
        manifest = {"version": version, "base_url": base, "commit": self.commit,
                    "channel": channel, "profile": "annotated", "markdown_sources": [],
                    "files": audit_site(path, base)}
        (path / "build-manifest.json").write_text(json.dumps(manifest))
        return path

    def release(self, tag):
        tree = self.root / tag
        self.site(tree / "root", tag[1:])
        self.site(tree / "version", tag[1:], f"/repo/{tag}")
        return (tag, tree, self.commit)

    def test_notice_uses_root_even_in_nested_version(self):
        path = self.site(self.root / "notice", base="/repo/v0.1.4")
        info = json.loads((path / "version-info.json").read_text())
        self.assertEqual(info["root"], "/repo")
        config = self.root / "myst.yml"
        config.write_text("site:\n  template: book-theme\n")
        add_version_config(config, info)
        self.assertIn("正式版本 v0.1.4", config.read_text())
        self.assertIn('/repo/versions/', config.read_text())
        with self.assertRaises(ValueError):
            add_version_config(config, info)
        self.assertEqual(verify_site(path, "v0.1.4", "/repo/v0.1.4")["commit"], self.commit)

    def test_tampered_missing_and_extra_files_block_release(self):
        path = self.site(self.root / "tamper")
        for filename in ("index.html", "unexpected.txt"):
            file = path / filename
            old = file.read_bytes() if file.exists() else None
            file.write_text("tamper")
            with self.assertRaises(ValueError):
                verify_site(path, "v0.1.4", "/repo")
            if old is None:
                file.unlink()
            else:
                file.write_bytes(old)
        with self.assertRaisesRegex(ValueError, "identity"):
            verify_site(path, "v0.1.4", "/repo", "b" * 40)

    def test_merge_keeps_old_version_bytes_and_stable_not_dev(self):
        dev = self.site(self.root / "dev", base="/repo/dev", channel="dev")
        older, newer = self.release("v0.1.4"), self.release("v0.1.10")
        original = (older[1] / "version/index.html").read_bytes()
        output = self.root / "output"
        merge_sites(dev, [older, newer], output, "/repo")
        versions = json.loads((output / "versions.json").read_text())
        self.assertEqual(versions["latest"], "v0.1.10")
        self.assertEqual((output / "v0.1.4/index.html").read_bytes(), original)
        self.assertEqual((output / "index.html").read_bytes(), (newer[1] / "root/index.html").read_bytes())
        self.assertEqual(json.loads((output / "dev/version-info.json").read_text())["channel"], "dev")

    def test_bad_release_or_dev_never_creates_deployment(self):
        dev = self.site(self.root / "dev", base="/repo/dev", channel="dev")
        release = self.release("v0.1.4")
        (release[1] / "version/index.html").unlink()
        with self.assertRaises(ValueError):
            merge_sites(dev, [release], self.root / "output", "/repo")
        self.assertFalse((self.root / "output").exists())
        (dev / "version-info.json").write_text("{}")
        with self.assertRaises(ValueError):
            merge_sites(dev, [], self.root / "output", "/repo")

    def test_bootstrap_does_not_claim_stable(self):
        dev = self.site(self.root / "dev", base="/repo/dev", channel="dev")
        merge_sites(dev, [], self.root / "output", "/repo")
        self.assertIn("尚无正式发布", (self.root / "output/index.html").read_text())

    def test_archive_rejects_traversal_links_duplicates(self):
        for name, kind, duplicate in (("../escape", tarfile.REGTYPE, False),
                                      ("root/link", tarfile.SYMTYPE, False),
                                      ("root/file", tarfile.REGTYPE, True)):
            with self.subTest(name=name, kind=kind):
                archive = self.root / "bad.tar.gz"
                with tarfile.open(archive, "w:gz") as tar:
                    member = tarfile.TarInfo(name)
                    member.type = kind
                    member.size = 0
                    tar.addfile(member, io.BytesIO())
                    if duplicate:
                        tar.addfile(member, io.BytesIO())
                with self.assertRaises(ValueError):
                    extract_bundle(archive, self.root / "extracted")
                self.assertFalse((self.root / "extracted").exists())

    def test_safe_archive_round_trip(self):
        path = self.site(self.root / "source")
        archive = self.root / "site.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(path, arcname="root")
        extract_bundle(archive, self.root / "extracted")
        self.assertEqual((self.root / "extracted/root/index.html").read_bytes(), (path / "index.html").read_bytes())


if __name__ == "__main__":
    unittest.main()
