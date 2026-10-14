"""把项目核心源码导出为可提交的「核心代码展示」PDF（零第三方依赖）。

流程：按 MANIFEST 读取源码片段 → 加行号与轻量语法高亮 → 生成带打印样式的 HTML
→ 本机 Edge 无头打印为 PDF。

设计约束：
- 不做 AST 解析，靠「文件 + 行区间」精确裁剪，MANIFEST 是唯一需要维护的地方；
  行区间越界只截到文件末尾，不会报错，方便代码小幅增删后继续用。
- 输出前统一过一遍敏感信息掩码，避免把 Key/口令类字面量带进提交材料。

用法（在 backend 目录下）：
    ..\\.venv\\Scripts\\python.exe scripts\\export_code_showcase_pdf.py
    ..\\.venv\\Scripts\\python.exe scripts\\export_code_showcase_pdf.py --out D:\\tmp\\code.pdf
    ..\\.venv\\Scripts\\python.exe scripts\\export_code_showcase_pdf.py --no-pdf
"""

import argparse
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_submission_pdf import find_edge  # noqa: E402  复用 Edge 定位逻辑

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "submission" / "核心代码展示"

# (相对路径, 行区间列表；None 表示整份文件, 展示说明)

MANIFEST: List[Dict] = [
    {
        "title": "一、AI 模拟面试引擎（核心创新）",
        "intro": "面试全流程的唯一编排入口：逐题评测 → 六维加权 → next_action 自适应换题/插追问 → 反问环节 → 结算报告。REST 与 WebSocket 共用同一份内核，保证两条链路行为一致。",
        "items": [
            ("backend/app/services/interview_core.py", None,
             "面试编排内核：答题评测与结算"),
            ("backend/app/ai/schemas.py", None,
             "AI 输出契约：强制六维齐全 + next_action 决策枚举"),
            ("backend/app/services/ai_provenance.py", None,
             "prompt / rubric 版本与请求隔离溯源上下文"),
        ],
    },
    {
        "title": "二、大模型能力封装与无 Key 降级",
        "intro": "统一封装大模型调用，所有能力方法以 JSON 契约进出；REAL 调用失败自动回退确定性 MOCK 引擎，并把真实/降级、耗时与 token 记入 AICallLog，保证演示与评审环境不中断。",
        "items": [
            ("backend/app/ai/provider.py", None,
             "AIProvider：prompt 构造、JSON 解析、降级与调用审计"),
            ("backend/app/services/ai_settings.py", None,
             "AI 配置优先级（DB > .env）、用户级 Key 与脱敏展示"),
        ],
    },
    {
        "title": "三、智能组卷引擎与结构化题库",
        "intro": "按题型配比 5:3:2 组卷，大类内做技能别名归一匹配、难度就近取值、阶段有序排列，题库缺口交由 AI 兜底生成，兼顾岗位贴合度与题目多样性。",
        "items": [
            ("backend/app/services/paper_builder.py", None,
             "组卷引擎：配比分配、技能命中排序、阶段排序"),
            ("backend/app/data/question_bank.py", [(1, 72)],
             "结构化题库种子（4800+ 行，节选字段与审核批次约定）"),
        ],
    },
    {
        "title": "四、面试会话接口、实时通道与状态机",
        "intro": "会话生命周期由状态机集中拦截非法迁移（409），答题提交带请求幂等与并发租约，超时僵尸会话由兜底任务结算。",
        "items": [
            ("backend/app/core/state_machine.py", None,
             "面试状态合法迁移表与集中拦截"),
            ("backend/app/websocket/interview_channel.py", None,
             "WebSocket 通道：转写定稿、版本 CAS、事件推送"),
            ("backend/app/api/v1/interviews.py", [(186, 488), (744, 870)],
             "面试 REST 入口（节选组卷预览/创建与答题-反问-结算链路）"),
            ("backend/app/services/interview_sweeper.py", None,
             "超时僵尸会话兜底结算"),
        ],
    },
    {
        "title": "五、简历 AI 诊断、能力评估与岗位匹配",
        "intro": "简历支持 PDF/DOCX 抽取与一键 AI 改写；六维胜任力按具体技能逐项累积真实题目证据；岗位推荐基于技能覆盖度打分。",
        "items": [
            ("backend/app/api/v1/resumes.py", [(32, 119), (280, 364)],
             "简历文本抽取、完整度计算、AI 诊断与一键应用"),
            ("backend/app/api/v1/personal.py", [(132, 220)],
             "岗位推荐与六维胜任力诊断（radar + gap 优先级）"),
            ("backend/app/services/matching.py", None,
             "技能覆盖度匹配打分"),
        ],
    },
    {
        "title": "六、数据契约：面试领域模型",
        "intro": "面试、题目、作答、逐题评测、报告与反问提问的数据建模，是评测可追溯、报告可重算的基础。",
        "items": [
            ("backend/app/models/interview.py", None,
             "Interview / Question / Answer / Evaluation / Report / ReverseQuestion"),
        ],
    },
    {
        "title": "七、前端：沉浸式面试间",
        "intro": "语音转写与题目朗读直接使用浏览器原生 Web Speech API，零依赖、不上传音频；逐题限时计时、草稿自动保护、OPENING/QA/REVERSE 三阶段驱动。",
        "items": [
            ("frontend/src/views/personal/InterviewSession.vue",
             [(431, 683), (808, 858), (911, 977)],
             "面试间逻辑（节选：语音转写与朗读、逐题计时、反问提交、答题上报）"),
            ("frontend/src/views/personal/InterviewReportView.vue", [(496, 617)],
             "报告页（节选：六维雷达、胜任力基准、题目收藏与导出）"),
            ("frontend/src/components/RadarChart.vue", None,
             "六维能力雷达图组件"),
        ],
    },
    {
        "title": "八、前端：架构、路由守卫与请求层",
        "intro": "路由懒加载 + requiresAuth / accountType / roles 三级守卫，401 统一收敛到登录态清理，权限判断集中在 store 与拦截器。",
        "items": [
            ("frontend/src/router/index.ts", [(80, 145), (200, 250)],
             "路由表与全局守卫（节选）"),
            ("frontend/src/stores/auth.ts", None,
             "登录态与角色存储"),
            ("frontend/src/api/client.ts", None,
             "Axios 实例：令牌注入、统一响应与 401 处理"),
        ],
    },
    {
        "title": "九、企业招聘协同与平台治理",
        "intro": "企业端覆盖职位发布、候选人全貌档案、招聘管道流转与人才库；治理端负责题库批次审核与 AI 服务管控。",
        "items": [
            ("backend/app/api/v1/enterprise.py", [(477, 546), (641, 676)],
             "候选人全貌档案与招聘管道看板（节选）"),
            ("backend/app/api/v1/admin.py", [(490, 556), (662, 691)],
             "题库检索与批次审核（节选）"),
        ],
    },
    {
        "title": "十、可靠性回归测试",
        "intro": "并发与幂等是评分正确性的前提：并发提交只有一个评分归属、重试不推进题序、反问阶段零 AI 调用、MOCK 评分不污染能力分。",
        "items": [
            ("backend/tests/test_reliability.py", [(269, 422), (446, 458)],
             "答题并发/幂等、报告可恢复、反问幂等与零 AI 调用（节选）"),
        ],
    },
]

SENSITIVE_VALUE = re.compile(
    r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd)\b"
    r"(\s*[:=]\s*)(['\"])([^'\"]{4,})(['\"])"
)
TOKEN_LIKE = re.compile(r"\b(?:sk|ak|pk)-[A-Za-z0-9_\-]{12,}\b|\b[0-9a-fA-F]{32,}\b")

PY_KEYWORDS = set(
    "False None True and as assert async await break class continue def del elif else except "
    "finally for from global if import in is lambda nonlocal not or pass raise return try "
    "while with yield self".split()
)
TS_KEYWORDS = set(
    "abstract any as async await boolean break case catch class const continue debugger declare "
    "default delete do else enum export extends false finally for from function get if implements "
    "import in instanceof interface let new null number object of return set static string "
    "super switch this throw true try typeof var void while with yield".split()
)
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def scrub(text: str) -> str:
    """兜底掩码：口令类字面量与 Key 形态字符串一律替换为圆点。"""
    masked = SENSITIVE_VALUE.sub(
        lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}{'•' * min(12, len(m.group(4)))}{m.group(5)}",
        text,
    )
    return TOKEN_LIKE.sub("••••••", masked)


def highlight(line: str, lang: str, state: Dict) -> str:
    """按行推进的极简高亮：注释 / 字符串 / 关键字 / 数字。

    state["block"] 记录跨行未闭合的 (结束符, 样式类)，覆盖 Python 三引号、
    JS 块注释与反引号模板字符串三种情况。
    """
    keywords = PY_KEYWORDS if lang == "py" else TS_KEYWORDS
    out: List[str] = []
    index = 0
    size = len(line)

    def emit(cls: Optional[str], text: str) -> None:
        if not text:
            return
        out.append(html.escape(text) if cls is None
                   else f'<span class="t-{cls}">{html.escape(text)}</span>')

    if state["block"]:
        term, cls = state["block"]
        end = line.find(term)
        if end == -1:
            emit(cls, line)
            return "".join(out)
        emit(cls, line[:end + len(term)])
        index = end + len(term)
        state["block"] = None

    while index < size:
        ch = line[index]
        pair = line[index:index + 2]

        if lang == "py" and line[index:index + 3] in ('"""', "'''"):
            quote = line[index:index + 3]
            end = line.find(quote, index + 3)
            if end == -1:
                state["block"] = (quote, "str")
                emit("str", line[index:])
                break
            emit("str", line[index:end + 3])
            index = end + 3
            continue

        if pair == "/*" and lang != "py":
            state["block"] = ("*/", "cmt")
            emit("cmt", line[index:])
            break
        if pair == "//" and lang != "py":
            emit("cmt", line[index:])
            break
        if ch == "#" and lang == "py":
            emit("cmt", line[index:])
            break

        if ch in "\"'`":
            quote = ch
            cursor = index + 1
            closed = False
            while cursor < size:
                if line[cursor] == "\\":
                    cursor += 2
                    continue
                if line[cursor] == quote:
                    cursor += 1
                    closed = True
                    break
                cursor += 1
            emit("str", line[index:cursor])
            if not closed and quote == "`":
                state["block"] = ("`", "str")
                break
            index = cursor
            continue

        if ch == "@" and lang == "py" and (index == 0 or line[index - 1] in " \t"):
            match = IDENT.match(line, index + 1)
            end = match.end() if match else index + 1
            emit("dec", line[index:end])
            index = end
            continue

        if ch.isdigit():
            cursor = index
            while cursor < size and (line[cursor].isalnum() or line[cursor] == "."):
                cursor += 1
            emit("num", line[index:cursor])
            index = cursor
            continue

        match = IDENT.match(line, index)
        if match:
            word = match.group()
            emit("kw" if word in keywords else None, word)
            index = match.end()
            continue

        emit(None, ch)
        index += 1

    return "".join(out)


def render_code(start: int, end: int, lines: List[str], lang: str) -> str:
    state = {"block": None}
    rows: List[str] = []
    width = len(str(end))
    for number in range(start, min(end, len(lines)) + 1):
        text = lines[number - 1].rstrip("\n")
        rows.append(
            f'<div class="l"><span class="n" style="width:{width + 1}ch">{number}</span>'
            f'<span class="c">{highlight(scrub(text), lang, state)}</span></div>'
        )
    return f'<div class="code">{"".join(rows)}</div>'


def git_commit() -> str:
    try:
        result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                                capture_output=True, text=True, timeout=10)
        return result.stdout.strip() or "-"
    except Exception:
        return "-"


def read_lines(rel_path: str) -> List[str]:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8", errors="replace").splitlines()


def lang_of(rel_path: str) -> str:
    return "py" if rel_path.endswith(".py") else "ts"


CSS = """
@page { size: A4; margin: 16mm 12mm 16mm 14mm; }
body { font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
       font-size: 10pt; line-height: 1.7; color: #1f2328; margin: 0; }
h1 { font-size: 15pt; margin: 0 0 10px; padding-bottom: 6px; border-bottom: 2px solid #2c6e49;
     page-break-after: avoid; }
h2 { font-size: 11pt; margin: 18px 0 6px; color: #14532d; page-break-after: avoid; }
h2 .path { font-family: "Cascadia Mono", Consolas, monospace; font-size: 9pt; color: #24292f; }
p { margin: 6px 0; }
.lead { color: #40494f; font-size: 9.5pt; }
.meta { color: #57606a; font-size: 8.5pt; font-family: "Cascadia Mono", Consolas, monospace; }
.note { color: #57606a; font-size: 8.5pt; margin-left: 6px; }
.file { page-break-inside: auto; margin-bottom: 14px; }
.section { page-break-before: always; }
.code { font-family: "Cascadia Mono", Consolas, "Courier New", monospace; font-size: 7.6pt;
        line-height: 1.45; background: #fafbfa; border: 1px solid #e2e6e3; border-radius: 4px;
        padding: 6px 8px; }
.l { display: flex; }
.n { flex: 0 0 auto; text-align: right; padding-right: 10px; color: #9aa4ad;
     user-select: none; white-space: pre; }
.c { flex: 1 1 auto; white-space: pre-wrap; overflow-wrap: anywhere; }
.t-cmt { color: #6b7a6f; font-style: italic; }
.t-str { color: #0a6e43; }
.t-kw { color: #a3308f; font-weight: 600; }
.t-num { color: #1c5ea8; }
.t-dec { color: #b06f00; }
.toc li { margin: 2px 0; font-size: 9.5pt; }
.toc .paths { color: #6b747d; font-size: 8.5pt; font-family: "Cascadia Mono", Consolas, monospace; }
"""


def build_html() -> Tuple[str, int, int]:
    parts: List[str] = []
    total_files = 0
    total_lines = 0

    parts.append(
        '<h1>智面舱 · 核心代码展示</h1>'
        f'<p class="meta">仓库 {html.escape(str(REPO_ROOT.name))}　git {git_commit()}　'
        '技术栈 FastAPI + SQLAlchemy + WebSocket / Vue3 + TypeScript + Element Plus + ECharts</p>'
        '<p class="lead">本册按模块挑选最能体现实现思路的核心源码，小文件给完整实现，'
        '大文件按行区间给核心片段（标题下方标注展示区间与文件总行数）。'
        '所有源码在导出时统一做过口令/密钥形态字面量掩码。</p>'
    )

    toc = ["<div class='toc'><h2 style='margin-top:0'>目录</h2><ol>"]
    for section in MANIFEST:
        paths = "；".join(item[0] for item in section["items"])
        toc.append(f"<li>{html.escape(section['title'])}"
                   f"<div class='paths'>{html.escape(paths)}</div></li>")
    toc.append("</ol></div>")
    parts.append("".join(toc))

    for section in MANIFEST:
        parts.append("<div class='section'>")
        parts.append(f"<h1>{html.escape(section['title'])}</h1>")
        parts.append(f"<p class='lead'>{html.escape(section['intro'])}</p>")
        for rel_path, ranges, note in section["items"]:
            lines = read_lines(rel_path)
            spans = ranges or [(1, len(lines))]
            total_files += 1
            shown = sum(min(end, len(lines)) - start + 1 for start, end in spans)
            total_lines += shown
            parts.append("<div class='file'>")
            parts.append(
                f"<h2><span class='path'>{html.escape(rel_path)}</span>"
                f"<span class='note'>{html.escape(note)}</span></h2>"
                f"<p class='meta'>共 {len(lines)} 行　展示 "
                + "、".join(f"L{start}-L{min(end, len(lines))}" for start, end in spans)
                + f"　（{shown} 行）</p>"
            )
            lang = lang_of(rel_path)
            for start, end in spans:
                parts.append(render_code(start, end, lines, lang))
            parts.append("</div>")
        parts.append("</div>")

    footer = (f"<p class='meta'>合计展示 {total_files} 个文件、{total_lines} 行源码。</p>")
    parts.append(footer)

    body = "\n".join(parts)
    document = (
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
        "<title>核心代码展示</title>"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )
    return document, total_files, total_lines


def to_pdf(html_path: Path, pdf_path: Path, edge: str) -> None:
    pdf_path.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="edge_code_pdf_") as profile:
        command = [
            edge, "--headless=new", "--disable-gpu", "--no-sandbox",
            f"--user-data-dir={profile}", "--no-pdf-header-footer",
            "--virtual-time-budget=15000", f"--print-to-pdf={pdf_path}", html_path.as_uri(),
        ]
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=300)
    if not pdf_path.exists():
        detail = (result.stderr or result.stdout or "").strip()[:300]
        raise RuntimeError(f"Edge 未生成 PDF（退出码 {result.returncode}）：{detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description="导出核心代码展示 PDF")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT, help="输出文件名（不含扩展名）")
    parser.add_argument("--no-pdf", action="store_true", help="只生成 HTML")
    args = parser.parse_args()

    missing = [item[0] for section in MANIFEST for item in section["items"]
               if not (REPO_ROOT / item[0]).exists()]
    if missing:
        print("MANIFEST 中以下文件不存在，请修正：")
        for path in missing:
            print(f"  - {path}")
        return 1

    document, total_files, total_lines = build_html()
    out = args.out if args.out.is_absolute() else REPO_ROOT / args.out
    out = out.with_suffix(".html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(document, encoding="utf-8")
    print(f"HTML  {out}　{out.stat().st_size / 1024:.0f} KB　{total_files} 文件 / {total_lines} 行")

    if args.no_pdf:
        return 0
    edge = find_edge()
    if not edge:
        print("未找到 Microsoft Edge，只生成 HTML；用浏览器打开后「打印 → 另存为 PDF」即可。")
        return 0
    pdf_path = out.with_suffix(".pdf")
    to_pdf(out, pdf_path, edge)
    print(f"PDF   {pdf_path}　{pdf_path.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
