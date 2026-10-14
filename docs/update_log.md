# 更新日志

## 2026-10-13（模拟面试自查闭环：缺陷修复 + D1~D6 决策落地）

- **反问环节收尾与幂等加固（§7-①②）**：`/interviews/{id}/reverse` 提问补齐 `request_id` 幂等，`seq` 改按 `max(seq)+1` 推导并由唯一索引 `uq_reverse_interview_seq` / `uq_reverse_interview_request` 兜底并发（迁移 `0011_reverse_idempotency`，先清洗历史重复行）；`/finish` 恢复优雅降级——报告生成失败不再 500 而是返回 `report_state=FAILED + retryable` 且保留已有得分
- **D1 反问语义定稿（反问 = 纯记录提问）**：面试官问"你还有什么想问的吗"，候选人就公司/岗位自由提问，也可直接跳过交卷；**"零成本"同时覆盖成绩与 AI 调用**——不计入总分、不产生 competency 证据、不改变六维得分，且**不再为每条提问调用 LLM**。删除 `AIProvider.answer_reverse_question` 与 `ReverseAnswerSchema`（连带无 Key 时写死的"面试官回答"兜底文案，那属于假数据），`submit_reverse_question_core` 改为同步落库，`interview_reverse_questions` 去掉 `ai_response`/`evaluation_json` 两列（迁移 `0013_reverse_record_only`；该表在开发库为 0 行，无数据损失）；报告快照 `answered_count` → `question_count`，`comment` 从"表现良好/具备信息增量"这种无依据评价改为陈述记录到的条数；面试间删除"面试官回答"气泡与逐条点评，报告区块改名「反问环节记录」，`/reverse` 请求撤掉为等待 LLM 而设的 120 秒超时
- **D6 整场倒计时改为计时器**：契约字段 `remaining_seconds` → `elapsed_seconds`（`interview_core.get_elapsed_seconds` 以服务端 `started_at` 为准，PAUSED 冻结），模拟面试**不再有硬性截止时间**；前端顶部改为「已用 xx:xx」常驻 pill 并删除自动交卷的 `watch(remainingSeconds)` 分支（逐题 `time_limit_sec` 与超时扣分 3分/30秒·上限15 保留不变）
- **D6-② 僵尸会话定时清扫**（新 `services/interview_sweeper.py`）：以「最后活动时间」（创建/开始/暂停 + 最后作答 + 最后反问，**不是** `started_at`）判定闲置 >24h 的 IN_PROGRESS/PAUSED 会话，有作答则 `finalize_interview(force=True)` 结算归档、无作答则 abort；`main.py` 用 `asyncio` lifespan 起停（10 分钟一轮，零新依赖），单轮失败回滚留待下一轮，TestClient 不进 lifespan 故不影响既有回归
- **D2 组卷零跨类**：删除 `paper_builder.RELATED_CATEGORIES` 白名单，`_candidate_tiers(PROFESSIONAL, cat)` 收敛为单一本类；缺口一律交 AI 按 JD 生成，不再借用相邻大类陈题
- **D3+D5 题库批次化与分批放行**：`question_bank` 新增 `batch` 列（迁移 `0012_question_bank_batch`），种子按批次拆为 `P0-CORE 86 / P0-NONTECH 32 / P0-3a 60 / P0-3b 65 / P0-3c 54 / P0-4 24 = 321`；仅 `APPROVED` 题可被组卷抽取，`P0-3a/b/c`（179）与新增 `P0-4`（24）默认 `PENDING` 走管理端审核；补 24 题消除专业题缺口
- **管理端审核面**（`admin.py` + `views/admin/QuestionBank.vue`）：新增 `PATCH /admin/question-bank/{id}/review`、`POST /admin/question-bank/batch-review`（按批次/大类批量放行·驳回·退回待审，只改目标状态外的行故幂等、不覆盖已有人工结论）；列表支持 `review_status`/`batch` 筛选，统计新增 `pending/rejected/by_batch`，页面上待审/驳回卡片可点击直达筛选 + 批次审核面板 + 行级三态操作
- **D4 陈旧脚本修复并纳入回归**：`scripts/test_overtime.py`（此前 422 崩溃）按现行契约重写、`scripts/test_admin_bank_and_insights.py` 修正 `bank_id` 取值与 RETRAIN 结算口径
- **验证**：`pytest tests -q` **76 passed / 0 failed**（回归覆盖：反问分数不变、**反问不触达 LLM**、反问幂等与并发同号、无硬截止、清扫器结算/取消/跳过、批次闸门与零跨类）；冒烟 `test_question_bank.py` **60/60**、`test_overtime.py` **32/32**、`test_admin_bank_and_insights.py` **46/46**；迁移 0011/0012/0013 在开发库**副本**上各自升级→降级→再升级通过（0013 复核反问表最终列集合与两个唯一索引）；`npm run build`（`vue-tsc -b` + 打包）通过；lifespan 起停实测 `idle=24.0h interval=600s`。回归阶段全程只读写副本；随后按发布流程在真实库就地执行了升库/灌库/放行
- **部署提示**：开发库已完成三步（2026-10-13 实测）——升到 **0013**、`seed_question_bank.py` 新增 24 题（总量 **321**）、全部批次放行（`select review_status,count(*) …` → `[('APPROVED', 321)]`，反问表已无 `ai_response`/`evaluation_json`）。其它环境部署同样需要这三步；执行 `0013` 前若该库反问表已有 AI 回答文本请先导出（降级只加回空列），并建议先备份 `zhimeicang.db`（`*.db` 已在 `.gitignore` 内）

## 2026-10-06
- **面试间页面改版：取消/结束合并 + 浅色简约主题 + 铺满布局**（`views/personal/InterviewSession.vue`）：
  - 「取消面试」并入「结束面试」：顶栏单按钮唤起对话框，展示真实作答进度（已答 N/总题数），提供"交卷并生成报告"（无作答时禁用）与"取消面试"（abort 中止归档、不生成报告）两个出口；快捷键 **Esc** 直接唤起该对话框
  - 主题从深色沉浸式改为浅色简约，与全站设计系统统一（页面底 `#F6F7F9`、白卡细边框、主色 `#2563EB`）；移除声波动效、冗余进度条与**写死假数据的"AI 实时表现辅助"抽屉**（158 字/分钟等永不更新，违反"禁止假数据"原则）
  - 布局铺满：修复 `StateContainer` 包裹层阻断 flex 高度传递导致的下方大片空白；回答框随可用高度自动拉伸；max-width 1200→1400px
  - 文案：「经纬职引-智面仓 AI 首席面试官」→「智面仓AI面试官」
- **语音口述"无输出"问题诊断与加固**（同文件）：Web Speech API 的识别在浏览器厂商云端完成（Chrome→Google、Edge→微软），网络不可达时原实现全程静默失败。现补充分级诊断：
  - `network` 错误显式提示并退出录音态；`no-speech` 连续两次提示麦克风未采到声音
  - **识别生命周期常驻指示**（转写期间按钮旁实时显示）：等待音频 → 麦克风已开启 → 已检测到人声 → 正常出字，不依赖一闪而过的 toast
  - **本地音量计**（WebAudio `AnalyserNode` 直采，不经网络）：8 秒无结果时用本地峰值裁决根因——峰值正常但服务无返回 → 提示"网络无法访问浏览器语音服务"；峰值过低 → 提示检查录音设备/音量；停止时以最终结果定稿防丢字、空结果诚实提示"未识别到语音内容"
  - 验证：`vue-tsc` 通过；用户环境实测确认 `audiostart` 触发（权限正常），当前卡点定位在"识别服务无返回或收音"，待用户按新指示器反馈进一步收敛
- **启动脚本精简**：删除 `start_all.bat`（与 `一键打开.bat` 完全重复，后者改为直调 `start_app.ps1 -Mode All`）与 `start_frontend.bat`（单独起前端无意义）；保留 一键打开/一键关闭/start_backend 三个；README 三处引用同步更新
- **开发库与数据维护**：题库灌库 86→118（新增 32 道非技术岗专业题入 `backend/zhimeicang.db`，幂等脚本）；删除项目根目录**陈旧空库** `zhimeicang.db`（47 表全空，系从根目录手工执行脚本误建——`.env` 的 `DATABASE_URL` 为相对路径，`start_app.ps1` 固定以 `backend/` 为工作目录故不受影响，README/脚本无需改动）
- **部署提示**：均为前端与文档变更，刷新页面即生效；如后端进程未重启过，`一键关闭.bat` → `一键打开.bat` 即可

## 2026-10-05（简历中心改版与 AI 解析提速）

- **简历中心重构为「在线简历 / 原文档」双 Tab**（在线简历与上传的原始文件分离存放，互不污染）：
  - **数据与迁移**：新增 `resume_documents` 表（`models/resume.py::ResumeDocument`，仅存 file_url/file_name），Alembic 迁移 `0007_resume_documents`；需 `alembic upgrade head` 建表
  - **后端新接口**（`resumes.py`，登录可用）：`GET/POST/DELETE /resume-documents`（文档列表/登记/删除，登记校验文件归属）；`POST /resume-documents/{id}/parse` 解析原文档并**生成一条独立的在线简历**回填结构化经历（不影响既有简历；用户首条简历自动设为默认；解析非真实来源时 503 拒绝落库）
  - **删除旧接口 `POST /resumes/{id}/parse`**：其"解析结果无条件追加"存在重复叠加缺陷（手动编辑过的简历再解析会翻倍），且新方案下前端已无调用入口
  - **在线简历 Tab**：卡片按钮统一为 结构化编辑 / AI诊断优化 / 更多操作（设为默认、删除）；移除卡片上的目标岗位行与文件相关按钮；按钮统一为深绿主题（浅绿底深绿字、悬停反白），文字清晰可读
  - **原文档 Tab**：左右分栏布局——左侧文档列表（点击选中高亮），右侧常驻内嵌预览区（PDF 用浏览器原生查看器 iframe，DOC/DOCX 显示引导提示 + 新窗口打开）；每项操作为 解析为在线简历 / 删除；上传成功后自动选中新文档
  - **新建简历不再预填数据**：`createNewResume` 仅传 `is_default`；后端 `ResumeCreate.target_job_title` 默认值由 `"Java后端开发工程师"` 改为空串
- **AI 解析提速（修复简历解析必超时 503）**：
  - **根因**：`qwen3` 系列默认开启思考模式，结构化解析前先生成数千推理 token（实测输出 6606 tokens / 90s），固定 25s 超时必然降级 mock 并被溯源保护拦截
  - **修复**（`ai/provider.py`）：模型名含 qwen 时下发 `enable_thinking:false`（实测 **90s → ~10s**，输出 642 tokens；非 qwen 供应商不下发避免 400）；`httpx` 超时改为分阶段 `connect=10s / read=120s / write=30s`
  - **解析 prompt 重写**：显式给出目标 JSON schema、限制字段长度（描述≤40字）、输入文本压缩空行并截断 4000 字符
  - 前端解析请求单独放宽 axios 超时至 150s（`api/index.ts`）
- **其他修复**：`ResumeDocumentOut` 补 `ConfigDict(from_attributes=True)`（Pydantic v2 校验 SQLAlchemy ORM 对象必需，缺失导致文档登记 500）
- **验证**：`vue-tsc` 通过；后端 `py_compile` 通过；真实 PDF 端到端压测确认解析 ~10s 返回合法 JSON
- **部署提示**：后端 uvicorn 无 `--reload`，代码更新后需重启进程（`一键关闭.bat` → `一键打开.bat`）

## 2026-10-05
- **用户级 AI 配置（修复设置页 403 权限拦截）**：求职者「账号与隐私」页加载即弹【权限拦截】——根因为页面并发调用管理员专属接口 `GET /public/ai-stats`。方案为按用户隔离的 AI 配置，而非放开全局权限
  - 数据与迁移：新增 `user_ai_settings` 表（`models/system.py::UserAISetting`，user_id 主键），Alembic 迁移 `0006_user_ai_settings`
  - 服务层（`services/ai_settings.py`）：`get_user_effective_config`（用户字段覆盖全局、缺省回退全局，按用户进程内缓存，全局保存联动失效）、`save_user_config`、`reset_user_config`
  - 调用链路：`AIProvider._current_config` 从请求上下文（trace 中间件的 `call_context.user_id`）解析生效配置——**个人 Key 仅影响本人 AI 调用**，后台任务/未登录回退全局
  - 新接口（`personal.py`，登录即可用）：`GET/PUT/DELETE /personal/ai-config`（读/存/清除个人配置，Key 仅掩码回显）、`POST /personal/ai-config/test`（测试连接）、`GET /personal/ai-usage`（仅本人用量统计）；全局 `/public/ai-settings`、`/public/ai-stats` 保持管理员专属不变
  - 前端：`Settings.vue` AI 标签页按 `isAdmin` 分流（管理员→全局接口，普通用户→个人接口 + "清除个人配置"），文案区分"个人专属仅影响自己"；「活跃会话」标签页按需求改为仅管理员可见；`api/index.ts` 补 5 个封装
  - 验证：新增 `test_personal_ai_config_is_user_scoped`（个人配置隔离、不污染他人/全局、用量接口不再 403）；pytest 全量 69 passed；`vue-tsc` 通过
- **模拟面试非技术岗位覆盖扩展**（此前题库/出题/报告均偏 Java/后端）：
  - **题库 86 → 118 题**（`data/question_bank.py`）：新增 8 个非技术大类——产品经理/用户运营/销售商务/人力资源/财务审计/市场品牌/交互视觉设计/客户成功，各 4 道专业题（专业基础×2 + 深度探究 + 项目深挖），全部含 `reference_points` 评分锚点；通用题/压力题沿用"通用"大类由组卷两级匹配覆盖
  - **修复岗位大类断点**：`JobCreate.vue` 此前不提交 `category`，所有新建岗位静默落默认"后端开发"——新增「岗位大类」下拉（19 类与题库对齐）并接入 payload/编辑回显/JD 解析回填；`parse_jd` prompt 约束 category 只能从 19 个大类取值；`JobSquare.vue` 筛选栏补 8 个非技术大类
  - **Mock 出题引擎按岗位选题**（`ai/mock_data.py`）：新增 `detect_job_category`（15 大类关键词识别，优先级排序防误吞）与分类出题池 `MOCK_QUESTION_BANK_BY_CATEGORY`（15 组 × 6 题 + 通用兜底）；重写 `generate_adaptive_mock_question`——删除写死的 Redis 首题与 Java 专属追问分支，改为按大类取题、答差降难 EASY/答好升难 HARD、`used_texts` 同场去重；`FALLBACK_QUESTIONS` 兜底题去后端化（行业中性）；三处调用点（创建面试/缺口补题/作答链路）传入已用题干
  - **报告维度自适应**：新增 `is_technical_role`/`report_dimension_names`——非技术岗五维雷达"系统设计"→"业务理解"；`generate_mock_report` 反馈文案随岗位类型切换（非技术岗不再出现"高并发/分布式/容灾"措辞）；`generate_report` LLM prompt 按岗位注入维度名并显式声明技术/非技术语境；`parse_jd` 约束 competencies 命名（非技术岗禁用"系统设计"，保护能力诊断口径）
- **测试脚本修复与更新**：
  - `scripts/test_question_bank.py`：适配 cd1db71 收紧的作答契约（必填 `question_id` + 幂等 `request_id`），新增 `answer()`/`current_qid()` 辅助，5 处调用点同步——修复 14 项连锁失败
  - `tests/test_job_search.py`：迁移 head 断言更新至 0006
  - 验证：pytest 69 passed；题库冒烟 44/44 全过（含自适应追问/自动结算/闭卷控制）；岗位识别 13 例抽查、两类岗位出题与报告维度差异抽查、`vue-tsc` 均通过
  - 部署提示：需 `alembic upgrade head` 建表 + 重跑 `scripts/seed_question_bank.py` 灌入新题（幂等）

## 2026-09-30
- **AI 引擎配置向导（方案 A：系统级全局配置，登录前可配置）**：自部署用户无需改 `.env`、无需重启，即可在页面配置自己的 LLM API-KEY / Base URL / 模型，保存即时生效
  - **后端存储与读取**：新增 `system_settings` 键值表（`models/system.py::SystemSetting`，随 create_all 自动建表）；新增 `services/ai_settings.py`——生效优先级 **DB > .env > 默认值**，进程内缓存 + 保存即失效；`AIProvider` 改为每次调用动态读取生效配置（13 处调用点零改动），未配置 Key 时照旧回退 mock
  - **登录前公开接口**（`public.py`）：`GET /public/ai-settings`（Key 仅掩码回显）、`PUT /public/ai-settings`（**首次未配置允许匿名写入**，已配置后仅 PLATFORM_ADMIN/SUPER_ADMIN 可改，其余 403）、`POST /public/ai-settings/test`（真实最小 chat 请求验证连通性，失败优雅返回原因）；Base URL 仅允许 http/https 协议（400 拦截）
  - **管理端接真**：`admin.py` 的 `GET/PATCH /admin/ai/providers` 从写死假数据改为读写同一份真实配置（支持 mode/model/base_url/api_key，空 Key 视为不修改）
  - **前端**：新增登录前向导页 `views/auth/AISetup.vue`（路由 `/ai-setup`，模式切换 + 5 个服务商预设一键填入 OpenAI/DeepSeek/通义/Kimi/Ollama + 测试连接）；`Login.vue` 未配置时显示黄色引导横幅、底部新增"AI 引擎配置"入口；`AIService.vue` 保存支持完整字段并新增"测试连接"按钮
  - 验证：接口 9 项断言全过（匿名/普通用户篡改 403、非法 URL 400、空 Key 保持原值、掩码不回显明文、测试连接优雅失败、清理后回退 .env）；浏览器实测 3 页面（向导回填/预设联动/登录页入口）通过，无 JS 报错；`vue-tsc` 类型检查通过
- 面试间摄像头镜像修复：`InterviewSession.vue` 预览视频加 `transform: scaleX(-1)` 水平翻转，消除前置摄像头镜面显示（仅视觉翻转，不影响采集流）
- **个人中心假数据全面清理**（前端 5 页 + 后端 5 接口，原则：无数据即空态，禁止写死兜底伪装繁荣）：
  - **Settings.vue 字段错位 bug + 假记录**：授权表改读后端真实字段（`scope/target_type/granted_at/revoked`，原读 `purpose/created_at/is_revoked` 导致真数据永远显示成写死文案且撤销状态恒为"生效中"）；会话表改读 `device/ip`；删除失败时注入的假授权/假会话记录；新增 scope/target_type 中文映射
  - **GrowthCenter.vue 假兜底回滚**：删除前端复活的 `82 分/85%/68-74-82 假趋势`（后端 9-28 已删，前端 `||` 兜底又加了回来）；null 显示"暂无"，趋势图与技能轨迹空态用 `el-empty`
  - **Dashboard.vue + `/personal/dashboard`**：后端无面试时 `recent_score` 返回 null（原写死 82）、训练时长去掉 `+4.2` 伪基数、准备度无分不计算、删除写死的 3 条今日任务（id 101-103，打卡必 404）与 68/75/82 假成长曲线、welcome 假默认岗位改 null；前端删除"张同学/82/4.2/5-1 周假曲线"兜底，空态显示引导链接（设置目标岗位/生成学习路线/完成首场面试）
  - **Assessment.vue**：删除雷达图三组写死数组（Java基础/Redis…六维与两组分值），改为直读后端真实 `radar`，空数据 `el-empty`
  - **`/personal/competencies` 与 `/{skillId}/evidence`**：删除无数据时的 5 条 mock 能力分与 3 条假证据链，返回空列表（确认无前端调用方依赖）
  - **`/learning/plans/current` + LearningRoadmap.vue**：删除无计划时写死的 4 条假任务（含假 progress 40/100），新增 `has_plan` 标记；前端空态引导一键生成学习规划，副标题假默认岗位改"未设置"
  - **`/personal/profile` + Profile.vue**：删除无档案时的假默认值（北京航空航天大学/计算机科学与技术/2024/热爱高并发/15-25K 等），字段返回 null，表单留空引导真实填写
  - **打卡接口诚实化**：`POST /learning/tasks/{id}/complete` 任务不存在时返回 404（原静默成功），前端各页不再吞错，失败显示真实报错
  - 验证：`vue-tsc` 类型检查通过；后端语法检查通过
- 学习路线混合架构改造（参照 `docs/references/AI岗位学习路线与规划.md` 的课程表形式）：
  - 新增岗位模板库 `backend/app/data/learning_path_templates.py`：从参考文档提炼 5 个 AI 岗位（智能内控 / AI Native 创新小组 / 滴滴 / AI 应用工程师 / Agent 开发工程师）的分阶段路线，每个任务含**产出物（deliverable）、推荐资源（resources）、建议周期（estimated_weeks）**；`match_keywords` 按特化优先排序避免误匹配
  - 数据模型：`LearningTask` 新增上述 3 字段（`ensure_schema` 增量迁移）；`/learning/plans/current` 返回新字段与阶段周期
  - 生成逻辑（`personal.py::generate_and_store_learning_plan`）：命中模板 → 模板骨架 + 面试薄弱项确定性个性化（命中任务升 HIGH 并改写依据）；未命中 → 回退 LLM 动态生成，prompt 已强制要求输出产出物/资源/周期字段
  - 前端 `LearningRoadmap.vue`：阶段标题显示"建议 N 周"，任务卡新增"产出物 + 推荐资源标签"区块
- 学习路线两项存量缺口修复：
  - **能力分文案不符**：`POST /learning/tasks/{id}/complete` 真实实现能力分联动——按任务 `competency_name` 给 `UserCompetency` +2（上限 100）并写入 `CompetencyHistory`（source=PRACTICE，成长中心技能进步曲线自动消费）；重复打卡幂等不重复加分；前端文案改为如实反馈实际加分
  - **PATCH 进度未接入**：前端 `api/index.ts` 补 `updateTaskProgress` 封装；任务卡进度条新增"调整进度"滑块，中间进度（0-100）可记录；后端 PATCH 补齐语义——越界钳制、滑到 100% 视同完成并发放能力分加成（与"标记已学完"一致）、>0 自动转 IN_PROGRESS；新增"攻坚中"状态标签
  - 验证：端到端断言通过（模板命中/误匹配防护、薄弱项提升 HIGH、打卡加分与幂等、PATCH 40%→IN_PROGRESS、100%→COMPLETED+加分、越界钳制）；`vue-tsc` 类型检查通过；顺带以模板路线填充了 learning_plans/learning_tasks 演示数据（此前为 0 行）

## 2026-09-29
- 语音链路治理（B 类第 7 项）浏览器实测收尾：设备检测卡显示真实文案（摄像头/麦克风数量、TTS 能力、后端往返实测毫秒），"语音口述/停止口述""重听题目/停止朗读"状态切换正常，键盘答题主流程无回归，无 Vue 报错——该条目至此完整交付
- 项目范围决策（更新《功能完善与实现建议》第五章）：明确本项目定位为竞赛作品/校内演示，砍掉与威胁模型不匹配的企业级能力——登录验证码、接口限流、Redis 缓存、AI 异步任务队列（Celery）、病毒扫描、邮箱/手机验证、Prometheus 监控告警，标注为"范围外（明确不做，非遗漏）"并记录现状兜底（mock 回退、dev_reset_token、扩展名+大小校验等）；保留低成本高价值项：企业/管理端统计真实化、候选人匹配度排行榜、AICallLog 可观测、/health、MIME 魔数校验与上传配置化、SECRET_KEY/CORS 收尾、pytest 改造，统一并入缩减后的第 3 批；原第 4 批取消独立存在

## 2026-09-22
- 修改.bat启动文件，采取虚拟环境管理依赖
- 优化登录、注册流程，登录时显示曾经登录过的账号列表；注册时修改为需填写用户名、邮箱地址、密码、确认密码
- 个人求职者端功能完善（原《功能完善与实现建议》第 1、2 批，已全部实现）：
  - 账号安全：新增修改密码端点（校验旧密码）；找回密码两步流程（邮件重置链接，未配置 SMTP 时返回开发令牌兜底）
  - 能力诊断真实化：岗位要求（JobCompetency）× 最新面试报告维度分实时计算差距，无记录时以用户能力均值兜底并诚实标注证据
  - 岗位探索/工作台推荐匹配分真实化：基于候选人技能与岗位技能命中的确定性计算，替换全部写死分值
  - 模拟面试 WebSocket 通道与 REST 逻辑同步：出题/评分/报告注入 JD + 简历上下文，学习路线使用真实目标岗位
  - 消息中心：新增通知实时推送 WebSocket 与批量已读端点，导航栏红点按未读数驱动
  - 账号与隐私：登录会话落库（jti 校验，支持真实设备列表与强制下线）；通知偏好落库
- 模拟面试题库与组卷引擎（第 2.5 批）：
  - 新增结构化题库 QuestionBank：86 题（62 专业 / 12 通用 / 12 压力），覆盖 11 个岗位大类，每题含参考答案要点与逐题限时；幂等灌库脚本并入 seed_demo
  - 组卷引擎：按面试模式题型配比抽题（综合 5:3:2、技术 7:2:1、压力 4:2:4 等），岗位技能优先命中、难度就近、题干去重、跨题型补足，卷面快照固化保证历史可复现
  - 创建面试改为一次性预生成整卷；新增配比查询、组卷预览、题库统计三个端点；支持"预览考卷 → 按此考卷开考"（所见即所考）
  - 闭卷与复盘机制：作答中不下发参考答案，面试结束后报告逐题下发参考答案要点用于对照补短板
  - AI 协同：题库缺口或关闭题库时回退 AI 实时出题并兜底参考答案；评分支持以参考答案要点作为锚点；REST 与 WebSocket 两条通道一致
  - 前端：创建页题库开关与考卷预览弹窗；面试间题型胶囊、逐题计时、来源标签与真实用时上报；报告页题型标签与参考答案对照
  - 验证：44 项端到端断言全部通过（backend/scripts/test_question_bank.py），真实 LLM 全链路与前端 UI 均验证通过

## 2026-09-28
- 模拟面试正确性修复（A 类问题 5 项，全部完成）：
  - 会话状态机：新增 `app/core/state_machine.py` 集中声明合法迁移（READY→IN_PROGRESS⇄PAUSED→COMPLETED/CANCELLED），非法迁移入口拦截返回 409——重复开始、重复提交同题（不再静默覆盖重评）、结算/中止后再作答或交卷均被拒绝；新增 `POST /interviews/{id}/abort` 中止端点（不生成报告，已答部分保留可查）
  - 双通道统一：抽取 REST 与 WebSocket 共用的答题/推进/结算核心服务 `app/services/interview_core.py`，WS 不再重复创建评分记录；能力沉淀由写死 "Redis" 改为最后作答的真实技能名；结算幂等
  - 自适应追问真实生效：评分返回的 next_action（FOLLOW_UP/DEEP 升难、BASIC/SIMPLIFY 降难）驱动从题库抽取同技能不同难度的追问题插入卷面，后续题号后移、总题数 +1（每场上限 2 次，题库无合适题自动放弃）；卷面快照记录 followup_count，前端提示"AI 面试官追加了针对性问题"
  - 整场计时服务端化：以 started_at 计算 remaining_seconds 并在 start/resume/answer/详情接口下发，刷新页面不再重置；面试间时间归零自动交卷生成报告；最后一题答完由服务端自动结算并直接返回 report_id
  - 假数据清理：面试列表无报告时 score 返回 null（前端显示"未生成"）；报告接口未结算时返回 404 而非写死的 82 分假报告；无任何作答交卷被 409 拒绝
  - 验证：test_question_bank.py 重写覆盖新行为共 44 项断言全部通过（含追问升难/降难、409 拦截、abort、自动结算）；真实 LLM 实机全链路验证通过；前端构建（vue-tsc）通过
- 模拟面试功能缺口补全（B 类第 8、9 项）：
  - 题库管理界面（M08）：新增 `GET/POST/PUT /admin/question-bank` 与 `PATCH /{id}/toggle`（仅 PLATFORM_ADMIN/SUPER_ADMIN 可访问）；支持分页 + 关键词/岗位大类/题型/难度/启用状态筛选与全量分类统计；题干去重与枚举校验；新题 source=MANUAL（种子重建不丢失）；只停用、不物理删除（bank_id 被历史卷面与错题清单引用）
  - 管理端页面：新增 `views/admin/QuestionBank.vue`（展开行查看题干与参考答案要点、编辑弹窗要点动态增删、"编辑仅影响之后组卷"提示），路由 `/admin/question-bank` 与侧边栏入口
  - 面试历史对比：`GET /interviews/history-comparison` 同岗位逐维趋势与 delta；`Interview` 新增 `purpose`(NORMAL/RETRAIN) 与 `derived_from_id` 字段（ensure_schema 迁移 + 回填），默认排除重练记录，少于 2 次返回空态不写死
  - 薄弱题重练：`GET /interviews/weak-questions` 按 bank_id 聚合历次得分、以"最近一次得分 < 阈值"判定薄弱并过滤已停用题；面试记录页新增"成长对比 + 薄弱题"双卡，一键重练直接复用 selected_bank_ids 按指定考卷开考（purpose=RETRAIN，不计入成长曲线）
  - 成长中心去假数据：`/personal/growth` 移除写死的 68/74/82 趋势与 85% 完成率兜底，改为真实聚合 + 空态（has_data/None），并默认排除重练记录
  - 验证：新增 test_admin_bank_and_insights.py 33 项断言全部通过（权限、CRUD、停用不组卷、薄弱清单、重练卷面、对比口径、growth 空态）；基线 test_question_bank.py 44 项无回归；前端构建通过；实机抽查迁移生效与端点数据正常
- 单题服务端超时校验（B 类第 6 项）：
  - 计时锚点：`Interview` 新增 `current_question_shown_at`（当前题呈现时间）与 `paused_at`（暂停时刻），`InterviewAnswer` 新增 `overtime` / `overtime_sec`；均由 `ensure_schema` 增量迁移并回填旧数据
  - 服务端判定：单题真实用时按 `utcnow - 呈现时间` 计算并**覆盖客户端上报的 duration_sec**（防脏数据与刷分），无锚点的历史会话退回客户端值；推进下一题/插入追问题时重置锚点，创建面试与 WS 连接时写入锚点
  - 超时轻扣分（不归零）：每超时 30 秒扣 3 分、上限 15 分，扣分过程写入评分证据（`raw_score → total_score`）并在接口响应返回 `raw_score/overtime/overtime_sec`，REST 与 WebSocket 两条通道一致
  - 空作答：直接判 0 分并给出"避免留白"的针对性建议，不消耗 LLM 调用，也不叠加超时扣分
  - 暂停豁免：resume 时把暂停时长从单题与整场锚点中整体剔除，暂停 10 分钟不会被判超时
  - 报告时间维度：`/interviews/{id}/report` 新增 `time_analysis`（累计/平均/极值用时、限时占用率、超时题数与超时率、超时集中的技能），逐题分析补 `duration_sec/time_limit_sec/overtime/overtime_sec/is_empty`
  - 前端：面试间按服务端结果提示"超时 N 秒已轻扣分（raw → final）"或"空作答按 0 分记录"；报告页逐题复盘新增"答题节奏与时间利用"分析卡（指标 + 逐题用时进度条 + 超时技能结论），逐题标题显示超时标记
  - 验证：新增 test_overtime.py 26 项断言全部通过（锚点写入、超时标记与秒数、扣分上限与不归零、服务端纠正客户端用时、空作答 0 分、暂停 600 秒豁免、报告时间统计）；基线 test_question_bank.py 44 项与 test_admin_bank_and_insights.py 33 项均无回归；前端构建通过；实机验证超时 80 秒扣 9 分、总用时统计准确
- 语音链路治理（B 类第 7 项，决策：不接云端 ASR/TTS，走浏览器原生能力 + 假指标清零）：
  - 假指标清零：`InterviewAnswerRequest` 移除 `speaking_rate/filler_count` 入参；核心服务显式写 0（语义"未测量"）；模型默认值 160/2 改为 0；`seed_demo` 不再灌假值；`ensure_schema` 启动时一次性把历史 answers 的假指标（160/2）清洗归零（已验证 87 条全部归零）
  - 真实语音转写：面试间"语音口述"按钮接入浏览器原生 Web Speech API（zh-CN、continuous、interimResults），识别结果实时写入回答框；不支持的浏览器/权限拒绝/异常均有降级提示，onend 自动重启防静默中断；暂停与页面卸载时正确 abort 并释放资源
  - 真实题目朗读："重听题目"改为 `speechSynthesis` 朗读当前题干（可停止），替代原"假重播"提示
  - 设备检测真实化：创建页四项检测改为真实探测——`enumerateDevices` 枚举摄像头/麦克风数量、TTS 能力检测、后端连通性实测往返毫秒（不再写死"延迟 25ms 优秀"），不支持项如实标灰/标黄
  - 验证：三套后端测试（44+26+33）无回归；前端构建通过；浏览器实测：检测卡显示"检测到 2 个（可文本作答）/检测到 3 个，支持语音转写/支持题目朗读/服务正常，往返 34ms"，"停止朗读""停止口述"状态切换正常，键盘答题主流程不受影响，无 Vue 报错
