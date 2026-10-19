from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pypdf import PdfWriter
from build_latex import font_families, prepare_compile_fonts, stamp_identity
from build_pdfs import EDITIONS, audit_open_fonts, digest, run_logged, verify_pdfs
from release import bundle
import test_release
from validate_pdf_links import audit_pdf


class FontProfileTests(unittest.TestCase):
    def test_compile_fonts_use_portable_explicit_path_and_ttc_index(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            main = root / "main.tex"
            main.write_text(r"\setmainfont{Arial}" + "\n" + r"\setCJKmainfont{Microsoft YaHei}")
            for name in ("latin.ttf", "cjk.ttc"):
                (root / name).write_bytes(b"font-fixture")
            with patch("build_latex.BUILD", root), patch.dict(os.environ, {"PDF_FONT_PROFILE": "open"}), \
                 patch("build_latex.resolve_font", side_effect=lambda family, style: root / (
                     "cjk.ttc" if family == "Noto Sans CJK SC" else "latin.ttf")), \
                 patch("build_latex.subprocess.check_output", return_value="2"):
                original, links = prepare_compile_fonts(main)
            self.assertIn("Microsoft YaHei", original)
            self.assertEqual(main.read_text().count("Path=./"), 2)
            self.assertEqual(main.read_text().count("FontIndex=2"), 1)
            self.assertIn("Extension=.ttf", main.read_text())
            self.assertIn("Extension=.ttc", main.read_text())
            self.assertIn("UprightFont=hispark-latin-regular,", main.read_text())
            self.assertNotIn("UprightFont=hispark-latin-regular.ttf", main.read_text())
            self.assertNotIn(str(root), main.read_text())
            self.assertEqual(len(links), 6)

    def test_profiles_are_explicit_and_unknown_values_fail(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(font_families(), ("Arial", "Microsoft YaHei"))
        with patch.dict(os.environ, {"PDF_FONT_PROFILE": "open"}):
            self.assertEqual(font_families(), ("Liberation Sans", "Noto Sans CJK SC"))
        with patch.dict(os.environ, {"PDF_FONT_PROFILE": "fallback"}):
            with self.assertRaises(ValueError):
                font_families()

    def test_cover_identity_is_validated_and_stamped(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "main.tex"
            path.write_text(r"\date{old}")
            identity = {"version": "1.2.3", "release_date": "2026-09-24",
                        "commit": "a" * 40, "channel": "dev"}
            with patch.dict(os.environ, {"PDF_FONT_PROFILE": "open",
                                         "HISPARK_PDF_IDENTITY": json.dumps(identity)}):
                stamp_identity(path)
            self.assertIn("v1.2.3", path.read_text())
            self.assertIn("非正式发布", path.read_text())
            self.assertIn("Noto Sans CJK SC", path.read_text())
            identity["version"] = r"\input{secret}"
            with patch.dict(os.environ, {"HISPARK_PDF_IDENTITY": json.dumps(identity)}):
                with self.assertRaises(ValueError):
                    stamp_identity(path)

    def test_actual_font_names_and_embedding_are_checked(self):
        header = "name type encoding emb sub uni object ID\n--------\n"
        good = ("AAAAAA+LiberationSans CID TrueType Identity-H yes yes yes 4 0\n"
                "BBBBBB+NotoSansCJKsc-Regular-Identity-H CID Type 0C Identity-H yes yes yes 6 0\n")
        with patch("build_pdfs.subprocess.check_output", return_value=header + good):
            self.assertEqual(len(audit_open_fonts(Path("fixture.pdf"))), 2)
        for bad in (good.replace("CJKsc", "CJKkr"), good.replace("yes yes yes", "no yes yes")):
            with patch("build_pdfs.subprocess.check_output", return_value=header + bad):
                with self.assertRaises(ValueError):
                    audit_open_fonts(Path("fixture.pdf"))

    def test_process_exit_diagnostics_and_timeout_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            env = dict(os.environ)
            for script in ("raise SystemExit(7)", "print('⛔ diagnostics')"):
                with self.assertRaises(RuntimeError):
                    run_logged([sys.executable, "-c", script], root, root / "failure.log", env)
            with self.assertRaises(TimeoutError):
                run_logged([sys.executable, "-c", "import time; time.sleep(10)"],
                           root, root / "timeout.log", env, timeout=0.05)


class PdfManifestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.version, self.commit = "0.1.6", "b" * 40
        self.font_patch = patch("build_pdfs.audit_open_fonts", return_value=["fixture-font"])
        self.font_patch.start()
        self.addCleanup(self.font_patch.stop)
        self.manifest = {"schema_version": 1, "version": self.version, "commit": self.commit,
                         "channel": "release", "font_profile": "open", "inputs": {"docs/x.md": {"sha256": "a" * 64}},
                         "editions": {}}
        self.manifest.update(fonts=[{
            "family": family, "style": style, "file": "fixture.ttf", "size": 100,
            "sha256": "a" * 64, "collection_index": 0, "postscript_name": face,
        } for family, face, styles in (
            ("Liberation Sans", "LiberationSans", ("Regular", "Bold", "Italic", "Bold Italic")),
            ("Noto Sans CJK SC", "NotoSansCJKsc-Regular", ("Regular", "Bold"))) for style in styles],
            toolchain={tool: "fixture-version" for tool in ("xelatex", "latexmk", "fc-match")},
            platform="fixture-platform")
        for edition, stem in EDITIONS.items():
            pdf, links = self.root / f"{stem}-v{self.version}.pdf", self.root / f"{stem}-v{self.version}.links.json"
            writer = PdfWriter()
            writer.add_blank_page(width=100, height=100)
            with pdf.open("wb") as stream:
                writer.write(stream)
            links.write_text("[]")
            self.manifest["editions"][edition] = {"pdf": pdf.name, "links": links.name,
                "file": digest(pdf), "link_file": digest(links), "audit": audit_pdf(pdf, []),
                "embedded_fonts": ["fixture-font"]}
        self.save()

    def save(self):
        (self.root / "pdf-manifest.json").write_text(json.dumps(self.manifest))

    def verify(self):
        return verify_pdfs(self.root, self.version, self.commit, "release")

    def test_complete_manifest_and_all_editions(self):
        self.assertEqual(len(self.verify()["editions"]), 3)

    def test_font_selection_and_toolchain_provenance_are_required(self):
        for key in ("fonts", "toolchain", "platform"):
            original = self.manifest.pop(key)
            self.save()
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.verify()
            self.manifest[key] = original
        self.manifest["fonts"][-1]["postscript_name"] = "NotoSansCJKjp-Regular"
        self.save()
        with self.assertRaises(ValueError):
            self.verify()

    def test_missing_pdf_link_report_or_manifest_fails(self):
        for path in [self.root / "pdf-manifest.json", *self.root.glob("*.pdf"), *self.root.glob("*.links.json")]:
            data = path.read_bytes()
            path.unlink()
            with self.assertRaises((ValueError, FileNotFoundError)):
                self.verify()
            path.write_bytes(data)

    def test_identity_profile_and_coverage_fail_closed(self):
        for key, value in (("version", "9.9.9"), ("commit", "a" * 40), ("channel", "dev"),
                           ("font_profile", "licensed"), ("inputs", {}), ("editions", {})):
            original = self.manifest[key]
            self.manifest[key] = value
            self.save()
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.verify()
            self.manifest[key] = original

    def test_tamper_bad_report_and_path_traversal_fail(self):
        record = self.manifest["editions"]["core"]
        for key, value in (("file", {"sha256": "0" * 64, "size": 1}),
                           ("audit", {}), ("pdf", "../outside.pdf"), ("embedded_fonts", [])):
            original = record[key]
            record[key] = value
            self.save()
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.verify()
            record[key] = original

    def test_bundle_requires_matching_site_and_pdf_sources(self):
        helper = test_release.ReleaseArtifactTests()
        helper.setUp()
        self.addCleanup(helper.doCleanups)
        site = helper.site(helper.root / "root", version=self.version)
        fixed = helper.site(helper.root / "version", version=self.version, base="/repo/v" + self.version)
        self.manifest["commit"] = helper.commit
        self.save()
        output = self.root / "assets"
        bundle(site, fixed, output, "v" + self.version, "/repo", self.root)
        self.assertEqual(len((output / "SHA256SUMS").read_text().splitlines()), 9)
        self.assertEqual(len(list(output.glob("*.pdf"))), 3)
        self.assertTrue((output / "pdf-manifest.json").is_file())
        for directory in (site, fixed):
            path = directory / "build-manifest.json"
            manifest = json.loads(path.read_text())
            manifest["markdown_sources"] = [{"source": "docs/x.md", "sha256": "wrong"}]
            path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "source identity"):
            bundle(site, fixed, self.root / "bad-assets", "v" + self.version, "/repo", self.root)


if __name__ == "__main__":
    unittest.main()
