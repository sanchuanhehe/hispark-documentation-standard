from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any


class ProfileError(RuntimeError):
    """Raised when a profile selector is ambiguous or no longer matches."""


@dataclass(frozen=True)
class TransformSummary:
    profile: str
    selector_count: int
    changed_files: tuple[str, ...]


def load_manifest(root: Path, profile: str) -> dict[str, Any]:
    path = root / "profiles" / f"{profile}.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ProfileError(f"profile manifest not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ProfileError(f"invalid profile manifest {path}: {error}") from error

    if manifest.get("version") != 1:
        raise ProfileError(f"unsupported profile manifest version: {manifest.get('version')!r}")
    if manifest.get("profile") != profile:
        raise ProfileError(
            f"profile name mismatch: requested={profile!r}, manifest={manifest.get('profile')!r}"
        )
    selectors = manifest.get("selectors")
    if not isinstance(selectors, list) or not selectors:
        raise ProfileError("profile manifest must contain a non-empty selectors list")

    identities: set[str] = set()
    for index, selector in enumerate(selectors, start=1):
        _validate_selector(selector, index)
        identity = json.dumps(selector, ensure_ascii=False, sort_keys=True)
        if identity in identities:
            raise ProfileError(f"duplicate selector at index {index}: {selector}")
        identities.add(identity)

    frontmatter_titles = manifest.get("frontmatter_titles", {})
    if not isinstance(frontmatter_titles, dict):
        raise ProfileError("frontmatter_titles must be an object")
    for raw_path, title in frontmatter_titles.items():
        path = PurePosixPath(raw_path)
        if path.is_absolute() or ".." in path.parts or path.parts[:1] != ("docs",):
            raise ProfileError(f"frontmatter title path must stay under docs/: {raw_path!r}")
        if path.suffix != ".md":
            raise ProfileError(f"frontmatter title must target Markdown: {raw_path!r}")
        if not isinstance(title, str) or not title or "\n" in title or "\r" in title:
            raise ProfileError(f"invalid frontmatter title for {raw_path!r}")
    return manifest


def _validate_selector(selector: Any, index: int) -> None:
    if not isinstance(selector, dict):
        raise ProfileError(f"selector {index} must be an object")
    kind = selector.get("kind")
    if kind not in {"section", "admonition", "line"}:
        raise ProfileError(f"selector {index} has unsupported kind: {kind!r}")

    raw_path = selector.get("path")
    if not isinstance(raw_path, str):
        raise ProfileError(f"selector {index} must provide a string path")
    path = PurePosixPath(raw_path)
    if path.is_absolute() or ".." in path.parts or path.parts[:1] != ("docs",):
        raise ProfileError(f"selector {index} path must stay under docs/: {raw_path!r}")
    if path.suffix != ".md":
        raise ProfileError(f"selector {index} must target a Markdown file: {raw_path!r}")

    field = {"section": "heading", "admonition": "title", "line": "text"}[kind]
    value = selector.get(field)
    if not isinstance(value, str) or not value or "\n" in value or "\r" in value:
        raise ProfileError(f"selector {index} must provide one exact {field} line")
    if kind == "section" and not re.fullmatch(r"#{1,6} .+", value):
        raise ProfileError(f"selector {index} has invalid section heading: {value!r}")


def apply_manifest(
    documents: dict[str, str], manifest: dict[str, Any]
) -> tuple[dict[str, str], TransformSummary]:
    transformed = deepcopy(documents)
    selectors_by_path: dict[str, list[dict[str, str]]] = defaultdict(list)
    for selector in manifest["selectors"]:
        selectors_by_path[selector["path"]].append(selector)

    unknown_paths = sorted(set(selectors_by_path) - set(documents))
    if unknown_paths:
        raise ProfileError(f"profile selectors target missing documents: {unknown_paths}")

    changed: set[str] = set()
    for path, selectors in selectors_by_path.items():
        text = transformed[path]
        for selector in selectors:
            text = apply_selector(text, selector, path)
        if text == documents[path]:
            raise ProfileError(f"profile selectors made no change to {path}")
        transformed[path] = text
        changed.add(path)

    for path, title in manifest.get("frontmatter_titles", {}).items():
        if path not in transformed:
            raise ProfileError(f"frontmatter title targets missing document: {path}")
        transformed[path] = _replace_frontmatter_title(transformed[path], title, path)
        changed.add(path)

    return transformed, TransformSummary(
        profile=manifest["profile"],
        selector_count=len(manifest["selectors"]),
        changed_files=tuple(sorted(changed)),
    )


def apply_selector(text: str, selector: dict[str, str], source: str) -> str:
    kind = selector["kind"]
    if kind == "line":
        return _remove_exact_line(text, selector["text"], source)
    if kind == "section":
        return _remove_section(text, selector["heading"], source)
    if kind == "admonition":
        return _remove_admonition(text, selector["title"], source)
    raise ProfileError(f"unsupported selector kind in {source}: {kind!r}")


def _matching_line_indices(lines: list[str], exact: str) -> list[int]:
    return [index for index, line in enumerate(lines) if line.rstrip("\r\n") == exact]


def _require_one_line(lines: list[str], exact: str, source: str) -> int:
    matches = _matching_line_indices(lines, exact)
    if len(matches) != 1:
        raise ProfileError(
            f"selector must match exactly once in {source}: {exact!r}; matches={len(matches)}"
        )
    return matches[0]


def _replace_frontmatter_title(text: str, title: str, source: str) -> str:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise ProfileError(f"missing frontmatter in {source}")
    try:
        end = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.rstrip("\r\n") == "---"
        )
    except StopIteration as error:
        raise ProfileError(f"unclosed frontmatter in {source}") from error
    matches = [
        index
        for index in range(1, end)
        if lines[index].rstrip("\r\n").startswith("title:")
    ]
    if len(matches) != 1:
        raise ProfileError(
            f"frontmatter title must occur exactly once in {source}; matches={len(matches)}"
        )
    index = matches[0]
    newline = "\r\n" if lines[index].endswith("\r\n") else "\n"
    replacement = f"title: {title}{newline}"
    if lines[index] == replacement:
        raise ProfileError(f"frontmatter title already has the profile value in {source}")
    lines[index] = replacement
    return "".join(lines)


def _next_fence_state(
    line: str, state: tuple[str, int] | None
) -> tuple[str, int] | None:
    content = line.rstrip("\r\n")
    if state is None:
        match = re.match(r"^[ ]{0,3}(`{3,}|~{3,})", content)
        if not match:
            return None
        token = match.group(1)
        return token[0], len(token)
    character, length = state
    if re.fullmatch(
        rf"[ ]{{0,3}}{re.escape(character)}{{{length},}}[ \t]*", content
    ):
        return None
    return state


def strip_fenced_code_blocks(text: str, source: str = "<text>") -> str:
    result: list[str] = []
    state: tuple[str, int] | None = None
    for line in text.splitlines(keepends=True):
        before = state
        state = _next_fence_state(line, state)
        if before is not None or state is not None:
            continue
        result.append(line)
    if state is not None:
        raise ProfileError(f"unclosed fenced code block in {source}")
    return "".join(result)


def _remove_exact_line(text: str, exact: str, source: str) -> str:
    lines = text.splitlines(keepends=True)
    index = _require_one_line(lines, exact, source)
    del lines[index]
    return "".join(lines)


def _remove_section(text: str, heading: str, source: str) -> str:
    lines = text.splitlines(keepends=True)
    start = _require_one_line(lines, heading, source)
    level = len(heading) - len(heading.lstrip("#"))
    heading_pattern = re.compile(rf"^#{{1,{level}}} ")
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if heading_pattern.match(lines[index].rstrip("\r\n")):
            end = index
            break
    del lines[start:end]
    return "".join(lines)


def _remove_admonition(text: str, title: str, source: str) -> str:
    lines = text.splitlines(keepends=True)
    opener = f":::{{admonition}} {title}"
    start = _require_one_line(lines, opener, source)
    depth = 0
    end: int | None = None
    fence_state: tuple[str, int] | None = None
    for index in range(start, len(lines)):
        stripped = lines[index].rstrip("\r\n")
        before_fence = fence_state
        fence_state = _next_fence_state(lines[index], fence_state)
        if before_fence is not None or fence_state is not None:
            continue
        if stripped.startswith(":::{"):
            depth += 1
        elif stripped == ":::" and depth:
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if end is None:
        raise ProfileError(f"unclosed admonition in {source}: {title!r}")
    del lines[start:end]
    return "".join(lines)


def read_documents(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted((root / "docs").rglob("*.md"))
    }


def write_documents(root: Path, documents: dict[str, str]) -> None:
    for relative, text in documents.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
