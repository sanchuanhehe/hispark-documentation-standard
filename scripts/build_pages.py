"""Build the Annotated HTML website without requiring local PDF fonts/artifacts."""
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
        files = audit_site(html, base_url)
        manifest = {
            "schema_version": 1,
            "commit": os.environ.get("GITHUB_SHA", "local-uncommitted"),
            "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
            "base_url": base_url,
            "profile": "annotated",
            "boundary": "HTML only; PDF production and font licensing are not validated here",
            "files": files,
        }
        (html / "build-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        publish_directory(html, output)
        print(f"Validated {len(files)} Pages files; output={output}", flush=True)


if __name__ == "__main__":
    main()
