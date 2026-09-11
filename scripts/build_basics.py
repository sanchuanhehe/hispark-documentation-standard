"""Build a short reading extract from the canonical requirements, without a fork."""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import urlsplit

from build_profile import ROOT, publish_file, resolve_myst, run
from profile_transform import apply_manifest, load_manifest, read_documents


def reading_extract() -> str:
    documents = read_documents(ROOT)
    core, _ = apply_manifest(documents, load_manifest(ROOT, "core"))
    basics = core["docs/part-1-foundations/04-core-principles.md"]
    body = basics.split("---", 2)[2].strip()
    # An offline excerpt cannot resolve targets in omitted chapters. Keep the
    # human-readable chapter references instead of emitting broken PDF links.
    body = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: match.group(0) if urlsplit(match.group(2)).scheme else match.group(1),
        body,
    )
    language = documents["docs/part-1-foundations/02-normative-language.md"]
    bcp = language.split("## 2.1 BCP 14 关键词\n", 1)[1].split("## 2.2 ", 1)[0].strip()
    return (
        "---\ntitle: '基础规范：十项共同要求'\n---\n\n"
        "V1.2 结构整改试行稿 · 2026-09-10\n\n"
        "这是完整规范第 4 章的阅读摘编，省略解释块，并附上第 2.1 节的关键词定义。"
        "正文中的章号指向完整规范；专项条款仍按场景适用。"
        "本摘编不构成独立符合性等级，也不替代完整规范或既有 Core 版本。\n\n"
        + bcp + "\n\n" + body + "\n"
    )


def main() -> None:
    myst = resolve_myst()
    destination = ROOT / "_build" / "variants" / "basics"
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="project-", dir=destination) as directory:
        shadow = Path(directory)
        (shadow / "docs").mkdir()
        (shadow / "docs" / "basics.md").write_text(reading_extract(), encoding="utf-8")
        shutil.copytree(ROOT / "latex", shadow / "latex")
        (shadow / "scripts").mkdir()
        for name in ('build_latex.py', 'pdf_links.py', 'profile_transform.py', 'validate_pdf_links.py'):
            shutil.copy2(ROOT / 'scripts' / name, shadow / 'scripts')
        config = """version: 1
project:
  title: HiSpark 文档规范
  authors:
    - name: HiSpark 文档规范维护者
  settings:
    myst_to_tex:
      code_style: listings
  exclude:
    - latex/**
    - scripts/**
    - exports/**
  toc:
    - file: docs/basics.md
  exports:
    - format: tex
      template: ./latex/plain_latex_book_zh
      output: exports/hispark-documentation-basics-tex.zip
      title: HiSpark 文档规范
      subtitle: 基础阅读摘编 · 十项共同要求
      articles:
        - file: docs/basics.md
          level: 0
"""
        (shadow / "myst.yml").write_text(config, encoding="utf-8")
        run([myst, "build", "--tex", "--strict"], shadow)
        run([sys.executable, "scripts/build_latex.py", "--edition", "basics"], shadow)
        for name in ("hispark-documentation-basics.pdf", "hispark-documentation-basics-tex.zip", "hispark-documentation-basics.links.json"):
            publish_file(shadow / "exports" / name, ROOT / "exports" / name)


if __name__ == "__main__":
    main()
