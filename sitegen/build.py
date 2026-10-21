# -*- coding: utf-8 -*-
"""Build a static, GitHub Pages friendly site from the Obsidian vault.

Usage: python sitegen/build.py --vault . --out _site
"""
import argparse
import html
import os
import re
import shutil
from urllib.parse import quote

import markdown
from pygments.formatters import HtmlFormatter

SKIP_DIRS = {".obsidian", ".git", "_site", "sitegen", ".github", "90-模板", "99-附件"}
SKIP_FILES = {"_meta_链接索引.md"}

CALLOUT_RE = re.compile(r"^>\s*\[!(\w+)\]([+-])?\s*(.*)$")
FM_RE = re.compile(r"^---\n(.*?)\n---\n?", re.S)
WIKI_RE = re.compile(r"\[\[([^\]\|#]+)(?:#([^\]\|]+))?(?:\|([^\]]+))?\]\]")

CALLOUT_ZH = {
    "note": "说明", "tip": "提示", "warning": "注意", "danger": "危险",
    "important": "重要", "abstract": "摘要", "info": "信息", "success": "完成",
    "question": "问题", "quote": "引用", "example": "示例", "bug": "缺陷",
}


def parse_front(text):
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"^([^\s:][^:]*):\s*(.*)$", line)
        if mm:
            k, v = mm.group(1).strip(), mm.group(2).strip()
            fm[k] = v.strip('"').strip("'")
    return fm, text[m.end():]


class Site:
    def __init__(self, vault, out):
        self.vault = os.path.abspath(vault)
        self.out = os.path.abspath(out)
        self.pages = []
        self.by_stem, self.by_base, self.by_alias = {}, {}, {}
        self.titles = {}

    @staticmethod
    def make_md():
        return markdown.Markdown(extensions=[
            "extra", "toc", "sane_lists", "codehilite",
        ], extension_configs={
            "codehilite": {"guess_lang": False, "noclasses": False, "css_class": "codehilite"},
        })

    # ---------- scan ----------
    def scan(self):
        for root, dirs, files in os.walk(self.vault):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for f in sorted(files):
                if not f.endswith(".md") or f in SKIP_FILES:
                    continue
                path = os.path.join(root, f)
                stem = os.path.relpath(path, self.vault).replace("\\", "/")[:-3]
                fm, body = parse_front(open(path, encoding="utf-8-sig").read())
                self.pages.append((stem, body, fm))
                self.by_stem[stem] = stem
                self.by_base.setdefault(stem.split("/")[-1], stem)
                self.titles[stem] = fm.get("title") or stem.split("/")[-1]
                for a in self._aliases(fm):
                    self.by_alias.setdefault(a, stem)
        self.pages.sort(key=lambda p: p[0])

    @staticmethod
    def _aliases(fm):
        raw = (fm.get("aliases") or "").strip()
        if not raw:
            return []
        if raw.startswith("["):
            return [x.strip().strip('"').strip("'") for x in raw.strip("[]").split(",") if x.strip()]
        return []

    def out_rel(self, stem):
        if stem == "00-开始这里/首页":
            return "index.html"
        return stem + ".html"

    def resolve(self, target):
        target = target.strip()
        return self.by_stem.get(target) or self.by_alias.get(target) or self.by_base.get(target)

    # ---------- markdown ----------
    def convert_callouts(self, text):
        lines = text.split("\n")
        out, i = [], 0
        while i < len(lines):
            m = CALLOUT_RE.match(lines[i])
            if not m:
                out.append(lines[i])
                i += 1
                continue
            kind = m.group(1).lower()
            title = m.group(3).strip() or CALLOUT_ZH.get(kind, kind)
            inner = []
            i += 1
            while i < len(lines) and lines[i].startswith(">"):
                inner.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            body = self.convert_callouts("\n".join(inner))
            rendered = markdown.markdown(body, extensions=["extra", "sane_lists", "codehilite"],
                                         extension_configs={"codehilite": {"guess_lang": False}})
            out.append('<div class="callout %s"><div class="callout-title">%s</div>'
                       '<div class="callout-body">%s</div></div>' % (kind, html.escape(title), rendered))
        return "\n".join(out)

    def convert_wikilinks(self, text, prefix):
        def one(m):
            target, anchor, label = m.group(1).strip(), m.group(2), (m.group(3) or "").strip()
            stem = self.resolve(target)
            text_label = label or (self.titles.get(stem, target) if stem else target)
            if stem is None:
                return '<span class="broken-link" title="链接目标不在库中">%s</span>' % html.escape(text_label)
            href = prefix + quote(self.out_rel(stem))
            if anchor:
                href += "#" + quote(anchor.strip())
            return '<a href="%s">%s</a>' % (href, html.escape(text_label))

        parts = re.split(r"(```.*?```)", text, flags=re.S)
        out = []
        for p in parts:
            if p.startswith("```"):
                out.append(p)
                continue
            segs = re.split(r"(`[^`\n]*`)", p)
            out.append("".join(s if s.startswith("`") else WIKI_RE.sub(one, s) for s in segs))
        return "".join(out)

    # ---------- render ----------
    def nav_html(self, prefix):
        groups = {}
        for stem, _, fm in self.pages:
            title = fm.get("title") or stem.split("/")[-1]
            top = stem.split("/")[0] if "/" in stem else "关于"
            groups.setdefault(top, []).append((stem, title))
        parts = []
        for top in sorted(groups, key=lambda g: (g == "关于", g)):
            parts.append('<div class="nav-group"><div class="nav-group-title">%s</div><ul>' % html.escape(top))
            for stem, title in groups[top]:
                parts.append('<li><a href="%s%s">%s</a></li>'
                             % (prefix, quote(self.out_rel(stem)), html.escape(title)))
            parts.append("</ul></div>")
        return "\n".join(parts)

    def render(self, stem, body, fm):
        out_rel = self.out_rel(stem)
        depth = out_rel.count("/")
        prefix = "../" * depth
        title = fm.get("title") or stem.split("/")[-1]

        # 用正文首个 H1 作为页面标题，避免和模板标题重复
        lines = body.split("\n")
        for idx, line in enumerate(lines):
            if not line.strip():
                continue
            if line.lstrip().startswith("# "):
                title = line.lstrip()[2:].strip().replace("`", "")
                del lines[idx]
            break
        body = "\n".join(lines)

        page_title = title if title != "Rust 学习宝库" else "Rust 学习宝库 · 中文学习笔记"

        body = self.convert_callouts(body)
        body = self.convert_wikilinks(body, prefix)
        content = self.make_md().convert(body)

        tags = (fm.get("tags") or "").strip().strip("[]")
        chips = [t.strip() for t in re.split(r"[,，]", tags) if t.strip()]
        tag_html = "".join('<span class="tag">%s</span>' % html.escape(t) for t in chips)
        tag_html = '<div class="tags">%s</div>' % tag_html if tag_html else ""

        return """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title}</title>
<meta name="description" content="中文 Rust 学习笔记与 std 标准库参考">
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
<header class="topbar">
  <a class="brand" href="{prefix}index.html">🦀 Rust 学习宝库</a>
  <span class="tagline">中文学习笔记 · 标准库参考</span>
</header>
<div class="layout">
<nav class="sidebar">
  <input id="nav-filter" type="search" placeholder="筛选页面标题…" autocomplete="off">
  <div id="nav-list">{nav}</div>
</nav>
<main>
<article>
<h1>{title}</h1>
{tags}
{content}
</article>
<footer class="page-footer">
  <a href="https://github.com/yinghan21/rust-vault">GitHub 仓库</a> ·
  <a href="{prefix}index.html">返回首页</a> ·
  MIT License
</footer>
</main>
</div>
<script src="{prefix}assets/app.js"></script>
</body>
</html>
""".format(page_title=html.escape(page_title), prefix=prefix, nav=self.nav_html(prefix),
           title=html.escape(title), tags=tag_html, content=content)

    def build(self):
        self.scan()
        if os.path.exists(self.out):
            shutil.rmtree(self.out)
        os.makedirs(os.path.join(self.out, "assets"), exist_ok=True)

        for stem, body, fm in self.pages:
            target = os.path.join(self.out, self.out_rel(stem).replace("/", os.sep))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(self.render(stem, body, fm))

        here = os.path.dirname(os.path.abspath(__file__))
        style = open(os.path.join(here, "style.css"), encoding="utf-8").read()
        style += "\n" + HtmlFormatter(style="github-dark").get_style_defs(".codehilite")
        open(os.path.join(self.out, "assets", "style.css"), "w", encoding="utf-8").write(style)
        shutil.copy(os.path.join(here, "app.js"), os.path.join(self.out, "assets", "app.js"))

        attach = os.path.join(self.vault, "99-附件")
        if os.path.isdir(attach):
            dst = os.path.join(self.out, "99-附件")
            os.makedirs(dst, exist_ok=True)
            for name in os.listdir(attach):
                src = os.path.join(attach, name)
                if os.path.isfile(src):
                    shutil.copy(src, os.path.join(dst, name))
        open(os.path.join(self.out, ".nojekyll"), "w").write("")
        print("pages:", len(self.pages), "->", self.out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=".")
    ap.add_argument("--out", default="_site")
    a = ap.parse_args()
    Site(a.vault, a.out).build()


if __name__ == "__main__":
    main()
