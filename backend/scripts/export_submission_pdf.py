"""把提交用 Markdown 文档导出为 PDF（零第三方依赖）。

流程：Markdown → 带打印样式的 HTML → 本机 Edge 无头打印为 PDF。
不引入 markdown / WeasyPrint / pandoc 等依赖，只实现本项目文档实际用到的语法：
标题、段落、粗体/斜体、行内代码、链接与裸 URL、有序与无序列表（支持一层嵌套）、
引用块、分隔线、表格、围栏代码块。

用法（在 backend 目录下）：
    ..\\.venv\\Scripts\\python.exe scripts\\export_submission_pdf.py
    ..\\.venv\\Scripts\\python.exe scripts\\export_submission_pdf.py 某个文档.md
不带参数时导出 docs/submission 下的《项目报告书》与《项目说明文档》，
生成的 .html 与 .pdf 与源文件同目录同名。
"""

import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
DEFAULT_DOCS = [
    REPO_ROOT / "docs" / "submission" / "项目报告书.md",
    REPO_ROOT / "docs" / "submission" / "项目说明文档.md",
]

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")
HR = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})$")
TABLE_SEP = re.compile(r"^\|?[\s:|-]+\|[\s:|-]*$")
LIST_UL = re.compile(r"^(\s*)[-*]\s+(.*)$")
LIST_OL = re.compile(r"^(\s*)\d+[.)]\s+(.*)$")
QUOTE = re.compile(r"^>\s?(.*)$")
FENCE = re.compile(r"^```(.*)$")

Item = Tuple[int, str, bool]  # (缩进, 已渲染内容, 是否有序)


def render_inline(text: str) -> str:
    """行内语法：先摘出行内代码避免被后续规则污染，再处理转义、粗斜体与链接。"""
    codes: List[str] = []

    def stash(match: re.Match) -> str:
        codes.append(match.group(1))
        return f"\x00{len(codes) - 1}\x00"

    stashed = re.sub(r"`([^`]+)`", stash, text)
    out = html.escape(stashed, quote=False)

    def restore(match: re.Match) -> str:
        return f"<code>{html.escape(codes[int(match.group(1))], quote=False)}</code>"

    out = re.sub(r"\x00(\d+)\x00", restore, out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)", r"<em>\1</em>", out)
    out = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', out)
    # 裸 URL 自动成链；跳过已在 <a href="..."> 内部出现的两处 URL
    out = re.sub(r'(?<!href=")(?<!">)(https?://[^\s<>"，。；、）)]+)', r'<a href="\1">\1</a>', out)
    return out


def split_row(line: str) -> List[str]:
    return [render_inline(cell.strip()) for cell in line.strip().strip("|").split("|")]


def render_table(rows: List[str]) -> str:
    header = split_row(rows[0])
    body = [split_row(row) for row in rows[2:]]
    head = "".join(f"<th>{cell}</th>" for cell in header)
    body_html = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in body)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body_html}</tbody></table>"


def render_list(items: List[Item]) -> str:
    """按缩进分组渲染，支持一层嵌套；同级混用 ul/ol 时以首项为准。"""
    if not items:
        return ""
    base, _, ordered = items[0]
    parts: List[str] = []
    index = 0
    while index < len(items):
        indent, content, _ = items[index]
        if indent < base:
            index += 1
            continue
        cursor = index + 1
        children: List[Item] = []
        while cursor < len(items) and items[cursor][0] > base:
            children.append(items[cursor])
            cursor += 1
        parts.append(f"<li>{content}{render_list(children)}</li>")
        index = cursor
    tag = "ol" if ordered else "ul"
    return f"<{tag}>{''.join(parts)}</{tag}>"


def is_structural(line: str, next_line: str) -> bool:
    """段落遇到结构性行必须结束，否则标题/表格会被吞进上一段。"""
    stripped = line.strip()
    return bool(
        HEADING.match(stripped)
        or HR.match(stripped)
        or FENCE.match(stripped)
        or QUOTE.match(line)
        or LIST_UL.match(line)
        or LIST_OL.match(line)
        or (stripped.startswith("|") and TABLE_SEP.match(next_line.strip()))
    )


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    total = len(lines)
    blocks: List[str] = []
    index = 0

    while index < total:
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        if FENCE.match(stripped):
            lang = FENCE.match(stripped).group(1).strip() or "text"
            buffer: List[str] = []
            index += 1
            while index < total and not lines[index].strip().startswith("```"):
                buffer.append(lines[index])
                index += 1
            index += 1  # 跳过收尾围栏
            blocks.append(f'<pre data-lang="{html.escape(lang)}">'
                          f"{html.escape(chr(10).join(buffer), quote=False)}</pre>")
            continue

        heading = HEADING.match(stripped)
        if heading:
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{render_inline(heading.group(2))}</h{level}>")
            index += 1
            continue

        if HR.match(stripped):
            blocks.append("<hr>")
            index += 1
            continue

        next_line = lines[index + 1] if index + 1 < total else ""
        if stripped.startswith("|") and TABLE_SEP.match(next_line.strip()):
            rows: List[str] = []
            while index < total and lines[index].strip().startswith("|"):
                rows.append(lines[index].strip())
                index += 1
            blocks.append(render_table(rows))
            continue

        if QUOTE.match(line):
            quoted: List[str] = []
            while index < total and QUOTE.match(lines[index]):
                inner = QUOTE.match(lines[index]).group(1)
                if inner.strip():
                    quoted.append(inner.strip())
                index += 1
            body = "".join(f"<p>{render_inline(text)}</p>" for text in quoted)
            blocks.append(f"<blockquote>{body}</blockquote>")
            continue

        if LIST_UL.match(line) or LIST_OL.match(line):
            items: List[Item] = []
            while index < total and (LIST_UL.match(lines[index]) or LIST_OL.match(lines[index])):
                match = LIST_OL.match(lines[index]) or LIST_UL.match(lines[index])
                ordered = bool(LIST_OL.match(lines[index]))
                items.append((len(match.group(1)), render_inline(match.group(2).strip()), ordered))
                index += 1
            blocks.append(render_list(items))
            continue

        paragraph: List[str] = []
        while index < total and lines[index].strip():
            if paragraph and is_structural(lines[index], lines[index + 1] if index + 1 < total else ""):
                break
            paragraph.append(lines[index].strip())
            index += 1
        if not paragraph:  # 兜底：任何未预期的行都不应让主循环停住
            paragraph.append(stripped)
            index += 1
        blocks.append("<p>" + "<br>".join(render_inline(text) for text in paragraph) + "</p>")

    return "\n".join(blocks)


CSS = """
@page { size: A4; margin: 18mm 15mm 16mm; }
body { font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
       font-size: 10.5pt; line-height: 1.75; color: #1f2328; margin: 0; }
h1 { font-size: 17pt; margin: 24px 0 12px; padding-bottom: 6px;
     border-bottom: 2px solid #2c6e49; page-break-after: avoid; }
h2 { font-size: 13.5pt; margin: 20px 0 10px; padding-left: 8px;
     border-left: 4px solid #2c6e49; page-break-after: avoid; }
h3 { font-size: 11.5pt; margin: 16px 0 8px; page-break-after: avoid; }
h4 { font-size: 10.5pt; margin: 14px 0 6px; page-break-after: avoid; }
p { margin: 8px 0; text-align: justify; }
strong { color: #14532d; }
a { color: #0b5cad; text-decoration: none; word-break: break-all; }
ul, ol { margin: 8px 0; padding-left: 22px; }
li { margin: 3px 0; }
li > ul, li > ol { margin: 2px 0; }
hr { border: none; border-top: 1px solid #d0d7de; margin: 18px 0; }
blockquote { margin: 10px 0; padding: 8px 14px; background: #f6faf7;
             border-left: 3px solid #2c6e49; color: #2b3a2f; page-break-inside: avoid; }
blockquote p { margin: 4px 0; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 9pt; }
th, td { border: 1px solid #cfd8d3; padding: 5px 8px; text-align: left; vertical-align: top; }
th { background: #eef3ef; font-weight: 600; }
tr { page-break-inside: avoid; }
code { font-family: "Cascadia Mono", Consolas, "Courier New", monospace;
       background: #f2f4f1; padding: 1px 4px; border-radius: 3px; font-size: 9pt; }
pre { font-family: "Cascadia Mono", Consolas, monospace; font-size: 8pt; line-height: 1.5;
      background: #f7f8f7; border: 1px solid #e2e6e3; border-radius: 4px; padding: 10px 12px;
      white-space: pre-wrap; overflow-wrap: anywhere; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
"""


def build_html(markdown: str, title: str) -> str:
    return (
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
        f"{markdown_to_html(markdown)}</body></html>"
    )


def find_edge() -> Optional[str]:
    candidates = [
        shutil.which("msedge"),
        shutil.which("msedge.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        str(Path.home() / r"AppData\Local\Microsoft\Edge\Application\msedge.exe"),
    ]
    return next((str(path) for path in candidates if path and Path(path).exists()), None)


def export(md_path: Path, edge: Optional[str]) -> Tuple[Path, Optional[Path]]:
    markdown = md_path.read_text(encoding="utf-8")
    html_path = md_path.with_suffix(".html")
    pdf_path = md_path.with_suffix(".pdf")
    html_path.write_text(build_html(markdown, md_path.stem), encoding="utf-8")
    if not edge:
        return html_path, None

    pdf_path.unlink(missing_ok=True)  # 清掉上次产物，避免旧文件掩盖本次失败
    # Edge 需要一个独立用户数据目录才能与已打开的浏览器并存，用完即删，避免在 %TEMP% 里堆积
    with tempfile.TemporaryDirectory(prefix="edge_pdf_") as profile:
        command = [
            edge, "--headless=new", "--disable-gpu", "--no-sandbox",
            f"--user-data-dir={profile}", "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}", html_path.as_uri(),
        ]
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=180)
    if not pdf_path.exists():
        detail = (result.stderr or result.stdout or "").strip()[:300]
        raise RuntimeError(f"Edge 未生成 PDF（退出码 {result.returncode}）：{detail}")
    return html_path, pdf_path


def main() -> int:
    targets = [Path(arg).resolve() for arg in sys.argv[1:]] or DEFAULT_DOCS
    edge = find_edge()
    if not edge:
        print("提示：未找到 Microsoft Edge，只生成 HTML；用浏览器打开 HTML 后「打印 → 另存为 PDF」即可。")
    failed = 0
    for md_path in targets:
        if not md_path.exists():
            print(f"跳过（文件不存在）：{md_path}")
            failed += 1
            continue
        try:
            html_path, pdf_path = export(md_path, edge)
        except Exception as exc:
            print(f"导出失败 {md_path.name}：{exc}")
            failed += 1
            continue
        print(f"HTML  {html_path}　{html_path.stat().st_size / 1024:.0f} KB")
        if pdf_path:
            print(f"PDF   {pdf_path}　{pdf_path.stat().st_size / 1024:.0f} KB")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
