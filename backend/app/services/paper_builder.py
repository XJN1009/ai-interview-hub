"""组卷引擎：从结构化题库按「题型配比 + 岗位技能匹配 + 难度就近」抽题。

设计要点（对齐 docs/report.html 中 v1.0 的可复现组卷思路，并适配本项目的多岗位模型）：
1. 题型配比：专业题 : 通用题 : 压力题，按面试 mode 选择配比，默认 5:3:2。
2. 岗位匹配：专业题只在 Job.category 对应的大类内抽题（技能命中优先），
   不足部分不再向其他大类借题（D2 取消关联大类白名单），直接计入缺口交 AI 按 JD 生成；
   通用/压力题回退到"通用"大类，保证任何岗位都能组出卷。
3. 难度就近：以 Interview.difficulty 为基准，按难度距离排序，同距离优先未用过的题。
4. 阶段有序：抽取后按 STAGE_ORDER 排布题序（综合素养 → 专业基础 → 深度探究 → 项目深挖
   → 系统设计 → 压力应对），同阶段内随机，避免题序与真实面试节奏脱节。
5. 去重与补足：同一卷内题干去重；专业题只取本岗位大类，
   通用/压力题可放宽到不限大类；仍不足时记入 missing，由调用方按 JD + 简历
   用 AI 动态生成兜底（不再跨岗位借题）。
6. 卷面快照：抽题结果写入 InterviewPlan.paper_json，题库后续变更不影响历史面试。
"""

import json
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.question import QuestionBank

# 题型常量
PROFESSIONAL = "PROFESSIONAL"
GENERAL = "GENERAL"
STRESS = "STRESS"

# 面试模式 → 题型配比（专业:通用:压力）。未列出的模式回退 COMPREHENSIVE。
MODE_RATIOS: Dict[str, Tuple[int, int, int]] = {
    "COMPREHENSIVE": (5, 3, 2),
    "TECHNICAL": (7, 2, 1),
    "PROJECT_DEEP_DIVE": (5, 4, 1),
    "BEHAVIORAL": (2, 7, 1),
    "STRESS": (4, 2, 4),
}
DEFAULT_RATIO = MODE_RATIOS["COMPREHENSIVE"]

DIFF_ORDER = {"EASY": 0, "MEDIUM": 1, "HARD": 2}

# 压力题固定为"通用"大类，这里允许按岗位大类精确匹配的专业题类别
GENERIC_CATEGORY = "通用"

# D2 决策：全栈研发 / 系统运维 / 运维架构 已直接补足本大类专业题，
# 原先的 RELATED_CATEGORIES 跨类借题白名单随之取消——专业题只有「本岗位大类」一级候选，
# 取不到就计入 missing 交 AI 按 JD 生成，不再有需要同步登记的硬编码特例。

# 面试阶段排布次序：让自动组卷的题序贴合真实面试节奏（开场通用 → 越问越深 → 压力收尾）。
# 未登记的阶段按「专业基础」位次处理，避免新增 stage 时掉到卷尾。
STAGE_ORDER: List[str] = ["综合素养", "专业基础", "深度探究", "项目深挖", "系统设计", "压力应对"]
_STAGE_RANK: Dict[str, int] = {s: i for i, s in enumerate(STAGE_ORDER)}
_DEFAULT_STAGE_RANK = _STAGE_RANK["专业基础"]


@dataclass
class PaperSlot:
    """一道组卷槽位的抽题结果。"""

    seq: int
    question_type: str
    bank_id: Optional[int]
    skill_name: str
    stage: str
    text: str
    difficulty: str
    reference_points: List[str] = field(default_factory=list)
    hints: Optional[str] = None
    time_limit_sec: int = 180
    source: str = "QUESTION_BANK"

    def to_interview_question_kwargs(self) -> Dict[str, Any]:
        return {
            "bank_id": self.bank_id,
            "seq": self.seq,
            "stage": self.stage,
            "question_type": self.question_type,
            "skill_name": self.skill_name,
            "text": self.text,
            "difficulty": self.difficulty,
            "reference_points_json": json.dumps(self.reference_points, ensure_ascii=False),
            "hints": self.hints,
            "time_limit_sec": self.time_limit_sec,
            "source": self.source,
        }


@dataclass
class Paper:
    """组卷结果：已抽到的题 + 未能满足的题型缺口（交由 AI 兜底）。"""

    slots: List[PaperSlot]
    missing: Dict[str, int]  # {"PROFESSIONAL": 1} 表示该题型仍缺 1 题
    plan: Dict[str, Any]     # 卷面快照（配比、题库统计、命中技能等）

    @property
    def snapshot_json(self) -> str:
        return json.dumps(self.plan, ensure_ascii=False)


def resolve_ratio(mode: str) -> Tuple[int, int, int]:
    return MODE_RATIOS.get((mode or "").upper(), DEFAULT_RATIO)


def allocate_counts(mode: str, total: int) -> Dict[str, int]:
    """按配比把总题量分配为各题型题数，余数按配比从大到小补齐。"""
    total = max(1, int(total or 1))
    pro, gen, str_ = resolve_ratio(mode)
    weight_sum = pro + gen + str_
    raw = {
        PROFESSIONAL: total * pro / weight_sum,
        GENERAL: total * gen / weight_sum,
        STRESS: total * str_ / weight_sum,
    }
    counts = {k: int(v) for k, v in raw.items()}
    remainder = total - sum(counts.values())
    # 余数优先给配比权重高的题型
    for key, _ in sorted(raw.items(), key=lambda kv: kv[1] - counts[kv[0]], reverse=True):
        if remainder <= 0:
            break
        counts[key] += 1
        remainder -= 1
    return counts


def collect_job_skills(job: Optional[Job]) -> List[str]:
    """岗位技能关键词：JobSkill 优先，回退 skills_required 逗号分隔。"""
    if not job:
        return []
    names = [s.skill_name.strip() for s in job.skills if s.skill_name and s.skill_name.strip()]
    if not names and job.skills_required:
        names = [x.strip() for x in job.skills_required.split(",") if x.strip()]
    return names


def _difficulty_distance(item_diff: str, target_diff: str) -> int:
    return abs(DIFF_ORDER.get(item_diff or "MEDIUM", 1) - DIFF_ORDER.get(target_diff or "MEDIUM", 1))


def _norm_token(value: str) -> str:
    """技能归一化：去空白 + 小写，得到可比对的 token（用于技能名与别名的交叉匹配）。"""
    return (value or "").strip().lower().replace(" ", "")


def _split_aliases(raw: Optional[str]) -> List[str]:
    """题库 aliases 字段（逗号分隔）解析为列表。"""
    return [x.strip() for x in (raw or "").split(",") if x.strip()]


def _skill_hit_rank(skill_name: str, aliases: List[str], job_skills: List[str]) -> int:
    """0 = 命中岗位技能；1 = 通用类技能；2 = 未命中（同岗位大类但技能不同）。

    命中判定：把技能名与 aliases 归一化为 token 集合，与岗位技能做相等/包含匹配。
    aliases 让"消息队列"这类岗位技能能命中 skill_name 为 "Kafka" 的题，不再依赖巧合的子串；
    保留包含匹配是为了历史未填 aliases 的题目仍能被正确命中（与原行为向后兼容）。
    """
    tokens = {_norm_token(skill_name)} | {_norm_token(a) for a in (aliases or [])}
    tokens.discard("")
    for js in job_skills:
        j = _norm_token(js)
        if not j:
            continue
        if any(t == j or t in j or j in t for t in tokens):
            return 0
    if _norm_token(skill_name) in {"综合素养", "抗压能力"}:
        return 1
    return 2


def _normalize(item: QuestionBank) -> Dict[str, Any]:
    try:
        points = json.loads(item.reference_points_json) if item.reference_points_json else []
    except Exception:
        points = []
    return {
        "id": item.id,
        "job_category": item.job_category or GENERIC_CATEGORY,
        "question_type": item.question_type,
        "skill_name": item.skill_name,
        "aliases": _split_aliases(item.aliases),
        "stage": item.stage,
        "text": item.text,
        "difficulty": item.difficulty,
        "reference_points": points if isinstance(points, list) else [],
        "hints": item.hints,
        "time_limit_sec": item.time_limit_sec or 180,
        "usage_count": item.usage_count or 0,
    }


def _rank(cand: Dict[str, Any], job_skills: List[str], target_diff: str) -> Tuple:
    """排序键：技能命中 → 难度就近 → 出题次数（均衡）→ 随机（避免固定顺序）。"""
    return (
        _skill_hit_rank(cand["skill_name"], cand.get("aliases") or [], job_skills),
        _difficulty_distance(cand["difficulty"], target_diff),
        cand["usage_count"],
        random.random(),
    )


def _pick(
    pool: List[Dict[str, Any]],
    question_type: str,
    job_skills: List[str],
    target_diff: str,
    used_ids: set,
    used_texts: set,
    categories: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """从候选池中选一道最合适的题；不满足去重/大类约束时返回 None。

    categories=None 表示不限大类（跨岗位兜底）。
    """
    candidates = [
        c for c in pool
        if c["question_type"] == question_type
        and c["id"] not in used_ids
        and c["text"] not in used_texts
        and (categories is None or c["job_category"] in categories)
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda c: _rank(c, job_skills, target_diff))
    return candidates[0]


def _stage_rank(stage: str) -> int:
    """阶段位次；未登记的阶段按「专业基础」处理，避免掉到卷尾。"""
    return _STAGE_RANK.get((stage or "").strip(), _DEFAULT_STAGE_RANK)


def order_by_stage(items: List[Any]) -> List[Any]:
    """按 STAGE_ORDER 排布整卷题序：阶段位次升序，同阶段内随机。

    接受任何带 stage 属性的对象（PaperSlot 或 InterviewQuestion）。
    组卷与创建面试（题库题 + AI 补位题合并后）共用，保证补位题也落在正确阶段位置，
    而不是被追加在卷尾。
    """
    return sorted(items, key=lambda x: (_stage_rank(getattr(x, "stage", "")), random.random()))


def _candidate_tiers(question_type: str, category: str) -> List[Optional[List[str]]]:
    """候选岗位大类的放宽层级（v2 相关性下限）。

    - 专业题：只有 ① 本岗位大类一级（D2 取消关联大类借题后不再有特例）。
      取不到就计入 missing 交 AI 按 JD 生成，不再用其他岗位的陈题顶替
      ——"不限大类"兜底正是"冒出跨岗位不贴切题目"的根因。
    - 通用/压力题：本就归"通用"大类，沿用「本大类 + 通用 → 不限大类」两级兜底。
    """
    if question_type == PROFESSIONAL:
        return [[category]]
    return [[category, GENERIC_CATEGORY], None]


def build_paper(
    db: Session,
    job: Optional[Job],
    mode: str,
    difficulty: str,
    total_questions: int,
    count_usage: bool = True,
) -> Paper:
    """组卷主入口。

    抽题顺序：先按题型配比取题；专业题只在本岗位大类内取，通用/压力题可放宽到不限大类。
    最终仍不足的题量与题型记入 missing，由调用方按 JD + 简历用 AI 生成兜底。

    count_usage=False 用于"组卷预览"：只抽题不累计出题次数，避免预览挤占真实组卷的均衡性。
    """
    counts = allocate_counts(mode, total_questions)
    job_skills = collect_job_skills(job)
    category = (job.category if job else None) or GENERIC_CATEGORY

    # 一次性取出可入卷的题库（数据量小，内存排序即可）：仅取已启用且已审的题
    rows = db.query(QuestionBank).filter(
        QuestionBank.enabled == True,  # noqa: E712
        QuestionBank.review_status == "APPROVED",
    ).all()
    all_items = [_normalize(r) for r in rows]

    used_ids: set = set()
    used_texts: set = set()
    slots: List[PaperSlot] = []
    missing: Dict[str, int] = {}

    # 抽取顺序：专业 → 压力 → 通用，保证小卷也能覆盖到压力题
    draw_order = [PROFESSIONAL, STRESS, GENERAL]
    for qtype in draw_order:
        want = counts.get(qtype, 0)
        got = 0
        tiers = _candidate_tiers(qtype, category)
        for _ in range(want):
            picked = None
            for cats in tiers:
                picked = _pick(all_items, qtype, job_skills, difficulty, used_ids, used_texts, cats)
                if picked:
                    break
            if picked is None:
                break
            got += 1
            used_ids.add(picked["id"])
            used_texts.add(picked["text"])
            slots.append(_to_slot(0, qtype, picked))
        if got < want:
            missing[qtype] = want - got

    # 说明：v2 起不再做"跨题型借用"——它按候选池顺序补位、不看岗位大类，
    # 会把其他岗位的题塞进本卷，正是"冒出跨岗位不贴切题目"的来源之一。
    # 缺额统一保留在 missing，交由调用方按 JD + 简历用 AI 生成。

    # 阶段有序排布：按面试节奏（综合素养 → 专业基础 → 深度探究 → 项目深挖 → 系统设计 → 压力应对）
    # 排序，同阶段内随机——既避免"上来就是系统设计"的错位体感，也不会形成固定题序。
    slots = order_by_stage(slots)
    for idx, slot in enumerate(slots, start=1):
        slot.seq = idx

    # 回写题库使用次数（组卷计数，用于均衡出题）；预览模式不计次
    if count_usage and used_ids:
        db.query(QuestionBank).filter(QuestionBank.id.in_(list(used_ids))).update(
            {QuestionBank.usage_count: QuestionBank.usage_count + 1}, synchronize_session=False
        )

    plan = {
        "mode": (mode or "COMPREHENSIVE").upper(),
        "ratio": dict(zip(["PROFESSIONAL", "GENERAL", "STRESS"], resolve_ratio(mode))),
        "allocated": counts,
        "bank_total": len(all_items),
        "bank_by_type": _type_stat(all_items),
        "matched_category": category,
        "job_skills": job_skills,
        # 相关性下限：专业题不跨岗位大类（D2 起连关联大类也不再借题）
        "relevance_floor": True,
        # 本次采用的阶段排布次序，便于事后核对题序规则
        "stage_order": list(STAGE_ORDER),
        "from_bank": len(slots),
        "missing_for_ai": missing,
        # 抽中的题库 ID（按 seq 顺序），供"预览考卷 → 按此考卷开考"复用
        "bank_ids": [s.bank_id for s in slots],
    }
    return Paper(slots=slots, missing=missing, plan=plan)


def paper_from_bank_ids(
    db: Session, bank_ids: List[int], question_types: Optional[List[str]] = None
) -> List[PaperSlot]:
    """按给定的题库 ID 顺序还原卷面（用于用户已预览并确认的考卷）。

    仅返回题库中真实存在且启用的题目；缺失的 ID 由调用方按缺口用 AI 补足。
    """
    if not bank_ids:
        return []
    rows = db.query(QuestionBank).filter(
        QuestionBank.id.in_(list(bank_ids)),
        QuestionBank.enabled == True  # noqa: E712
    ).all()
    by_id = {r.id: _normalize(r) for r in rows}
    slots: List[PaperSlot] = []
    for idx, bid in enumerate(bank_ids):
        item = by_id.get(bid)
        if not item:
            continue
        qtype = item["question_type"]
        if question_types and idx < len(question_types) and question_types[idx]:
            qtype = question_types[idx]
        slots.append(_to_slot(len(slots) + 1, qtype, item))
    return slots


def _to_slot(seq: int, question_type: str, picked: Dict[str, Any]) -> PaperSlot:
    return PaperSlot(
        seq=seq,
        question_type=question_type,
        bank_id=picked["id"],
        skill_name=picked["skill_name"],
        stage=picked["stage"],
        text=picked["text"],
        difficulty=picked["difficulty"],
        reference_points=picked["reference_points"],
        hints=picked["hints"],
        time_limit_sec=picked["time_limit_sec"],
    )


def _type_stat(items: List[Dict[str, Any]]) -> Dict[str, int]:
    stat: Dict[str, int] = {}
    for i in items:
        stat[i["question_type"]] = stat.get(i["question_type"], 0) + 1
    return stat
