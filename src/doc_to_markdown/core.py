"""Conversion core."""

from __future__ import annotations

import io
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

Code = Literal["unsupported", "corrupt", "too_large", "too_deep", "unsafe_xml"]


class ConversionError(Exception):
    """Base error with a stable machine-readable ``code``."""

    def __init__(self, code: Code, message: str) -> None:
        super().__init__(message[:200])
        self.code: Code = code


DROP = {"script", "style", "noscript", "template", "iframe", "object", "nav"}
VOID = {"br", "img", "hr", "meta", "link", "input", "area", "base", "col", "source", "wbr"}
BLOCK = {"p", "div", "section", "article", "main", "header", "footer", "blockquote", "body"}
BAD_SCHEMES = ("javascript:", "vbscript:", "data:")
_CTRL = re.compile(r"[\x00-\x20\x7f]")


def _clean_url(raw: str, base: str | None) -> str | None:
    url = _CTRL.sub("", raw)
    if not url:
        return None
    low = url.lower()
    if low.startswith(BAD_SCHEMES):
        return None
    m = re.match(r"^([a-z][a-z0-9+.-]*):", low)
    if m and m.group(1) not in ("http", "https", "mailto"):
        return None
    raw_url = raw.strip()
    if base and not m:
        raw_url = urljoin(base, raw_url)
    raw_url = _CTRL.sub(lambda x: "%20" if x.group() == " " else "", raw_url)
    return raw_url.replace("(", "%28").replace(")", "%29")


def _url(raw: str, base: str | None) -> str | None:
    stripped = raw.strip()
    chk = _clean_url(stripped, base)
    if chk is None:
        return None
    if base and not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", _CTRL.sub("", stripped)):
        stripped = urljoin(base, stripped)
    return stripped.replace(" ", "%20").replace("(", "%28").replace(")", "%29")


def _esc(text: str) -> str:
    text = text.replace("<", "&lt;")
    for ch in "\\*_`[]":
        text = text.replace(ch, "\\" + ch)
    return re.sub(r"^(\d+)\.(\s)", r"\1\\.\2", text)


class _Node:
    def __init__(self, tag: str, attrs: dict[str, str], parent: _Node | None) -> None:
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.kids: list[_Node | str] = []


class _Builder(HTMLParser):
    def __init__(self, max_depth: int) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("#root", {}, None)
        self.cur = self.root
        self.depth = 0
        self.max_depth = max_depth

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(tag, {k: v or "" for k, v in attrs}, self.cur)
        self.cur.kids.append(node)
        if tag in VOID:
            return
        self.depth += 1
        if self.depth > self.max_depth:
            raise ConversionError("too_deep", "nesting too deep")
        self.cur = node

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.cur.kids.append(_Node(tag, {k: v or "" for k, v in attrs}, self.cur))

    def handle_endtag(self, tag: str) -> None:
        n: _Node | None = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is None or n.parent is None:
            return
        while self.cur is not n:
            self.depth -= 1
            parent = self.cur.parent
            if parent is None:
                break
            self.cur = parent
        self.depth -= 1
        self.cur = n.parent

    def handle_data(self, data: str) -> None:
        self.cur.kids.append(data)


def _hidden(n: _Node) -> bool:
    a = n.attrs
    style = a.get("style", "").replace(" ", "").lower()
    return (
        n.tag in DROP
        or "hidden" in a
        or a.get("aria-hidden", "").lower() == "true"
        or "display:none" in style
    )


def _in_section(n: _Node) -> bool:
    p = n.parent
    while p is not None:
        if p.tag in ("article", "main", "section"):
            return True
        p = p.parent
    return False


class _Renderer:
    def __init__(self, base: str | None, images: bool) -> None:
        self.base = base
        self.images = images

    def inline(self, n: _Node | str) -> str:
        if isinstance(n, str):
            return _esc(re.sub(r"\s+", " ", n))
        if _hidden(n) or (n.tag in ("header", "footer") and not _in_section(n)):
            return ""
        t = n.tag
        inner = "".join(self.inline(k) for k in n.kids)
        if t in ("em", "i"):
            return f"*{inner}*" if inner.strip() else inner
        if t in ("strong", "b"):
            return f"**{inner}**" if inner.strip() else inner
        if t == "code":
            return "`" + self.text(n).replace("`", "'") + "`"
        if t == "br":
            return " "
        if t == "a":
            u = _url(n.attrs.get("href", ""), self.base)
            return inner if u is None else f"[{inner}]({u})"
        if t == "img":
            u = _url(n.attrs.get("src", ""), self.base) if self.images else None
            return "" if u is None else f"![{_esc(n.attrs.get('alt', ''))}]({u})"
        return inner

    def text(self, n: _Node | str) -> str:
        if isinstance(n, str):
            return n
        return "".join(self.text(k) for k in n.kids)

    def blocks(self, n: _Node, indent: int = 0) -> list[str]:
        out: list[str] = []
        buf = ""

        def flush() -> None:
            nonlocal buf
            if buf.strip():
                out.append(buf.strip())
            buf = ""

        for k in n.kids:
            if isinstance(k, str) or k.tag not in _BLOCKY:
                buf += self.inline(k)
                continue
            if _hidden(k) or (k.tag in ("header", "footer") and not _in_section(k)):
                continue
            flush()
            out.extend(self.block(k, indent))
        flush()
        return out

    def block(self, k: _Node, indent: int) -> list[str]:
        t = k.tag
        if len(t) == 2 and t[0] == "h" and t[1] in "123456":
            s = "".join(self.inline(x) for x in k.kids).strip()
            return ["#" * int(t[1]) + " " + s] if s else []
        if t == "pre":
            cls = ""
            for x in k.kids:
                if isinstance(x, _Node) and x.tag == "code":
                    cls = x.attrs.get("class", "")
            m = re.search(r"language-([\w+-]+)", cls)
            body = self.text(k).strip("\n")
            return [f"```{m.group(1) if m else ''}\n{body}\n```"]
        if t in ("ul", "ol"):
            return ["\n".join(self.items(k, 0))]
        if t == "table":
            return self.table(k)
        if t == "hr":
            return ["---"]
        if t == "blockquote":
            return ["\n".join("> " + ln for b in self.blocks(k) for ln in b.split("\n"))]
        return self.blocks(k, indent)

    def items(self, lst: _Node, level: int) -> list[str]:
        lines: list[str] = []
        num = 0
        for li in lst.kids:
            if not isinstance(li, _Node) or li.tag != "li" or _hidden(li):
                continue
            num += 1
            mark = "1." if lst.tag == "ol" else "-"
            head = ""
            subs: list[str] = []
            for c in li.kids:
                if isinstance(c, _Node) and c.tag in ("ul", "ol"):
                    subs.extend(self.items(c, level + 1))
                else:
                    head += self.inline(c)
            lines.append("  " * level + f"{mark} {head.strip()}".rstrip())
            lines.extend(subs)
        return lines

    def table(self, t: _Node) -> list[str]:
        rows: list[list[str]] = []

        def walk(n: _Node) -> None:
            for c in n.kids:
                if isinstance(c, _Node):
                    if c.tag == "tr":
                        rows.append(
                            [
                                " ".join(
                                    "".join(self.inline(x) for x in d.kids)
                                    .replace("|", "\\|")
                                    .split()
                                )
                                for d in c.kids
                                if isinstance(d, _Node) and d.tag in ("td", "th")
                            ]
                        )
                    else:
                        walk(c)

        walk(t)
        return [_pipe(rows)] if rows else []


def _pipe(rows: list[list[str]]) -> str:
    w = max(len(r) for r in rows) or 1
    rows = [r + [""] * (w - len(r)) for r in rows]
    lines = ["| " + " | ".join(r) + " |" for r in rows]
    lines.insert(1, "| " + " | ".join(["---"] * w) + " |")
    return "\n".join(lines)


_BLOCKY = BLOCK | {"h1", "h2", "h3", "h4", "h5", "h6", "pre", "ul", "ol", "table", "hr", "li"}


def html_to_markdown(
    html: str,
    *,
    base_url: str | None = None,
    keep_images: bool = True,
    max_chars: int = 5_000_000,
    max_depth: int = 256,
) -> str:
    """Convert HTML text to Markdown."""
    if len(html) > max_chars:
        raise ConversionError("too_large", "html exceeds max_chars")
    b = _Builder(max_depth)
    b.feed(html)
    b.close()
    blocks = _Renderer(base_url, keep_images).blocks(b.root)
    return "\n\n".join(blocks) + "\n" if blocks else ""


_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_PR = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def _read_all(zf: zipfile.ZipFile, max_bytes: int, max_members: int) -> dict[str, bytes]:
    infos = zf.infolist()
    if len(infos) > max_members:
        raise ConversionError("too_large", "too many members")
    total = 0
    parts: dict[str, bytes] = {}
    for info in infos:
        if info.filename not in (
            "word/document.xml",
            "word/styles.xml",
            "word/_rels/document.xml.rels",
        ):
            continue
        buf = bytearray()
        with zf.open(info) as f:
            while chunk := f.read(65536):
                total += len(chunk)
                if total > max_bytes:
                    raise ConversionError("too_large", "decompressed size exceeds max_bytes")
                buf += chunk
        parts[info.filename] = bytes(buf)
    return parts


def _parse(data: bytes) -> ET.Element:
    head = data.upper()
    wide = data.decode("utf-16", "ignore").upper()
    if b"<!DOCTYPE" in head or b"<!ENTITY" in head or "<!DOCTYPE" in wide or "<!ENTITY" in wide:
        raise ConversionError("unsafe_xml", "DOCTYPE or ENTITY not allowed")
    try:
        return ET.fromstring(data)  # noqa: S314
    except ET.ParseError as e:
        raise ConversionError("corrupt", "invalid XML") from e


def docx_to_markdown(
    source: Path | bytes, *, max_bytes: int = 50_000_000, max_members: int = 1000
) -> str:
    """Convert a DOCX file or its bytes to Markdown."""
    data = source.read_bytes() if isinstance(source, Path) else source
    if len(data) > max_bytes:
        raise ConversionError("too_large", "file exceeds max_bytes")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            parts = _read_all(zf, max_bytes, max_members)
    except zipfile.BadZipFile as e:
        raise ConversionError("corrupt", "not a zip file") from e
    if "word/document.xml" not in parts:
        raise ConversionError("corrupt", "missing word/document.xml")
    doc = _parse(parts["word/document.xml"])
    styles: dict[str, str] = {}
    if "word/styles.xml" in parts:
        for s in _parse(parts["word/styles.xml"]).iter(_W + "style"):
            nm = s.find(_W + "name")
            if nm is not None:
                styles[s.get(_W + "styleId", "")] = nm.get(_W + "val", "").lower()
    rels: dict[str, str] = {}
    if "word/_rels/document.xml.rels" in parts:
        for r in _parse(parts["word/_rels/document.xml.rels"]).iter(_PR + "Relationship"):
            if r.get("TargetMode") == "External":
                rels[r.get("Id", "")] = r.get("Target", "")
    body = doc.find(_W + "body")
    if body is None:
        raise ConversionError("corrupt", "missing body")
    blocks: list[str] = []
    for el in body:
        if el.tag == _W + "p":
            para = _para(el, styles, rels)
            if para:
                blocks.append(para)
        elif el.tag == _W + "tbl":
            rows = []
            for tr in el.iter(_W + "tr"):
                row: list[str] = []
                for tc in tr.findall(_W + "tc"):
                    txt = " ".join(_runs(p, rels) for p in tc.iter(_W + "p")).replace("|", "\\|")
                    row.append(" ".join(txt.split()))
                    gs = tc.find(f"{_W}tcPr/{_W}gridSpan")
                    if gs is not None:
                        row.extend([""] * (int(gs.get(_W + "val", "1")) - 1))
                rows.append(row)
            if rows:
                blocks.append(_pipe(rows))
    # merge consecutive list items
    out: list[str] = []
    for b in blocks:
        if out and _is_item(b) and _is_item(out[-1]):
            out[-1] += "\n" + b
        else:
            out.append(b)
    return "\n\n".join(out) + "\n" if out else ""


def _is_item(b: str) -> bool:
    return b.lstrip(" ").startswith("- ") and "\n\n" not in b


def _runs(p: ET.Element, rels: dict[str, str]) -> str:
    out = ""
    for ch in p:
        if ch.tag == _W + "r":
            out += _esc("".join(t.text or "" for t in ch.iter(_W + "t")))
        elif ch.tag == _W + "hyperlink":
            txt = _esc("".join(t.text or "" for t in ch.iter(_W + "t")))
            u = _url(rels.get(ch.get(_R + "id", ""), ""), None)
            out += f"[{txt}]({u})" if u else txt
    return out


def _para(p: ET.Element, styles: dict[str, str], rels: dict[str, str]) -> str:
    text = _runs(p, rels).strip()
    if not text:
        return ""
    ps = p.find(f"{_W}pPr/{_W}pStyle")
    name = styles.get(ps.get(_W + "val", ""), "") if ps is not None else ""
    m = re.fullmatch(r"heading ([1-6])", name)
    if m:
        return "#" * int(m.group(1)) + " " + text
    num = p.find(f"{_W}pPr/{_W}numPr")
    if num is not None:
        lv = num.find(_W + "ilvl")
        level = int(lv.get(_W + "val", "0")) if lv is not None else 0
        return "  " * level + "- " + text
    return text


def convert(path: Path) -> str:
    """Convert a file, dispatching on its extension."""
    ext = path.suffix.lower()
    if ext in (".html", ".htm"):
        return html_to_markdown(path.read_text(encoding="utf-8", errors="replace"))
    if ext == ".docx":
        return docx_to_markdown(path)
    raise ConversionError("unsupported", f"unsupported extension: {ext[:50]}")
