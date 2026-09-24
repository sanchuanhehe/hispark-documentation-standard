"""Assemble immutable Release artifacts plus a freshly validated dev site."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile

from build_pages import audit_site, validate_base_url
from build_profile import ROOT, publish_directory
from release import version_key, verify_site


def gh_json(*args: str):
    return json.loads(subprocess.check_output(["gh", *args], text=True))


def extract_bundle(archive: Path, destination: Path) -> None:
    """Reject links, traversal, duplicates and excessive expansion before writing."""
    with tarfile.open(archive, "r:gz") as tar:
        members = tar.getmembers()
        names = set()
        if len(members) > 50000 or sum(m.size for m in members) > 1024 ** 3:
            raise ValueError("release archive exceeds size limit")
        for member in members:
            p = PurePosixPath(member.name)
            if (p.is_absolute() or ".." in p.parts or "\\" in member.name
                    or not p.parts or p.parts[0] not in {"root", "version"}
                    or p.as_posix() != member.name.rstrip("/")
                    or member.name in names or not (member.isfile() or member.isdir())):
                raise ValueError(f"unsafe archive member: {member.name}")
            names.add(member.name)
        for member in members:
            target = destination / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)


def merge_sites(dev: Path, releases: list[tuple[str, Path, str]], output: Path, base_url: str) -> None:
    """Validate every incoming tree; a failed or missing release blocks deployment."""
    dev_manifest = json.loads((dev / "build-manifest.json").read_text())
    dev_files = audit_site(dev, base_url + "/dev")
    dev_files.pop("build-manifest.json")
    if (dev_manifest["channel"] != "dev" or dev_manifest["base_url"] != base_url + "/dev"
            or dev_files != dev_manifest["files"]):
        raise ValueError("dev artifact identity/coverage mismatch")
    ordered = sorted(releases, key=lambda item: version_key(item[0]), reverse=True)
    if len({tag for tag, _, _ in ordered}) != len(ordered):
        raise ValueError("duplicate release version")
    for tag, tree, commit in ordered:
        stable = verify_site(tree / "root", tag, base_url, commit)
        fixed = verify_site(tree / "version", tag, f"{base_url}/{tag}", commit)
        if stable["markdown_sources"] != fixed["markdown_sources"]:
            raise ValueError("release content identity mismatch")
        for reserved in ("dev", "versions", "versions.json", "deployment-manifest.json"):
            if (tree / "root" / reserved).exists():
                raise ValueError("release occupies a deployment-reserved path")
        if any((tree / "root" / version).exists() for version, _, _ in ordered):
            raise ValueError("release occupies a version path")
    output.mkdir(parents=True, exist_ok=False)
    if ordered:
        shutil.copytree(ordered[0][1] / "root", output, dirs_exist_ok=True)
    else:
        # Bootstrap only: no stable release exists yet. Never label dev as stable.
        (output / "index.html").write_text(
            f'<!doctype html><meta charset="utf-8"><title>HiSpark</title>'
            f'<p>尚无正式发布。<a href="{base_url}/dev/">阅读开发版</a></p>')
    shutil.copytree(dev, output / "dev")
    records = []
    for tag, tree, commit in ordered:
        shutil.copytree(tree / "version", output / tag)
        records.append({"tag": tag, "commit": commit, "path": f"{base_url}/{tag}/"})
    (output / "versions.json").write_text(json.dumps({
        "latest": ordered[0][0] if ordered else None,
        "dev_commit": dev_manifest["commit"], "releases": records,
    }, ensure_ascii=False, indent=2) + "\n")
    (output / "versions").mkdir()
    entries = "".join(f'<li><a href="{item["path"]}">{item["tag"]}</a> · <code>{item["commit"]}</code></li>'
                      for item in records)
    (output / "versions/index.html").write_text(
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>HiSpark 文档版本</title>'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<body style="max-width:60em;margin:3em auto;padding:1em;font:16px/1.7 Arial,sans-serif">'
        f'<h1>HiSpark 文档版本</h1><p><a href="{base_url}/">最新稳定版</a> · '
        f'<a href="{base_url}/dev/">开发版</a>（非正式发布）</p><ul>{entries}</ul></body></html>', encoding="utf-8")
    for route in ["", "dev", "versions", *(item["tag"] for item in records)]:
        if not (output / route / "index.html").is_file():
            raise ValueError(f"version navigation target missing: {route}")
    (output / ".nojekyll").touch()
    files = audit_site(output, base_url)
    (output / "deployment-manifest.json").write_text(json.dumps({
        "schema_version": 1, "dev_commit": dev_manifest["commit"],
        "releases": records, "files": files,
    }, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--dev", type=Path, default=ROOT / "_build/pages-dev")
    args = parser.parse_args()
    base_url = validate_base_url(args.base_url)
    pages = gh_json("api", f"repos/{args.repo}/releases", "--paginate", "--slurp")
    releases = [r for page in pages for r in page if not r["draft"] and not r["prerelease"]]
    with tempfile.TemporaryDirectory(prefix="hispark-versions-") as directory:
        temporary = Path(directory)
        trees = []
        for release in releases:
            tag = release["tag_name"]
            version_key(tag)
            print(f"Restoring verified release {tag}", flush=True)
            archive_name = f"site-{tag}.tar.gz"
            assets = {asset["name"]: asset for asset in release["assets"]}
            if archive_name not in assets or "SHA256SUMS" not in assets:
                raise ValueError(f"published release {tag} has missing artifacts")
            download = temporary / tag
            download.mkdir()
            subprocess.run(["gh", "release", "download", tag, "--repo", args.repo,
                            "--pattern", archive_name, "--pattern", "SHA256SUMS",
                            "--dir", str(download)], check=True)
            archive = download / archive_name
            lines = (download / "SHA256SUMS").read_text().splitlines()
            actual = hashlib.sha256(archive.read_bytes()).hexdigest()
            if lines.count(f"{actual}  {archive_name}") != 1:
                raise ValueError(f"release archive checksum mismatch: {tag}")
            digest = assets[archive_name].get("digest")
            if digest and digest != "sha256:" + actual:
                raise ValueError(f"GitHub asset digest mismatch: {tag}")
            tree = download / "extracted"
            extract_bundle(archive, tree)
            commit = gh_json("api", f"repos/{args.repo}/commits/{tag}")["sha"]
            trees.append((tag, tree, commit))
        assembled = temporary / "assembled"
        merge_sites(args.dev, trees, assembled, base_url)
        publish_directory(assembled, ROOT / "_build/pages")
        print(f"Assembled {len(trees)} immutable releases plus dev", flush=True)


if __name__ == "__main__":
    main()
