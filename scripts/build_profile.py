from __future__ import annotations

from argparse import ArgumentParser
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Iterable
from uuid import uuid4
import zipfile


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from profile_transform import (  # noqa: E402
    ProfileError,
    apply_manifest,
    load_manifest,
    read_documents,
    write_documents,
)


CORE_PROFILE = "core"
CORE_SITE = ROOT / "_build" / "site-core"
CORE_HTML = ROOT / "_build" / "html-core"
CORE_PDF = ROOT / "exports" / "hispark-documentation-standard-core.pdf"
CORE_TEX = ROOT / "exports" / "hispark-documentation-standard-core-tex.zip"
SHADOW_PDF = Path("exports/hispark-documentation-standard.pdf")
SHADOW_TEX = Path("exports/hispark-documentation-standard-tex.zip")
SHADOW_CORE_TEX = Path("exports/hispark-documentation-standard-core-tex.zip")
ANNOTATED_PDF = ROOT / "exports" / "hispark-documentation-standard.pdf"
ANNOTATED_TEX = ROOT / "exports" / "hispark-documentation-standard-tex.zip"
SHADOW_TEX_PREFIX = "hispark-documentation-standard-tex"
CORE_TEX_PREFIX = "hispark-documentation-standard-core-tex"


def run(command: Iterable[str], cwd: Path) -> None:
    argv = [str(part) for part in command]
    print(f"+ {' '.join(argv)}", flush=True)
    subprocess.run(argv, cwd=cwd, check=True)


def resolve_myst() -> Path:
    local = ROOT / "node_modules" / ".bin" / "myst"
    if local.is_file():
        return local
    executable = shutil.which("myst")
    if executable:
        return Path(executable)
    raise FileNotFoundError("MyST CLI not found; run npm install first")


def document_hashes() -> dict[str, str]:
    return {
        path: hashlib.sha256(text.encode("utf-8")).hexdigest()
        for path, text in read_documents(ROOT).items()
    }


def file_hash(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_substitution(
    text: str, pattern: str, replacement: str, expected: int, description: str
) -> str:
    updated, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if count != expected:
        raise ProfileError(
            f"could not rewrite {description}: expected {expected} matches, found {count}"
        )
    return updated


def remove_exports_and_downloads(text: str) -> str:
    text, exports_count = re.subn(
        r"(?ms)^  exports:\n.*?(?=^  downloads:)", "", text
    )
    text, downloads_count = re.subn(
        r"(?ms)^  downloads:\n.*?(?=^site:)", "", text
    )
    if (exports_count, downloads_count) != (1, 1):
        raise ProfileError(
            "could not remove shadow exports/downloads: "
            f"exports={exports_count}, downloads={downloads_count}"
        )
    return text


def write_core_config(destination: Path, manifest: dict, include_exports: bool) -> None:
    text = (ROOT / "myst.yml").read_text(encoding="utf-8")
    title = manifest["title"]
    subtitle = manifest["subtitle"]
    description = manifest["description"]
    text = require_substitution(
        text,
        r"^(\s*)title: HiSpark 文档规范$",
        rf"\1title: {title}",
        4,
        "profile titles",
    )
    text = require_substitution(
        text,
        r"^(\s*)subtitle: 基于 Diátaxis 的 SDK 文档设计、质量与治理要求$",
        rf"\1subtitle: {subtitle}",
        3,
        "profile subtitles",
    )
    text = require_substitution(
        text,
        r"^  description: HiSpark SDK 类项目的文档信息架构、创作、验证、Review、CI 与持续维护规范。$",
        f"  description: {description}",
        1,
        "profile description",
    )
    text = require_substitution(
        text,
        r"^    logo_text: HiSpark 文档规范$",
        f"    logo_text: {title}",
        1,
        "site logo text",
    )

    if not include_exports:
        text = remove_exports_and_downloads(text)
    destination.write_text(text, encoding="utf-8")


def write_annotated_config(destination: Path, include_exports: bool) -> None:
    text = (ROOT / "myst.yml").read_text(encoding="utf-8")
    if not include_exports:
        text = remove_exports_and_downloads(text)
    destination.write_text(text, encoding="utf-8")


def prepare_shadow(shadow: Path, profile: str, include_exports: bool) -> dict | None:
    source_hashes = document_hashes()

    shutil.copytree(ROOT / "docs", shadow / "docs")
    shutil.copytree(ROOT / "latex", shadow / "latex")
    shutil.copytree(
        ROOT / "scripts",
        shadow / "scripts",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    shutil.copytree(ROOT / "profiles", shadow / "profiles")

    template_cache = ROOT / "_build" / "templates"
    if template_cache.is_dir():
        shadow_build = shadow / "_build"
        shadow_build.mkdir()
        (shadow_build / "templates").symlink_to(
            template_cache.resolve(), target_is_directory=True
        )

    manifest: dict | None = None
    if profile == CORE_PROFILE:
        manifest = load_manifest(ROOT, CORE_PROFILE)
        annotated = read_documents(ROOT)
        core, summary = apply_manifest(annotated, manifest)
        write_documents(shadow, core)
        write_core_config(shadow / "myst.yml", manifest, include_exports)

        if summary.selector_count != 15 or len(summary.changed_files) != 12:
            raise ProfileError(
                "unexpected Core transformation scope: "
                f"selectors={summary.selector_count}, files={len(summary.changed_files)}"
            )
        scope = (
            f"{summary.selector_count} selectors, "
            f"{len(summary.changed_files)} changed files"
        )
    else:
        write_annotated_config(shadow / "myst.yml", include_exports)
        scope = "source content unchanged"

    if document_hashes() != source_hashes:
        raise ProfileError("source documents changed while preparing a shadow project")

    run([sys.executable, "scripts/validate_structure.py", "--profile", profile], shadow)
    print(
        f"Prepared {profile} shadow project: {scope}.",
        flush=True,
    )
    return manifest


def ensure_output(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"expected build output is missing or empty: {path}")


def ensure_directory(path: Path) -> None:
    if not path.is_dir() or not any(path.iterdir()):
        raise RuntimeError(f"expected build directory is missing or empty: {path}")


def assert_under(path: Path, parent: Path) -> None:
    resolved_path = path.resolve(strict=False)
    resolved_parent = parent.resolve()
    if resolved_path == resolved_parent or resolved_parent not in resolved_path.parents:
        raise RuntimeError(f"unsafe output path: {path}")


def publish_file(source: Path, destination: Path) -> None:
    ensure_output(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
    shutil.copy2(source, temporary)
    os.replace(temporary, destination)
    print(f"Published {destination}", flush=True)


def publish_directory(source: Path, destination: Path) -> None:
    ensure_directory(source)
    assert_under(destination, ROOT / "_build")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent)
    )
    staging = staging_root / "payload"
    backup = destination.with_name(f".{destination.name}.{uuid4().hex}.backup")
    shutil.copytree(source, staging)
    try:
        if destination.exists():
            if destination.is_symlink():
                raise RuntimeError(f"refusing to replace symlinked output: {destination}")
            os.replace(destination, backup)
        os.replace(staging, destination)
        if backup.exists():
            shutil.rmtree(backup)
    except BaseException:
        if not destination.exists() and backup.exists():
            os.replace(backup, destination)
        raise
    finally:
        if staging_root.exists():
            shutil.rmtree(staging_root)
    print(f"Published {destination}", flush=True)


def preserve_template_cache(shadow: Path) -> None:
    source = shadow / "_build" / "templates"
    destination = ROOT / "_build" / "templates"
    if destination.exists() or source.is_symlink() or not source.is_dir():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
    shutil.copytree(source, staging)
    try:
        if not destination.exists():
            os.replace(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def rewrite_core_tex_archive(source: Path, destination: Path) -> None:
    ensure_output(source)
    temporary = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
    names: set[str] = set()
    with zipfile.ZipFile(source) as annotated, zipfile.ZipFile(
        temporary, "w", compression=zipfile.ZIP_DEFLATED
    ) as core:
        members = annotated.infolist()
        if not members:
            raise RuntimeError(f"empty TeX archive: {source}")
        for member in members:
            if not member.filename.startswith(SHADOW_TEX_PREFIX):
                raise RuntimeError(
                    f"unexpected TeX archive member prefix: {member.filename}"
                )
            core_name = CORE_TEX_PREFIX + member.filename[len(SHADOW_TEX_PREFIX) :]
            if core_name in names:
                raise RuntimeError(f"duplicate Core TeX archive member: {core_name}")
            names.add(core_name)
            data = annotated.read(member)
            if member.filename.endswith(".tex"):
                text = data.decode("utf-8")
                text = text.replace(SHADOW_TEX_PREFIX, CORE_TEX_PREFIX)
                data = text.encode("utf-8")
            core.writestr(core_name, data)
    os.replace(temporary, destination)

    with zipfile.ZipFile(destination) as archive:
        for member in archive.infolist():
            if not member.filename.startswith(CORE_TEX_PREFIX):
                raise RuntimeError(f"Core TeX archive contains an old name: {member.filename}")
            if member.filename.endswith(".tex"):
                text = archive.read(member).decode("utf-8")
                if SHADOW_TEX_PREFIX in text:
                    raise RuntimeError(
                        f"Core TeX archive contains an old internal prefix: {member.filename}"
                    )


def build_tex(shadow: Path, myst: Path, compile_pdf: bool) -> None:
    annotated_before = {
        ANNOTATED_PDF: file_hash(ANNOTATED_PDF),
        ANNOTATED_TEX: file_hash(ANNOTATED_TEX),
    }
    run([myst, "build", "--tex", "--strict"], shadow)
    latex_command = [sys.executable, "scripts/build_latex.py"]
    if not compile_pdf:
        latex_command.append("--tex-only")
    run(latex_command, shadow)

    rewrite_core_tex_archive(shadow / SHADOW_TEX, shadow / SHADOW_CORE_TEX)
    publish_file(shadow / SHADOW_CORE_TEX, CORE_TEX)
    if compile_pdf:
        publish_file(shadow / SHADOW_PDF, CORE_PDF)

    annotated_after = {
        ANNOTATED_PDF: file_hash(ANNOTATED_PDF),
        ANNOTATED_TEX: file_hash(ANNOTATED_TEX),
    }
    if annotated_after != annotated_before:
        raise RuntimeError("Core build changed an Annotated artifact")


def build_site(shadow: Path, myst: Path, publish: bool) -> None:
    run([myst, "build", "--site", "--strict", "--ci"], shadow)
    preserve_template_cache(shadow)
    if publish:
        publish_directory(shadow / "_build" / "site", CORE_SITE)


def build_html(shadow: Path, myst: Path, publish: bool) -> None:
    run([myst, "build", "--html", "--strict"], shadow)
    if publish:
        publish_directory(shadow / "_build" / "html", CORE_HTML)


def main() -> None:
    parser = ArgumentParser(
        description="Build the optional Core profile from a temporary shadow project."
    )
    parser.add_argument("profile", choices=("annotated", CORE_PROFILE))
    parser.add_argument(
        "action", choices=("check", "site", "html", "tex", "pdf", "all", "start")
    )
    parser.add_argument("--keep-workdir", action="store_true")
    args = parser.parse_args()

    if args.profile == "annotated" and args.action != "check":
        parser.error("the Annotated shadow is only used by the self-contained check action")

    myst = resolve_myst()
    variant_root = ROOT / "_build" / "variants" / args.profile
    variant_root.mkdir(parents=True, exist_ok=True)
    shadow = Path(tempfile.mkdtemp(prefix="project-", dir=variant_root))
    include_exports = args.action in {"tex", "pdf", "all"}
    try:
        manifest = prepare_shadow(
            shadow, profile=args.profile, include_exports=include_exports
        )
        if args.action == "tex":
            build_tex(shadow, myst, compile_pdf=False)
        elif args.action == "pdf":
            build_tex(shadow, myst, compile_pdf=True)
        elif args.action == "site":
            build_site(shadow, myst, publish=True)
        elif args.action == "html":
            build_html(shadow, myst, publish=True)
        elif args.action == "check":
            build_site(shadow, myst, publish=False)
        elif args.action == "all":
            build_tex(shadow, myst, compile_pdf=True)
            if manifest is None:
                raise ProfileError("Core manifest unavailable during all-profile build")
            write_core_config(shadow / "myst.yml", manifest, include_exports=False)
            build_site(shadow, myst, publish=True)
            build_html(shadow, myst, publish=True)
        elif args.action == "start":
            print(f"Core preview source: {shadow}", flush=True)
            run([myst, "start"], shadow)
    finally:
        if args.keep_workdir:
            print(f"Kept shadow project: {shadow}", flush=True)
        elif shadow.exists():
            assert_under(shadow, variant_root)
            shutil.rmtree(shadow)


if __name__ == "__main__":
    main()
