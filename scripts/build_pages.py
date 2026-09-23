"""Build Annotated HTML and canonical Markdown without local PDF fonts/artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from build_profile import ROOT, prepare_shadow, publish_directory, resolve_myst, run


def validate_base_url(value: str) -> str:
    if not re.fullmatch(r"(?:/[A-Za-z0-9._-]+)*", value) or any(
        part in {".", ".."} for part in value.split("/")
    ):
        raise ValueError("BASE_URL must be empty or a repository path without a trailing slash")
    return value


def audit_site(directory: Path, base_url: str) -> dict:
    """Require a real export and record exactly the deployable file identities."""
    index = directory / "index.html"
    if not index.is_file() or index.stat().st_size == 0:
        raise ValueError("Pages index.html is missing or empty")
    html = index.read_text(encoding="utf-8")
    if "HiSpark" not in html:
        raise ValueError("Pages export does not contain the expected site")
    if base_url and base_url + "/" not in html:
        raise ValueError("Pages export does not use the repository base path")
    files = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Pages artifact cannot contain symbolic links: {path.name}")
        if not path.is_file():
            continue
        files[path.relative_to(directory).as_posix()] = {
            "size": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    return files


def publish_markdown(source_root: Path, directory: Path) -> list[dict]:
    """Expose only rendered docs, byte-for-byte, with route and source-path URLs."""
    expected = {p.relative_to(source_root).as_posix()
                for p in (source_root / "docs").rglob("*.md")}
    records, sources, destinations = [], set(), set()
    copies = []
    for metadata in sorted(directory.glob("*.json")):
        article = json.loads(metadata.read_text(encoding="utf-8"))
        if not isinstance(article, dict) or article.get("kind") != "Article":
            continue
        slug, location = article.get("slug"), article.get("location")
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError("invalid Markdown route slug")
        if (not isinstance(location, str) or not location.startswith("/docs/")
                or not location.endswith(".md") or "\\" in location
                or any(part in {"", ".", ".."} for part in location[1:].split("/"))):
            raise ValueError("Markdown source must be a canonical docs path")
        relative = location[1:]
        source = source_root / relative
        if (not source.is_file() or source.is_symlink()
                or not source.resolve().is_relative_to((source_root / "docs").resolve())):
            raise ValueError(f"missing or unsafe Markdown source: {relative}")
        html_path = directory / ("index.html" if slug == "index" else f"{slug}/index.html")
        if not html_path.is_file():
            raise ValueError(f"Markdown has no rendered page: {slug}")
        if relative in sources:
            raise ValueError(f"duplicate Markdown source: {relative}")
        sources.add(relative)
        data = source.read_bytes()
        paths = [f"{slug}.md", relative]
        for path in paths:
            target = directory / path
            if (path in destinations or target.exists() or target.is_symlink()
                    or any((directory / p).is_symlink() for p in Path(path).parents)):
                raise ValueError(f"Markdown destination collision: {path}")
            destinations.add(path)
            copies.append((target, data))
        records.append({"source": relative, "slug": slug, "paths": paths,
                        "sha256": hashlib.sha256(data).hexdigest()})
    if not expected or sources != expected:
        raise ValueError("rendered Markdown coverage does not match canonical docs")
    # Validate the whole mapping before writing anything.
    for target, data in copies:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("BASE_URL", ""))
    args = parser.parse_args()
    base_url = validate_base_url(args.base_url)
    os.environ["BASE_URL"] = base_url
    output = ROOT / "_build/pages"
    with tempfile.TemporaryDirectory(prefix="hispark-pages-") as temporary:
        shadow = Path(temporary)
        # Only export/download controls are removed. Canonical content and both
        # profile quality checks stay unchanged; no stale local PDFs are copied.
        prepare_shadow(shadow, "annotated", include_exports=False)
        run([resolve_myst(), "build", "--html", "--strict", "--check-links"], shadow)
        html = shadow / "_build/html"
        (html / ".nojekyll").touch()
        markdown_sources = publish_markdown(shadow, html)
        files = audit_site(html, base_url)
        manifest = {
            "schema_version": 1,
            "commit": os.environ.get("GITHUB_SHA", "local-uncommitted"),
            "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
            "base_url": base_url,
            "profile": "annotated",
            "boundary": "HTML and canonical Markdown; PDF production and font licensing are not validated here",
            "markdown_sources": markdown_sources,
            "files": files,
        }
        (html / "build-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        publish_directory(html, output)
        print(f"Validated {len(files)} Pages files; output={output}", flush=True)


if __name__ == "__main__":
    main()
