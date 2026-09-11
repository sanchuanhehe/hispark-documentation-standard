from argparse import ArgumentParser
from pathlib import Path
import json
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
REQUIRED_FONTS = ("Arial", "Microsoft YaHei")
LINKS = []


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
    faces = {
        "hispark-arial-regular.ttf": resolve_font("Arial", "Regular"),
        "hispark-arial-bold.ttf": resolve_font("Arial", "Bold"),
        "hispark-arial-italic.ttf": resolve_font("Arial", "Italic"),
        "hispark-arial-bold-italic.ttf": resolve_font("Arial", "Bold Italic"),
        "hispark-yahei-regular.ttc": resolve_font("Microsoft YaHei", "Regular"),
        "hispark-yahei-bold.ttc": resolve_font("Microsoft YaHei", "Bold"),
    }
    links: list[Path] = []
    for name, source in faces.items():
        link = BUILD / name
        link.symlink_to(source)
        links.append(link)

    portable = main.read_text(encoding="utf-8")
    latin = """[
  UprightFont=hispark-arial-regular.ttf,
  BoldFont=hispark-arial-bold.ttf,
  ItalicFont=hispark-arial-italic.ttf,
  BoldItalicFont=hispark-arial-bold-italic.ttf
]{hispark-arial-regular.ttf}"""
    cjk = """[
  UprightFont=hispark-yahei-regular.ttc,
  BoldFont=hispark-yahei-bold.ttc,
  ItalicFont=hispark-yahei-regular.ttc,
  BoldItalicFont=hispark-yahei-bold.ttc,
  FontIndex=0
]{hispark-yahei-regular.ttc}"""
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
    for family in REQUIRED_FONTS:
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

    if not args.tex_only:
        compile_pdf()
    make_archive()
    print(f"Patched {patched} literal code blocks from MyST sources; tex_only={args.tex_only}.")


if __name__ == "__main__":
    main()
