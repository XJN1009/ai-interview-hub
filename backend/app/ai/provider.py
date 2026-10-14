import time
import json
import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx
from app.ai.schemas import (
    ResumeParseSchema, JDParseSchema, QuestionGenSchema,
    AnswerEvalSchema, ReportGenSchema, LearningPlanSchema,
    MatchExplainerSchema, ResumeOptimizeSchema, ResumeRewriteSchema
)
from app.ai.mock_data import (
    MOCK_RESUME_PARSED, MOCK_JD_PARSED,
    generate_mock_evaluation, generate_adaptive_mock_question,
    generate_mock_report, generate_mock_learning_tasks
)

from app.services.ai_provenance import call_context, metadata, traced, PROMPT_VERSION

logger = logging.getLogger("ai_provider")


def _log_ai_call(business_type: str, model: str, tokens_in: int, tokens_out: int,
                 latency_ms: int, status: str, error_code: str = None, result_source: str = "REAL"):

    """异步安全地将一次 AI 调用记入 AICallLog。"""
    from app.core.database import SessionLocal
    from app.models.system import AICallLog
    db = SessionLocal()
    try:
        db.add(AICallLog(
            business_type=business_type,
            **call_context.get(),
            prompt_version=PROMPT_VERSION,
            result_source=result_source,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            status=status,
            error_code=error_code,
            created_at=datetime.utcnow()
        ))
        db.commit()
    except Exception:
        logger.exception("AI 调用日志写入失败")
    finally:
        db.close()


class AIProvider:
    def _current_config(self) -> Dict[str, Any]:
        """每次调用时读取生效配置（DB 覆盖 .env，带缓存，保存即生效）。

        按当前请求上下文中的用户解析：用户若配置了个人 AI Key，则优先使用其
        个人配置，仅影响自身调用；否则回退到全局配置。
        """
        from app.core.database import SessionLocal
        from app.services.ai_settings import get_user_effective_config
        user_id = (call_context.get() or {}).get("user_id")
        db = SessionLocal()
        try:
            return get_user_effective_config(db, user_id)
        finally:
            db.close()

    @property
    def is_real(self) -> bool:
        """仅当显式开启 real 且配置了 Key 时才调用真实模型。"""
        cfg = self._current_config()
        return cfg["mode"] != "mock" and bool(cfg["api_key"])

    async def _call_llm_json(self, prompt: str, schema_class, call_type: str = "UNKNOWN") -> Dict[str, Any]:
        """Calls real LLM API with fallback to mock if unreachable or unconfigured."""
        cfg = self._current_config()
        if cfg["mode"] == "mock" or not cfg["api_key"]:
            reason = "MOCK_MODE" if cfg["mode"] == "mock" else "NO_API_KEY"
            source = "MOCK" if cfg["mode"] == "mock" else "MOCK_FALLBACK"
            metadata(source, "mock-ai", reason)
            _log_ai_call(call_type, "mock-ai", 0, 0, 0, "MOCK" if source == "MOCK" else "FALLBACK", reason, source)
            return None

        headers = {
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": cfg["model"],
            "messages": [
                {"role": "system", "content": "You are a professional AI interview engine. Output ONLY valid JSON matching the requested structure."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        # qwen3 系列默认开启思考模式，会先生成数千推理 token 导致结构化调用超时；
        # 这些确定性 JSON 抽取/生成任务关闭思考可将耗时从 ~90s 降到 ~10s。
        # 该参数为 DashScope 专有，仅对 qwen 模型下发，避免其他供应商报 400。
        if "qwen" in str(cfg["model"]).lower():
            payload["enable_thinking"] = False

        started = time.time()
        status = "SUCCESS"
        error_code = None
        tokens_in = 0
        tokens_out = 0
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)
            ) as client:
                res = await client.post(f"{cfg['base_url'].rstrip('/')}/chat/completions", headers=headers, json=payload)
                latency_ms = int((time.time() - started) * 1000)
                if res.status_code == 200:
                    data = res.json()
                    usage = data.get("usage") or {}
                    tokens_in = usage.get("prompt_tokens", 0)
                    tokens_out = usage.get("completion_tokens", 0)
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    validated = schema_class(**parsed)
                    result = validated.model_dump()
                    _log_ai_call(call_type, cfg["model"], tokens_in, tokens_out, latency_ms, "SUCCESS")
                    metadata("REAL", cfg["model"])
                    return result
                else:
                    latency_ms = int((time.time() - started) * 1000)
                    error_code = f"HTTP_{res.status_code}"
                    status = "ERROR"
                    metadata("MOCK_FALLBACK", "mock-ai", error_code)
                    _log_ai_call(call_type, cfg["model"], 0, 0, latency_ms, "FALLBACK", error_code, "MOCK_FALLBACK")
        except Exception as e:
            latency_ms = int((time.time() - started) * 1000)
            error_code = "TIMEOUT" if isinstance(e, httpx.TimeoutException) else "INVALID_RESULT" if isinstance(e, (ValueError, KeyError, IndexError)) else "PROVIDER_ERROR"
            logger.warning("AI 调用降级：%s", error_code)
            metadata("MOCK_FALLBACK", "mock-ai", error_code)
            _log_ai_call(call_type, cfg["model"], 0, 0, latency_ms, "FALLBACK", error_code, "MOCK_FALLBACK")
            return None
        return None

    @traced
    async def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """Parses resume text into structured entities."""
        # 控制输入规模：PDF 抽取文本常含页眉页脚等噪声，截断可显著降低 LLM 生成耗时
        cleaned = re.sub(r"\n{3,}", "\n\n", resume_text or "").strip()
        cleaned = cleaned[:4000]
        prompt = (
            "Extract the resume into JSON. Output ONLY the JSON object, no markdown, no explanation. "
            "Keep every text field SHORT (phrases, not sentences). Use empty string if unknown.\n"
            'Schema: {"education":[{"school","major","degree","start_date","end_date"}], '
            '"work_experience":[{"company","title","description","start_date","end_date"}], '
            '"projects":[{"name","role","description","technologies","start_date","end_date"}], '
            '"skills":[{"skill_name","level","evidence"}], '
            '"certificates":[str], "warnings":[str]}\n'
            "description fields: max 40 chars each. skills evidence: max 30 chars. "
            "Do not invent facts; only extract what appears in the text.\n\n"
            f"=== Resume ===\n{cleaned}"
        )
        real_res = await self._call_llm_json(prompt, ResumeParseSchema, "RESUME_PARSE")
        if real_res:
            return real_res
        # Mock mode fallback
        validated = ResumeParseSchema(**MOCK_RESUME_PARSED)
        return validated.model_dump()

    @traced
    async def parse_jd(self, jd_text: str) -> Dict[str, Any]:
        """Parses enterprise JD text into job fields and skill requirements."""
        prompt = (
            "Parse this Job Description into JSON.\n"
            "The 'category' field MUST be exactly one of these job families (岗位大类), "
            "choose the closest match to the role:\n"
            "后端开发, 前端开发, 全栈研发, 人工智能, 大数据, 系统运维, 运维架构, "
            "质量保障, 客户端, 系统底层, 信息安全, 产品经理, 用户运营, 销售商务, "
            "人力资源, 财务审计, 市场品牌, 交互视觉设计, 客户成功.\n"
            "If the role does not fit any technical family, pick the nearest non-technical one; "
            "never invent a new category string.\n"
            "The 'competencies' list must fit the role type: for technical roles use names like "
            "专业基础/项目经验/系统设计/沟通表达/综合素质; for NON-technical roles replace 系统设计 with 业务理解 "
            "(business/process understanding) and keep the rest role-neutral. Weights must sum to 100.\n\n"
            f"=== JD ===\n{jd_text}"
        )
        real_res = await self._call_llm_json(prompt, JDParseSchema, "JD_PARSE")
        if real_res:
            return real_res
        validated = JDParseSchema(**MOCK_JD_PARSED)
        return validated.model_dump()

    @traced
    async def generate_question(
        self,
        job_title: str,
        stage: str = "专业基础",
        difficulty: str = "MEDIUM",
        seq: int = 1,
        last_question: str = None,
        last_answer: str = None,
        last_score: float = None,
        jd_text: str = None,
        resume_context: str = None,
        question_type: str = None,
        used_texts: List[str] = None
    ) -> Dict[str, Any]:
        """Dynamically generates interview question based on JD, resume and candidate's previous response."""
        type_hint = ""
        if question_type:
            type_desc = {
                "PROFESSIONAL": "a role-specific technical/professional question grounded in the JD skills",
                "GENERAL": "a general/behavioral question (project deep-dive, collaboration, learning ability)",
                "STRESS": "a pressure question that simulates a high-stress scenario (production incident, hostile challenge, tight deadline)"
            }.get(question_type.upper(), "")
            if type_desc:
                type_hint = f"\nRequired question type: {question_type.upper()} — {type_desc}."

        prompt = (
            f"You are an expert technical interviewer conducting an interview for '{job_title}'.\n"
            f"Question sequence: {seq}\n"
            f"Target stage: {stage} | Difficulty: {difficulty}{type_hint}\n\n"
            f"=== Job Description (JD) ===\n{(jd_text or 'N/A')[:2000]}\n\n"
            f"=== Candidate Resume ===\n{(resume_context or 'N/A')[:2000]}\n\n"
            f"Last question asked: {last_question or 'N/A'}\n"
            f"Candidate's last answer: {last_answer or 'N/A'}\n"
            f"Last answer score: {last_score if last_score is not None else 'N/A'}\n\n"
            f"Requirements:\n"
            f"- Ground the question in the JD's required skills and the candidate's actual resume/projects.\n"
            f"- If the candidate answered with high technical depth, generate a deep follow-up probing edge cases, concurrency, or architectural trade-offs.\n"
            f"- If the candidate's answer was superficial or indicated lack of knowledge, generate a foundational question to diagnose core concepts.\n"
            f"- Output JSON adhering to: question, skill_name, stage, difficulty, hints, "
            f"question_type (PROFESSIONAL|GENERAL|STRESS), time_limit_sec (integer seconds, 120-300)."
        )
        real_res = await self._call_llm_json(prompt, QuestionGenSchema, "QUESTION_GEN")
        if real_res:
            return real_res

        # Adaptive Mock Engine
        raw_q = generate_adaptive_mock_question(
            job_title=job_title,
            seq=seq,
            last_question=last_question,
            last_answer=last_answer,
            last_score=last_score,
            used_texts=used_texts
        )
        if question_type:
            raw_q["question_type"] = question_type
        else:
            # 按阶段推断题型，保证 mock 题也带题型标签
            inferred_stage = raw_q.get("stage") or ""
            if inferred_stage in ("综合素养", "基础素养"):
                raw_q["question_type"] = "GENERAL"
            elif inferred_stage == "压力应对":
                raw_q["question_type"] = "STRESS"
            else:
                raw_q["question_type"] = "PROFESSIONAL"
        validated = QuestionGenSchema(**raw_q)
        return validated.model_dump()

    @traced
    async def evaluate_answer(
        self, question_text: str, answer_text: str, seq: int, jd_text: str = None,
        resume_context: str = None, reference_points: List[str] = None
    ) -> Dict[str, Any]:
        """Evaluates single answer using the 6-dimension Rubric with JSON Schema validation."""
        ref_block = ""
        if reference_points:
            points = "\n".join(f"- {p}" for p in reference_points[:6])
            ref_block = (
                "\n=== Reference Key Points (grading rubric anchor) ===\n"
                f"{points}\n"
                "Judge coverage of these key points explicitly: reward genuinely covered points, "
                "and list uncovered ones in missing_knowledge.\n"
            )

        prompt = (
            "You are a strict but fair technical interview evaluator.\n"
            "Score the candidate's answer on a 0-100 scale across 6 dimensions: "
            "professional(30%), relevance(20%), completeness(15%), logic(15%), depth(15%), communication(5%).\n\n"
            f"=== Job Description (JD) ===\n{(jd_text or 'N/A')[:1500]}\n\n"
            f"=== Candidate Resume ===\n{(resume_context or 'N/A')[:1500]}\n"
            f"{ref_block}\n"
            f"Question #{seq}: {question_text}\n"
            f"Candidate answer: {answer_text}\n\n"
            "Output JSON with keys: score (0-100 float), dimensions "
            "(professional, relevance, completeness, logic, depth, communication), "
            "evidence (list of strings), weaknesses (list), missing_knowledge (list), "
            "suggestions (list), next_action (one of FOLLOW_UP, DEEP, BASIC, CHANGE_TOPIC, FINISH)."
        )
        real_res = await self._call_llm_json(prompt, AnswerEvalSchema, "ANSWER_EVAL")
        if real_res:
            return real_res

        raw_eval = generate_mock_evaluation(question_text, answer_text, seq)
        validated = AnswerEvalSchema(**raw_eval)
        return validated.model_dump()

    @traced
    async def generate_report(
        self, interview_id: int, total_questions: int, scores: List[float] = None,
        qa_pairs: List[Dict[str, Any]] = None, job_title: str = None
    ) -> Dict[str, Any]:
        """Generates comprehensive interview post-review report with radar scores."""
        if qa_pairs:
            from app.ai.mock_data import report_dimension_names, is_technical_role
            dims = "、".join(report_dimension_names(job_title or ""))
            role_hint = (
                "a technical role (use engineering-grounded examples)"
                if is_technical_role(job_title or "")
                else "a NON-technical role (use business/process/communication-grounded examples; never assume software engineering context)"
            )
            transcript = "\n".join(
                f"Q{item.get('seq')}: {item.get('question')}\nA: {item.get('answer')}\nScore: {item.get('score')}"
                for item in qa_pairs
            )
            prompt = (
                f"You are a senior interview coach writing a post-interview review report for '{job_title or '综合岗位'}' — {role_hint}.\n"
                f"Here is the full transcript with per-question scores:\n{transcript[:4000]}\n\n"
                "All feedback text must be in 中文 and grounded in the actual Q&A above.\n"
                f"Output JSON with keys: total_score (0-100 float), performance_level (中文), "
                f"dimension_scores (dict of {dims} -> float), "
                "strengths (list of 中文 strings), weaknesses (list), suggestions (list), summary (中文 string)."
            )
            real_res = await self._call_llm_json(prompt, ReportGenSchema, "REPORT_GEN")
            if real_res:
                return real_res

        raw_report = generate_mock_report(interview_id, total_questions, scores, job_title=job_title)
        validated = ReportGenSchema(**raw_report)
        return validated.model_dump()

    @traced
    async def generate_learning_plan(
        self, job_title: str, gaps: List[str] = None, jd_text: str = None, count: int = 6
    ) -> List[Dict[str, Any]]:
        """Generates staged, targeted tasks for personal growth roadmap based on target job/JD."""
        prompt = (
            f"You are a career coach building a staged learning roadmap for the target role '{job_title}'.\n"
            f"=== Job Description (JD) ===\n{(jd_text or 'N/A')[:2000]}\n\n"
            f"Known weak points / gaps: {', '.join(gaps) if gaps else 'N/A'}\n\n"
            f"Generate exactly {count} learning tasks ordered by stage.\n"
            "Each task must be actionable: include a concrete deliverable (产出物/验收标准), "
            "recommended learning resources (书籍/官方文档/课程名), and an estimated duration in weeks.\n"
            "Output JSON: {\"tasks\": [{\"title\": str(中文), \"competency_name\": str, "
            "\"priority\": \"HIGH|MEDIUM|LOW\", \"reason\": str(中文), "
            "\"action_type\": \"INTERVIEW_PRACTICE|COURSE|READING|PROJECT\", \"stage\": str(中文阶段名), "
            "\"deliverable\": str(中文产出物), \"resources\": [str(推荐资源)], \"estimated_weeks\": int}]}"
        )
        real_res = await self._call_llm_json(prompt, LearningPlanSchema, "LEARNING_PLAN")
        if real_res and real_res.get("tasks"):
            return real_res["tasks"]

        tasks = generate_mock_learning_tasks()
        validated = LearningPlanSchema(tasks=tasks)
        return validated.model_dump()["tasks"]

    @traced
    async def optimize_resume(self, resume_text: str, job_title: str = None) -> Dict[str, Any]:
        """Analyzes and diagnoses a resume, returning structured optimization advice."""
        prompt = (
            "You are a senior resume consultant. Analyze the resume below against the target role "
            f"'{job_title or '通用技术岗位'}'.\n\n"
            f"=== Resume ===\n{resume_text[:4000]}\n\n"
            "Output JSON with keys: completeness_score (0-100 int), strengths (list of 中文 strings), "
            "improvements (list of 中文 strings), suggested_modifications "
            "(list of {section, suggestion} objects), keyword_enrichment (list of 中文技术关键词)."
        )
        real_res = await self._call_llm_json(prompt, ResumeOptimizeSchema, "RESUME_OPTIMIZE")
        if real_res:
            return real_res

        return {
            "completeness_score": 78,
            "strengths": [
                "教育背景清晰，专业技术对口",
                "项目描述具备 STAR 原则雏形，阐明了高并发和分布式锁的应用"
            ],
            "improvements": [
                "建议量化项目收益，例如支撑 QPS 从 800 提升至 5000+",
                "技能模块建议明确区分‘精通’与‘熟练’，突出核心竞争力"
            ],
            "suggested_modifications": [
                {"section": "项目经历", "suggestion": "在电商秒杀项目中补充‘利用 Redis Lua 脚本原子扣减库存’等细节"},
                {"section": "自我评价", "suggestion": "突出对分布式高可用与故障排查的热情与实操案例"}
            ],
            "keyword_enrichment": ["JVM调优", "Redis主从哨兵", "RocketMQ事务消息", "MySQL分库分表"]
        }

    @traced
    async def rewrite_resume(self, resume_text: str, job_title: str = None) -> Dict[str, Any]:
        """Rewrites resume project/skill descriptions to be more compelling without fabricating facts."""
        prompt = (
            "You are a senior resume writer. Rewrite the descriptions in the resume below to be more "
            f"compelling for the role '{job_title or '通用技术岗位'}'.\n"
            "CRITICAL: Never fabricate experiences, companies, metrics or technologies not present. "
            "Only improve wording, structure (STAR) and clarity, and surface existing highlights.\n\n"
            f"=== Resume ===\n{resume_text[:4000]}\n\n"
            "Output JSON: {\"projects\": [{\"name\": str, \"description\": str, \"technologies\": str}], "
            "\"skills\": [{\"skill_name\": str, \"level\": str, \"evidence\": str}], "
            "\"work_experience\": [{\"company\": str, \"title\": str, \"description\": str}], "
            "\"changes\": [list of 中文 strings describing what was improved]}"
        )
        real_res = await self._call_llm_json(prompt, ResumeRewriteSchema, "RESUME_REWRITE")
        if real_res:
            return real_res
        return {"projects": [], "skills": [], "work_experience": [], "changes": []}

    async def explain_job_match(
        self, job_title: str, candidate_skills: List[str], required_skills: List[str]
    ) -> Dict[str, Any]:
        """Calculates deterministic match score and returns explanation."""
        from app.services.matching import skill_match
        result = skill_match(candidate_skills, required_skills)
        return {"match_score": result["score"], "advantage_skills": result["advantage_skills"],
                "missing_skills": result["missing_skills"], "explanation": result["explanation"]}

ai_provider = AIProvider()
