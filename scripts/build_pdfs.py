"""Build all PDF editions from an isolated snapshot; archive evidence before release."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from build_profile import ROOT, prepare_shadow, publish_directory, resolve_myst
from build_latex import font_families, resolve_font
from release import check
from validate_pdf_links import audit_pdf

EDITIONS = {
    "annotated": "hispark-documentation-standard",
    "core": "hispark-documentation-standard-core",
    "basics": "hispark-documentation-basics",
}


def audit_open_fonts(pdf: Path) -> list[str]:
    """Inspect embedded font names, not just the requested Fontconfig family."""
    text = subprocess.check_output(["pdffonts", str(pdf)], text=True)
    names = []
    for line in text.splitlines()[2:]:
        fields = line.split()
        if len(fields) < 8 or fields[-5] != "yes":
            raise ValueError("PDF contains an unembedded or unparseable font")
        names.append(re.sub(r"^[A-Z]{6}\+", "", fields[0]))
    # Ubuntu's locked Noto TTC shares the internal CFF PostScript name "jp"
    # across regional faces, including SC (collection index 2). pdffonts shows
    # that shared name; record the selected regional face/index independently.
    if (not any("LiberationSans" in name for name in names)
            or not any("NotoSansCJKsc" in name or "NotoSansCJKjp" in name for name in names)
            or any("Arial" in name or "YaHei" in name for name in names)):
        raise ValueError(f"PDF embedded font profile mismatch: {names}")
    return sorted(names)


def digest(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"missing, empty or unsafe artifact: {path}")
    return {"size": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def input_hashes(root: Path) -> dict:
    paths = [root / name for name in ("VERSION", "CHANGELOG.md", "myst.yml", "package.json",
                                     "package-lock.json", "requirements-pdf.txt")]
    for folder in ("docs", "latex", "profiles", "scripts", ".github/workflows"):
        paths.extend(p for p in (root / folder).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(paths)}


def run_logged(command: list, cwd: Path, log: Path, env: dict, timeout: int = 900) -> None:
    """Bound the full process tree and keep the true exit status in the evidence."""
    print("+ " + " ".join(map(str, command)), flush=True)
    started = time.monotonic()
    with log.open("w") as stream:
        process = subprocess.Popen(list(map(str, command)), cwd=cwd, env=env,
                                   stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            while True:
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise TimeoutError(f"PDF command exceeded {timeout}s: {log.name}")
                try:
                    code = process.wait(timeout=min(30, remaining))
                    break
                except subprocess.TimeoutExpired:
                    print(f"PDF build active: {log.name}, {int(time.monotonic() - started)}s", flush=True)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
                # Descendants can survive their parent; kill the original group.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
    text = log.read_text(errors="replace")
    if code or "⛔" in text:
        print(text[-8000:], flush=True)
        raise RuntimeError(f"PDF command failed: exit={code}; log={log}")


def verify_pdfs(directory: Path, version: str, commit: str, channel: str) -> dict:
    manifest_path = directory / "pdf-manifest.json"
    digest(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    if (manifest.get("schema_version") != 1 or manifest.get("version") != version
            or manifest.get("commit") != commit or manifest.get("channel") != channel
            or manifest.get("font_profile") != "open" or not manifest.get("inputs")
            or set(manifest.get("editions", {})) != set(EDITIONS)):
        raise ValueError("PDF identity, provenance or edition coverage mismatch")
    expected_faces = {(family, style) for family, styles in (
        ("Liberation Sans", ("Regular", "Bold", "Italic", "Bold Italic")),
        ("Noto Sans CJK SC", ("Regular", "Bold"))) for style in styles}
    fonts = manifest.get("fonts", [])
    if (len(fonts) != len(expected_faces)
            or {(font.get("family"), font.get("style")) for font in fonts} != expected_faces
            or any(not re.fullmatch(r"[0-9a-f]{64}", font.get("sha256", ""))
                   or not isinstance(font.get("size"), int) or font["size"] <= 0
                   or not isinstance(font.get("collection_index"), int) or font["collection_index"] < 0
                   or not font.get("file")
                   or not font.get("postscript_name", "").startswith(
                       "NotoSansCJKsc-" if font["family"] == "Noto Sans CJK SC" else "LiberationSans")
                   for font in fonts)
            or not all(manifest.get("toolchain", {}).get(tool) for tool in ("xelatex", "latexmk", "fc-match"))
            or not manifest.get("platform")):
        raise ValueError("PDF font selection or toolchain provenance missing or invalid")
    for edition, stem in EDITIONS.items():
        record = manifest["editions"][edition]
        expected_pdf = f"{stem}-v{version}.pdf"
        expected_links = f"{stem}-v{version}.links.json"
        if record.get("pdf") != expected_pdf or record.get("links") != expected_links:
            raise ValueError("unexpected PDF artifact path")
        pdf, links = directory / expected_pdf, directory / expected_links
        if digest(pdf) != record.get("file") or digest(links) != record.get("link_file"):
            raise ValueError("PDF or link manifest checksum mismatch")
        result = audit_pdf(pdf, json.loads(links.read_text()))
        if result != record.get("audit"):
            raise ValueError("PDF audit report mismatch")
        if audit_open_fonts(pdf) != record.get("embedded_fonts"):
            raise ValueError("PDF embedded font report mismatch")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=("dev", "release"), default="dev")
    parser.add_argument("--output", type=Path, default=ROOT / "_build/pdf-release")
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT / "_build") or args.output.resolve() == ROOT / "_build":
        parser.error("output must be a subdirectory of _build")
    if os.environ.get("PDF_FONT_PROFILE") != "open":
        parser.error("automated PDF artifacts require explicit PDF_FONT_PROFILE=open")
    version, date, _ = check()
    commit = os.environ.get("DOCS_COMMIT", os.environ.get("GITHUB_SHA", "local-uncommitted"))
    if not re.fullmatch(r"[0-9a-f]{40}|local-uncommitted", commit):
        parser.error("invalid commit identity")
    if args.channel == "release" and commit == "local-uncommitted":
        parser.error("release PDF requires an exact commit")
    identity = {"version": version, "release_date": date, "commit": commit, "channel": args.channel}
    inputs = input_hashes(ROOT)
    evidence = ROOT / "_build/pdf-evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    fonts = []
    for family, styles in ((font_families()[0], ("Regular", "Bold", "Italic", "Bold Italic")),
                           (font_families()[1], ("Regular", "Bold"))):
        for style in styles:
            font = resolve_font(family, style)
            face = subprocess.check_output(["fc-match", "--format=%{postscriptname}\n%{index}",
                                            f"{family}:style={style}"], text=True).splitlines()
            if len(face) != 2 or not face[1].isdigit():
                raise ValueError("font face identity missing")
            if family == "Noto Sans CJK SC" and not face[0].startswith("NotoSansCJKsc-"):
                raise ValueError("resolved CJK face is not Simplified Chinese")
            fonts.append({"family": family, "style": style, "file": font.name,
                          "postscript_name": face[0], "collection_index": int(face[1]), **digest(font)})
    toolchain = {tool: subprocess.check_output([tool, "--version"], text=True,
                                              stderr=subprocess.STDOUT).strip().splitlines()[0]
                 for tool in ("xelatex", "latexmk", "fc-match")}
    env = {**os.environ, "HISPARK_PDF_IDENTITY": json.dumps(identity)}
    with tempfile.TemporaryDirectory(prefix="pdf-project-", dir=ROOT / "_build") as temporary:
        shadow = Path(temporary)
        prepare_shadow(shadow, "annotated", include_exports=True)
        for name in ("VERSION", "CHANGELOG.md", "package.json", "package-lock.json", "requirements-pdf.txt"):
            shutil.copyfile(ROOT / name, shadow / name)
        (shadow / "node_modules").symlink_to(ROOT / "node_modules", target_is_directory=True)
        commands = [
            ([resolve_myst(), "build", "--tex", "--strict"], "tex.log"),
            ([sys.executable, "scripts/build_latex.py"], "annotated.log"),
            ([sys.executable, "scripts/build_profile.py", "core", "pdf"], "core.log"),
            ([sys.executable, "scripts/build_basics.py"], "basics.log"),
        ]
        for command, name in commands:
            run_logged(command, shadow, evidence / name, env)
        staged = shadow / "validated-pdfs"
        staged.mkdir()
        editions = {}
        for edition, stem in EDITIONS.items():
            pdf, links = staged / f"{stem}-v{version}.pdf", staged / f"{stem}-v{version}.links.json"
            shutil.copyfile(shadow / "exports" / f"{stem}.pdf", pdf)
            shutil.copyfile(shadow / "exports" / f"{stem}.links.json", links)
            editions[edition] = {"pdf": pdf.name, "links": links.name, "file": digest(pdf),
                                 "link_file": digest(links),
                                 "embedded_fonts": audit_open_fonts(pdf),
                                 "audit": audit_pdf(pdf, json.loads(links.read_text()))}
        if input_hashes(ROOT) != inputs:
            raise ValueError("PDF inputs changed during build")
        manifest = {"schema_version": 1, **identity, "font_profile": "open", "fonts": fonts,
                    "toolchain": toolchain, "platform": platform.platform(),
                    "inputs": inputs, "editions": editions}
        (staged / "pdf-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        verify_pdfs(staged, version, commit, args.channel)
        publish_directory(staged, args.output.resolve())
        shutil.copyfile(staged / "pdf-manifest.json", evidence / "pdf-manifest.json")
        print(f"Validated 3 PDF editions: {args.output}")


if __name__ == "__main__":
    main()
