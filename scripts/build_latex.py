from argparse import ArgumentParser
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import zipfile

from pdf_links import repair_links, resolve_destinations
from validate_pdf_links import audit_pdf


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "exports" / "hispark-documentation-standard-tex.zip"
BUILD = ROOT / "_build" / "latex"
PDF = ROOT / "exports" / "hispark-documentation-standard.pdf"
PREFIX = "hispark-documentation-standard-tex"
EDITION = "full"
FONT_PROFILES = {
    "licensed": ("Arial", "Microsoft YaHei"),
    "open": ("Liberation Sans", "Noto Sans CJK SC"),
}
LINKS = []


def font_families() -> tuple[str, str]:
    profile = os.environ.get("PDF_FONT_PROFILE", "licensed")
    if profile not in FONT_PROFILES:
        raise ValueError(f"unknown PDF_FONT_PROFILE: {profile}")
    return FONT_PROFILES[profile]


def stamp_identity(main: Path) -> None:
    """Version identity is supplied by the verified PDF orchestration entry point."""
    raw = os.environ.get("HISPARK_PDF_IDENTITY")
    if not raw:
        return
    identity = json.loads(raw)
    version, date, commit = (identity[k] for k in ("version", "release_date", "commit"))
    if (not re.fullmatch(r"\d+\.\d+\.\d+", version)
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date)
            or not re.fullmatch(r"[0-9a-f]{40}|local-uncommitted", commit)
            or identity["channel"] not in {"release", "dev"}):
        raise ValueError("invalid PDF identity")
    label = "正式发布" if identity["channel"] == "release" else "开发快照（非正式发布）"
    latin, cjk = font_families()
    text = main.read_text()
    text, count = re.subn(r"\\date\{[^}]*\}", lambda _: (
        f"\\date{{v{version} · {date}\\\\[0.4em]\\small {label} · {commit[:8]}"
        f"\\\\[0.4em]\\small {cjk} / {latin}}}"), text)
    if count != 1:
        raise ValueError("PDF title-page identity anchor missing or duplicated")
    main.write_text(text)


def safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    root = destination.resolve()
    for member in archive.infolist():
        target = (destination / member.filename).resolve()
        if root not in target.parents and target != root:
            raise RuntimeError(f"unsafe archive member: {member.filename}")
    archive.extractall(destination)


def source_code_blocks(text: str) -> list[str]:
    pattern = re.compile(r"(?ms)^```[A-Za-z0-9_+.-]*[^\n]*\n(.*?)^```[ \t]*$")
    return [match.group(1).rstrip("\n") for match in pattern.finditer(text)]


def patch_listings(source: Path, generated: Path) -> int:
    blocks = source_code_blocks(source.read_text(encoding="utf-8"))
    tex = generated.read_text(encoding="utf-8")
    pattern = re.compile(r"(?ms)(\\begin\{lstlisting\}(?:\[[^\]]*\])?\n)(.*?)(\n\\end\{lstlisting\})")
    matches = list(pattern.finditer(tex))
    if len(blocks) != len(matches):
        raise RuntimeError(
            f"code block mismatch for {source.relative_to(ROOT)}: "
            f"source={len(blocks)}, tex={len(matches)}"
        )
    for match, block in reversed(list(zip(matches, blocks))):
        tex = tex[: match.start()] + match.group(1) + block + match.group(3) + tex[match.end() :]
    generated.write_text(tex, encoding="utf-8")
    return len(blocks)


def patch_generated_structure() -> None:
    for path in BUILD.glob(f"{PREFIX}-*.tex"):
        tex = path.read_text(encoding="utf-8")
        tex = tex.replace("\\begin{tabular}", "\\begin{longtable}")
        tex = tex.replace("\\end{tabular}", "\\end{longtable}")
        tex = re.sub(r"\\chapter\{\d+\.\s*", r"\\chapter{", tex, count=1)
        tex = re.sub(r"\\section\{\d+\.\d+\s*", r"\\section{", tex)
        tex = re.sub(r"\\subsection\{\d+\.\d+\.\d+\s*", r"\\subsection{", tex)
        path.write_text(tex, encoding="utf-8")

    main = BUILD / f"{PREFIX}.tex"
    if EDITION == "basics":
        text = main.read_text(encoding="utf-8")
        # Single-article exports embed the body in the main file. Keep source
        # labels (4.1–4.10) without adding the book's automatic 0.x numbering.
        text = text.replace("\\mainmatter", "\\mainmatter\n\\setcounter{secnumdepth}{-1}", 1)
        text = text.replace("\\begingroup\n\\small\n\\tableofcontents\n\\endgroup", "")
        main.write_text(text, encoding="utf-8")
        return

    preface = BUILD / f"{PREFIX}-preface.tex"
    text = preface.read_text(encoding="utf-8")
    text = text.replace("\\chapter{前言}", "\\chapter*{前言}\\addcontentsline{toc}{chapter}{前言}", 1)
    preface.write_text(text, encoding="utf-8")

    appendix = BUILD / f"{PREFIX}-appendix-a-directory-mapping.tex"
    text = appendix.read_text(encoding="utf-8")
    text = text.replace("\\chapter{附录 A：一级目录到 Diátaxis 的推荐映射}", "\\chapter{一级目录到 Diátaxis 的推荐映射}", 1)
    appendix.write_text(text, encoding="utf-8")

    text = main.read_text(encoding="utf-8")
    preface_include = f"\\include{{{PREFIX}-preface}}"
    text = text.replace(
        f"\\mainmatter\n\n{preface_include}",
        f"{preface_include}\n\n\\mainmatter\n\n\\part{{基础}}",
        1,
    )
    part_markers = {
        f"\\include{{{PREFIX}-information-architecture}}": "设计与创作",
        f"\\include{{{PREFIX}-validation-and-testing}}": "质量保证",
        f"\\include{{{PREFIX}-governance-and-maintenance}}": "治理与落地",
    }
    for include, title in part_markers.items():
        text = text.replace(include, f"\\part{{{title}}}\n\n{include}", 1)
    appendix_include = f"\\include{{{PREFIX}-appendix-a-directory-mapping}}"
    text = text.replace(appendix_include, f"\\appendix\n\n{appendix_include}", 1)
    main.write_text(text, encoding="utf-8")


def generated_name(source: Path) -> str:
    stem = re.sub(r"^\d+-", "", source.stem)
    return f"{PREFIX}-{stem}.tex"


def patch_internal_links() -> None:
    global LINKS
    if EDITION == 'basics':
        LINKS = []  # Omitted chapters are intentionally plain-text references.
    else:
        sources, generated = {}, {}
        for source in sorted((ROOT / 'docs').rglob('*.md')):
            name = generated_name(source)
            if (BUILD / name).exists():
                slug = name[len(PREFIX) + 1:-4]
                if slug in sources:
                    raise ValueError(f'duplicate document slug: {slug}')
                sources[slug] = source.read_text(encoding='utf-8')
                generated[slug] = (BUILD / name).read_text(encoding='utf-8')
        fixed, LINKS = repair_links(sources, generated)
        for slug, text in fixed.items():
            (BUILD / f'{PREFIX}-{slug}.tex').write_text(text, encoding='utf-8')
    (BUILD / f'{PREFIX}-links.json').write_text(
        json.dumps(LINKS, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def make_archive() -> None:
    temporary = ARCHIVE.with_suffix(".patched.zip")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(BUILD.glob("*.tex")):
            archive.write(path, path.name)
        archive.write(BUILD / f'{PREFIX}-links.json', f'{PREFIX}-links.json')
    temporary.replace(ARCHIVE)


def resolve_font(family: str, style: str) -> Path:
    """Resolve one exact installed face through Fontconfig."""
    query = f"{family}:style={style}"
    result = subprocess.run(
        ["fc-match", "--format=%{file}\n%{family}\n", query],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(lines) < 2 or family.casefold() not in lines[1].casefold():
        raise RuntimeError(f"required font face not found: {query}")
    font_file = Path(lines[0])
    if not font_file.is_file():
        raise RuntimeError(f"font resolver returned a missing file for {query}: {font_file}")
    return font_file


def prepare_compile_fonts(main: Path) -> tuple[str, list[Path]]:
    """Link resolved faces into the temporary build without persisting host paths."""
    latin_family, cjk_family = font_families()
    faces = {}
    for group, family, styles in (
        ("latin", latin_family, ("Regular", "Bold", "Italic", "Bold Italic")),
        ("cjk", cjk_family, ("Regular", "Bold")),
    ):
        for style in styles:
            source = resolve_font(family, style)
            name = f"hispark-{group}-{style.lower().replace(' ', '-')}{source.suffix}"
            index = subprocess.check_output(
                ["fc-match", "--format=%{index}", f"{family}:style={style}"], text=True).strip()
            if not index.isdigit():
                raise ValueError(f"missing font collection index: {family}/{style}")
            faces[group, style] = (name, source, int(index))
    links: list[Path] = []
    for name, source, _ in faces.values():
        link = BUILD / name
        link.symlink_to(source)
        links.append(link)

    portable = main.read_text(encoding="utf-8")
    def options(group):
        styles = ("Regular", "Bold", "Italic", "Bold Italic") if group == "latin" else ("Regular", "Bold", "Regular", "Bold")
        # Fontspec in TeX Live 2023 can append the inferred extension again
        # to explicit *Font filenames. Declare it once; use stems for faces.
        extension = faces[group, "Regular"][1].suffix
        if any(faces[group, style][1].suffix != extension for style in styles):
            raise ValueError("font faces require different file extensions")
        fields = ["Path=./", f"Extension={extension}"]
        indices = set()
        for key, style in zip(("Upright", "Bold", "Italic", "BoldItalic"), styles):
            name, _, index = faces[group, style]
            fields.append(f"{key}Font={Path(name).stem}")
            indices.add(index)
        if len(indices) != 1:
            raise ValueError("font faces require different collection indices")
        index = indices.pop()
        if faces[group, "Regular"][1].suffix.lower() == ".ttc":
            fields.append(f"FontIndex={index}")
        return "[\n  " + ",\n  ".join(fields) + "\n]{" + Path(faces[group, "Regular"][0]).stem + "}"
    latin, cjk = options("latin"), options("cjk")
    compiled = portable
    for command in ("setmainfont", "setsansfont", "setmonofont"):
        compiled = compiled.replace(f"\\{command}{{Arial}}", f"\\{command}{latin}", 1)
    for command in ("setCJKmainfont", "setCJKsansfont", "setCJKmonofont"):
        compiled = compiled.replace(
            f"\\{command}{{Microsoft YaHei}}", f"\\{command}{cjk}", 1
        )
    main.write_text(compiled, encoding="utf-8")
    return portable, links


def validate_required_font_families() -> None:
    for family in font_families():
        result = subprocess.run(
            ["fc-match", "--format=%{file}\n%{family}\n", family],
            check=True,
            capture_output=True,
            text=True,
        )
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if len(lines) < 2 or family.casefold() not in lines[1].casefold():
            raise RuntimeError(f"required font family not found: {family}")
        font_file = Path(lines[0])
        if not font_file.is_file():
            raise RuntimeError(f"font resolver returned a missing file for {family}: {font_file}")


def compile_pdf() -> None:
    main = BUILD / f"{PREFIX}.tex"
    validate_required_font_families()
    portable_main, font_links = prepare_compile_fonts(main)
    command = [
        "latexmk",
        "-xelatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        main.name,
    ]
    try:
        subprocess.run(command, cwd=BUILD, check=True)
        log = main.with_suffix(".log").read_text(encoding="utf-8", errors="replace")
        forbidden = ["Missing character:", "There were undefined references", "LaTeX Error:"]
        problems = [marker for marker in forbidden if marker in log]
        if problems:
            raise RuntimeError(f"LaTeX log contains blocking diagnostics: {problems}")
        resolved = resolve_destinations(BUILD, LINKS)
        print('PDF link audit:', audit_pdf(main.with_suffix('.pdf'), resolved))
        (BUILD / f'{PREFIX}-links.json').write_text(
            json.dumps(resolved, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        shutil.copy2(main.with_suffix(".pdf"), PDF)
        shutil.copy2(BUILD / f'{PREFIX}-links.json', PDF.with_suffix('.links.json'))
    finally:
        main.write_text(portable_main, encoding="utf-8")
        for link in font_links:
            link.unlink(missing_ok=True)


def main() -> None:
    global ARCHIVE, BUILD, PDF, PREFIX, EDITION
    parser = ArgumentParser()
    parser.add_argument("--tex-only", action="store_true")
    parser.add_argument("--edition", choices=("full", "basics"), default="full")
    args = parser.parse_args()
    EDITION = args.edition
    if EDITION == "basics":
        PREFIX = "hispark-documentation-basics-tex"
        ARCHIVE = ROOT / "exports" / f"{PREFIX}.zip"
        PDF = ROOT / "exports" / "hispark-documentation-basics.pdf"
        BUILD = ROOT / "_build" / "latex-basics"

    if not ARCHIVE.exists():
        raise FileNotFoundError(f"run MyST TeX export first: {ARCHIVE}")
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    with zipfile.ZipFile(ARCHIVE) as archive:
        safe_extract(archive, BUILD)

    patched = 0
    for source in sorted((ROOT / "docs").rglob("*.md")):
        generated = BUILD / generated_name(source)
        if generated.exists():
            patched += patch_listings(source, generated)

    patch_generated_structure()
    patch_internal_links()
    stamp_identity(BUILD / f"{PREFIX}.tex")

    if not args.tex_only:
        compile_pdf()
    make_archive()
    print(f"Patched {patched} literal code blocks from MyST sources; tex_only={args.tex_only}.")


if __name__ == "__main__":
    main()
