"""Single-version checks and release packaging; no inferred or generated changelog."""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SEMVER = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"


def version_key(tag: str) -> tuple[int, int, int]:
    if not re.fullmatch("v" + SEMVER, tag):
        raise ValueError(f"expected stable vMAJOR.MINOR.PATCH, got {tag!r}")
    return tuple(map(int, tag[1:].split(".")))


def release_metadata(root: Path = ROOT) -> tuple[str, str, str]:
    version = (root / "VERSION").read_text().strip()
    version_key("v" + version)
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if not changelog.startswith("# Changelog\n") or "## [Unreleased]\n" not in changelog:
        raise ValueError("Keep a Changelog header and Unreleased section required")
    headings = re.findall(r"^## \[([^]]+)\](.*)$", changelog, re.M)
    versions = [name for name, _ in headings if name != "Unreleased"]
    if len(versions) != len(set(versions)) or not versions or versions[0] != version:
        raise ValueError("VERSION must equal the latest unique changelog version")
    for name in versions:
        version_key("v" + name)
    match = re.search(r"^## \[" + re.escape(version) + r"\] - (\d{4}-\d{2}-\d{2})\n(.*?)(?=^## |^\[Unreleased\]:|\Z)",
                      changelog, re.M | re.S)
    if not match:
        raise ValueError("dated release notes missing")
    released, notes = match.groups()
    date.fromisoformat(released)
    if not re.search(r"^- .+", notes, re.M):
        raise ValueError("release notes must contain user-visible entries")
    sections = re.findall(r"^### (.+)$", notes, re.M)
    allowed = {"Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"}
    if not sections or len(sections) != len(set(sections)) or set(sections) - allowed:
        raise ValueError("invalid Keep a Changelog categories")
    for section in re.split(r"^### .+\n", notes, flags=re.M)[1:]:
        if not re.search(r"^- .+", section, re.M):
            raise ValueError("empty changelog category")
    if not re.search(r"^\[" + re.escape(version) + r"\]: https://", changelog, re.M):
        raise ValueError("release comparison/source link missing")
    return version, released, notes.strip() + "\n"


def check(root: Path = ROOT, tag: str | None = None) -> tuple[str, str, str]:
    version, released, notes = release_metadata(root)
    if tag is not None and tag != "v" + version:
        raise ValueError("tag and VERSION do not match")
    package = json.loads((root / "package.json").read_text())
    lock = json.loads((root / "package-lock.json").read_text())
    if any(value != version for value in (package["version"], lock["version"], lock["packages"][""]["version"])):
        raise ValueError("package versions drifted from VERSION")
    index = (root / "docs/index.md").read_text()
    if f"- 规范版本：v{version}\n" not in index or f"- 发布日期：{released}\n" not in index:
        raise ValueError("homepage release identity drifted")
    if f"  date: {released}\n" not in (root / "myst.yml").read_text():
        raise ValueError("document export date drifted")
    return version, released, notes


def verify_site(directory: Path, tag: str, base_url: str, commit: str | None = None) -> dict:
    from build_pages import audit_site
    manifest = json.loads((directory / "build-manifest.json").read_text())
    if (manifest["version"] != tag[1:] or manifest["channel"] != "release"
            or manifest["base_url"] != base_url or manifest["profile"] != "annotated"
            or not re.fullmatch(r"[0-9a-f]{40}", manifest["commit"])
            or (commit is not None and manifest["commit"] != commit)):
        raise ValueError("site release identity mismatch")
    actual = audit_site(directory, base_url)
    actual.pop("build-manifest.json")
    if actual != manifest["files"]:
        raise ValueError("site file hashes/coverage mismatch")
    return manifest


def bundle(root: Path, versioned: Path, output: Path, tag: str, base_url: str) -> None:
    version_key(tag)
    current = verify_site(root, tag, base_url)
    fixed = verify_site(versioned, tag, f"{base_url}/{tag}", current["commit"])
    if current["markdown_sources"] != fixed["markdown_sources"]:
        raise ValueError("stable and fixed-version content differs")
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"site-{tag}.tar.gz"
    if archive.exists():
        raise ValueError("refusing to overwrite an existing release bundle")
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(root, arcname="root")
        tar.add(versioned, arcname="version")
    skills = output / f"skills-{tag}.zip"
    with zipfile.ZipFile(skills, "x", compression=zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted((ROOT / ".agents/skills").rglob("*")):
            if path.is_symlink():
                raise ValueError("skill symlink is not publishable")
            if path.is_file():
                zipped.write(path, path.relative_to(ROOT / ".agents/skills"))
    sums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in (archive, skills))
    (output / "SHA256SUMS").write_text(sums)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "notes", "bundle"))
    parser.add_argument("--tag")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--versioned", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--base-url")
    args = parser.parse_args()
    version, released, notes = check(tag=args.tag)
    if args.action == "notes":
        if not args.output:
            parser.error("notes requires --output")
        args.output.write_text(f"## {version} - {released}\n\n{notes}", encoding="utf-8")
    elif args.action == "bundle":
        if not all((args.tag, args.root, args.versioned, args.output, args.base_url)):
            parser.error("bundle requires tag, root, versioned, output and base-url")
        bundle(args.root, args.versioned, args.output, args.tag, args.base_url)
    else:
        print(f"Version, changelog, package metadata and document identity agree: v{version}")


if __name__ == "__main__":
    main()
