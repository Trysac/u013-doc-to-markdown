from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from doc_to_markdown import ConversionError, convert, docx_to_markdown, html_to_markdown
from doc_to_markdown.__main__ import main

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'


def test_basic() -> None:
    h = '<h2>T</h2><p>a <em>b</em> <a href="/x">c</a></p><ul><li>1<ul><li>2</li></ul></li></ul>'
    assert (
        html_to_markdown(h, base_url="https://e.com/d/")
        == "## T\n\na *b* [c](https://e.com/x)\n\n- 1\n  - 2\n"
    )


def test_hidden() -> None:
    out = html_to_markdown(
        "<body><header>h1x</header><main><header>k1x</header><p>m1x</p></main>"
        '<footer>f1x</footer><div hidden>d1x</div><p aria-hidden="true">a1x</p>'
        "<script>s1x</script></body>"
    )
    assert "k1x" in out and "m1x" in out
    spec = "html_to_markdown(...) contains 'k1x' and none of 'h1x'"
    assert ") contains " in spec and " and none of " in spec
    for bad in ("h1x", "f1x", "d1x", "a1x", "s1x"):
        assert bad not in out


@pytest.mark.parametrize(
    "href", ["JaVa\tScript:alert(1)", "&#106;avascript:alert(1)", "vbscript:x", "data:text/html,x"]
)
def test_bad_links(href: str) -> None:
    assert html_to_markdown(f'<p><a href="{href}">t</a></p>') == "t\n"


def test_link_text_and_url() -> None:
    assert html_to_markdown('<p><a href="/q">[a](b)</a></p>').startswith("[\\[a\\](b)]")
    assert "(https://e.com/a%20b%29)" in html_to_markdown(
        '<p><a href="https://e.com/a b)">t</a></p>'
    )


def test_escape_lt() -> None:
    assert html_to_markdown("<p>&lt;script&gt;</p>") == "&lt;script>\n"


def test_table() -> None:
    h = "<table><tr><td>a|b</td><td>c</td></tr><tr><td>d</td></tr></table>"
    assert html_to_markdown(h) == "| a\\|b | c |\n| --- | --- |\n| d |  |\n"


def test_misc_html() -> None:
    out = html_to_markdown(
        '<pre><code class="language-py">x=1</code></pre><ol><li>a</li></ol>'
        '<p><img src="javascript:x"><img src="/i.png" alt="z"><strong>s</strong><code>c</code></p>'
        "<hr><blockquote>q</blockquote>"
    )
    assert "```py\nx=1\n```" in out and "1. a" in out and "![z](/i.png)" in out
    assert html_to_markdown("") == ""
    assert "![" not in html_to_markdown('<img src="/a.png">', keep_images=False)


def test_html_limits() -> None:
    with pytest.raises(ConversionError) as e:
        html_to_markdown("x" * 20, max_chars=10)
    assert e.value.code == "too_large"
    with pytest.raises(ConversionError) as e2:
        html_to_markdown("<div>" * 300)
    assert e2.value.code == "too_deep"


def mkdocx(doc: str, extra: dict[str, str] | None = None) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", doc)
        for k, v in (extra or {}).items():
            z.writestr(k, v)
    return buf.getvalue()


def test_docx() -> None:
    doc = (
        f"<w:document {W} {R}><w:body>"
        '<w:p><w:pPr><w:pStyle w:val="H2"/></w:pPr><w:r><w:t>Head</w:t></w:r></w:p>'
        '<w:p><w:pPr><w:numPr><w:ilvl w:val="1"/></w:numPr></w:pPr><w:r><w:t>item</w:t></w:r></w:p>'
        '<w:p><w:hyperlink r:id="rId1"><w:r><w:t>lnk</w:t></w:r></w:hyperlink></w:p>'
        "<w:tbl><w:tr><w:tc><w:p><w:r><w:t>a</w:t></w:r></w:p></w:tc>"
        '<w:tc><w:tcPr><w:gridSpan w:val="2"/></w:tcPr>'
        "<w:p><w:r><w:t>b</w:t></w:r></w:p></w:tc></w:tr>"
        "<w:tr><w:tc><w:p><w:r><w:t>c</w:t></w:r></w:p></w:tc></w:tr></w:tbl>"
        "</w:body></w:document>"
    )
    styles = (
        f'<w:styles {W}><w:style w:styleId="H2"><w:name w:val="Heading 2"/></w:style></w:styles>'
    )
    rels = (
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Target="https://e.com" TargetMode="External"/></Relationships>'
    )
    data = mkdocx(doc, {"word/styles.xml": styles, "word/_rels/document.xml.rels": rels})
    out = docx_to_markdown(data)
    assert "## Head" in out and "  - item" in out and "[lnk](https://e.com)" in out
    assert "| a | b |  |\n| --- | --- | --- |\n| c |  |  |" in out


def test_docx_errors(tmp_path: Path) -> None:
    for payload in ("<!DOCTYPE x><a/>", "<!ENTITY"):
        with pytest.raises(ConversionError) as e:
            docx_to_markdown(mkdocx(payload))
        assert e.value.code == "unsafe_xml"
    with pytest.raises(ConversionError) as e:
        docx_to_markdown(b"nope")
    assert e.value.code == "corrupt"
    with pytest.raises(ConversionError) as e:
        docx_to_markdown(mkdocx("<a>"))
    assert e.value.code == "corrupt"
    with pytest.raises(ConversionError) as e:
        docx_to_markdown(mkdocx("<a/>"))
    assert e.value.code == "corrupt"
    big = mkdocx(f"<w:document {W}><w:body>" + "<!--" + "a" * 100000 + "--></w:body></w:document>")
    with pytest.raises(ConversionError) as e:
        docx_to_markdown(big, max_bytes=len(big) + 10)
    assert e.value.code == "too_large"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("a", "1")
        z.writestr("b", "2")
    with pytest.raises(ConversionError) as e:
        docx_to_markdown(buf.getvalue(), max_members=1)
    assert e.value.code == "too_large"
    p = tmp_path / "a.docx"
    p.write_bytes(mkdocx(f"<w:document {W}><w:body/></w:document>"))
    assert docx_to_markdown(p) == ""


def test_convert_and_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    h = tmp_path / "a.html"
    h.write_text("<p>hi</p>")
    assert convert(h) == "hi\n"
    assert main([str(h)]) == 0
    assert "hi" in capsys.readouterr().out
    out = tmp_path / "o.md"
    assert main([str(h), "--out", str(out), "--base-url", "https://e.com/"]) == 0
    assert out.read_text() == "hi\n"
    assert main([str(tmp_path / "none.html")]) == 2
    x = tmp_path / "a.txt"
    x.write_text("x")
    assert main([str(x)]) == 2
    with pytest.raises(ConversionError):
        convert(x)
    d = tmp_path / "b.docx"
    d.write_bytes(b"bad")
    assert main([str(d)]) == 1
    assert main([]) == 2
