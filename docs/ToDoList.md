# 前端页面对应模块

## 合并

- 简历中心、成长中心、学习路线、能力诊断归类于个人档案

## 新增

1. 个人工作台：
2. 岗位探索：
3. 我的求职：
4. 简历中心：
   - 加入简历优化功能
   - “上传本地简历”功能实现“直接上传至前端显示为可打开的文档”或者“读取文件并提取信息结构化显示”
   - 简历完整度的百分比显示需根据“实际用户上传内容量”动态更新
   - 进入AI智能诊断界面后无法返回“简历中心”
   - AI智能诊断需接入AI模型，实现对用户上传的简历进行分析和诊断
5. 能力诊断：
6. 模拟面试：
   - 模拟面试功能：系统根据用户输入的岗位JD和用户上传的简历，模拟面试面试场景
7. 成长中心：
8. 学习路线：
   - 加入根据岗位JD自动生成学习路线功能，将路线展示在“学习路线”页面，分阶段展示待办便于用户学习
9. 消息中心：
10. 个人档案：
11. 账号与隐私：

## 优化

1. 个人工作台：
   - 将“个人工作台”左上角目标岗位的显示与“个人档案”中信息对齐
2. 岗位探索：
3. 我的求职：
4. 简历中心：
5. 能力诊断：
6. 模拟面试：
7. 成长中心：
8. 学习路线：
   - ~~打卡提示"能力分已同步提升"但后端未更新 UserCompetency（文案与实现不符）~~ ✅ 已完成（2026-09-30：complete 端点真实发放能力分 +2 并写 PRACTICE 历史，重复打卡幂等）
   - ~~progress 字段无前端更新入口，只能"标记完成"置 100（PATCH 端点未接入）~~ ✅ 已完成（2026-09-30：前端补 updateTaskProgress + 进度滑块，100% 视同完成并发放能力分）
   - ~~COURSE/READING/PROJECT 仅是标签，无课程内容/外链/学习资源，任务不可执行~~ ✅ 已完成（2026-09-30：新增 5 个 AI 岗位模板库，任务带产出物+推荐资源+建议周期；未命中模板时 LLM 生成同样强制输出这三字段）
9. 消息中心：
   - 标题栏的“消息中心”跳转按钮当前为常态红点标记，后需更改为正常图标
10. 个人档案：
   <!-- - 标题栏用户名称显示为用户注册时的姓名；若“个人档案”中姓名有更改，则随之更新 -->
11. 账号与隐私：
   - 注册账号时的必填信息稍作修改，如：
      - 用户名：虚拟名称
      - 邮箱：用户邮箱地址
      - 密码：用户设置的密码
      - 确认密码：用户确认密码

# 待办事项

## 一、值得新增的功能模块（报告有、本项目无）

| 优先级 | 模块 | 报告做法 | 本项目现状 | 为什么值得补| 状态 |
| :--- | :--- | :--- | :---: | :--- | :---: |
| P0 | 结构化题库 + 组卷引擎 | 6 岗位 × 60 道预置题，按专业:通用:压力 = 5:3:2 抽题，去重打乱 | 已建 `QuestionBank`（86 题）+ `paper_builder` 按 mode 配比组卷 | 三重收益：① 无网/无 Key/额度耗尽时功能 100% 可用；② AI 成本从"每题一次调用"降到"仅评分"；③ 同岗位题目稳定，学生成绩可横向比较 | ✅ 已完成 |
| P0 | 卷面 JSON 固化（历史可复现） | 组卷结果以 JSON 快照写入会话记录 | 已加 `InterviewPlan.paper_json`，抽题结果与 bank_id 全量固化 | 与已有`jd_text` 快照思路一致，顺手可做 | ✅ 已完成 |
| P1 | 参考答案要点 + 逐题对照 | 每题附「参考答案要点」+ 逐题诊断，学生可对照补短板、教师可据此教学 | 题库题带要点，作答中闭卷不下发、结算后报告逐题对照 | 这是"测—评—学"闭环的关键缺口，直接接现有学习路线 | ✅ 已完成 |
| P1 | 会话状态机 + 非法迁移拦截 | `created→in_progress→evaluating→finished→archived` 集中声明，非法迁移入口即返 409；支持 abort | 已加 `core/state_machine.py`，重复开始/重复提交/终态后操作一律 409，新增 abort 端点 | 属于 正确性缺陷修复 ，不只是新功能 | ✅ 已完成 |
| P1 | 逐题倒计时 + 超时处理 + 字数统计 | 倒计时环、进度条、字数统计、分类临场提示；超时不归零只轻扣 | 逐题限时下发 + 服务端按呈现时间锚点计时；超时轻扣（30s/3分，上限15分不归零）、空作答判 0 分、暂停豁免、报告含 time_analysis；字数统计已有 | 报告明确"超时提交不报错且给出反馈"，这是压力面试还原的核心 | ✅ 已完成 |
| P2 | 岗位候选人匹配度排行榜 | 按匹配度排序的榜单 + 成绩段分布 | `/enterprise/candidates` 已算出`match_score` 但按`Application.id desc` 排序，等于没排序 | 数据已就位，只差排序 + 榜单视图，性价比极高 |  待实现 |
| P2 | 评分通道可观测接口 | `GET /api/channel` 返回当前通道与降级原因；LLM 异常自动降级不扩散 | 有 mock 回退但 不可观测 ；`AICallLog` 表定义了却 全库零写入点、零查询端点 | 正好合并进待办第 3 批"管理端 AI 统计真实化" | ⏳ 待实现 |
| P2 | 题型三分类（专业/通用/压力） | 三类题、压力题专门给情绪应对反馈 | 题库带 question_type，按 mode 配比抽题（综合 5:3:2、压力 4:2:4），面试间与报告均显示题型标签 | 选压力面试却拿不到压力题，是明显的功能空转 | ✅ 已完成 |
| P3（可选） | 零依赖单进程演示模式 | `python main.py` 一条命令、无构建无 CDN | 需 venv + pip + npm install + Vite | 竞赛/评审现场可能断网，值得留一个"打包演示"开关（如后端直接托管 `dist/`） | ⏳ 待决策 |

## 二、需要修改的本项目自身问题（报告反衬出来的）
这几处 报告是诚实的、本项目名不副实 ，建议优先处理：

1. ~~README 与代码不符~~ ✅ **已修复**：题库已落地，README 启动章节也已改为虚拟环境版；"从题库或 AI 生成"现在与代码一致。
2. ~~`duration_sec` 是假数据~~ ✅ **已修复（2026-09-28）**：服务端按 `current_question_shown_at` 锚点计算真实单题用时并**覆盖客户端上报值**，超时轻扣分、空作答判 0 分；"作答节奏"不再基于假字段给分。
3. ~~`speaking_rate` /`filler_count` /`audio_file_id` 是空壳字段~~ ✅ **已修复（2026-09-29，决策：不接云端 ASR）**：接口入参移除、写入语义改为 0=未测量、模型默认值与种子修正、历史假数据启动清洗归零；语音作答改浏览器原生 Web Speech API 转写，"重听题目"改真实朗读，创建页设备检测真实化。列保留（SQLite 不支持删列）但不再承载假数据。
4. ~~成长曲线与报告有硬编码兜底~~ ✅ **已修复（2026-09-28）**：`/personal/growth` 改为真实聚合并支持空态（`has_data`/`null`），报告接口未结算返回 404、列表 score 返回 null，不再产出写死的 68/74/82 与 82 分假报告。
另外，报告暴露的 统计真实化缺口 与你`docs/功能完善与实现建议.md` 第 3 批完全重合：企业端`get_analytics` （`interview_rate: 65` 写死）、管理端`get_ai_providers` （`success_rate: 99.8` 写死）。报告里的「7 项核心指标 + 岗位训练量柱状图 + 成绩段分布」可以直接作为这两个接口的目标形态。 ⏳ **仍待实现（第 3 批）**

---
# 完成事项

## 新增 4 · 简历中心

4.1 加入简历优化功能 目前只有"诊断报告"（只读），无"优化并应用"闭环。API 已预留`optimizeResume` ，但没有应用建议的入口。
   - api/index.ts — 需新增`applyOptimization` 等接口
   - Resumes.vue — 卡片操作区需增加"简历优化"按钮
   - resumes.py — 需新增真正执行改写的优化端点

4.2 "上传本地简历"功能（当前为假实现） 上传成功后完全忽略返回值，写死了一段 mock 数据。这是最关键的一处。
   - **决策（已定）：采用「预览」方案** —— 上传后直接在前端以可打开的文档形式展示（PDF/DOCX 预览），不强制解析为结构化字段。
   - Resumes.vue —`handleUploadSuccess` 硬编码简历内容，未使用上传返回的`file_url`；需改为保存返回的`file_url` 并跳转/内嵌预览
   - Resumes.vue —`el-upload` 未接`:on-success` 的响应体
   - Resumes.vue — 新增可打开文档预览入口（`iframe`/`embed` 打开`file_url`，或新窗口打开）
   - files.py — 上传接口已返回`file_url` ，可复用
   - resumes.py —`parse_resume_ai` 第 187 行传的是`"Candidate: {name}, Job: {title}"` 假文本，需改为读取真实文件内容（PDF/DOCX 文本抽取，供 AI 诊断使用；展示仍走预览）
   - schemas/resume.py —`ResumeCreate` 需接收`file_url/file_name` （模型 resume.py 已有字段）

4.3 完整度按实际内容量动态更新 现算法只判断"有没有"，不判断"有多少"，且创建时写死 80。
   - resumes.py —`calculate_completeness` 需按字段填充率/条目数/描述长度加权
   - resumes.py — 创建时`completeness=80` 写死
   - Resumes.vue — 展示位（逻辑无需改，改后端即可）

4.4 进入 AI 诊断后无法返回简历中心 ResumeAnalysis.vue 整个页面没有返回入口；对照 ResumeEdit.vue 已有"← 返回简历列表"。需补返回按钮/面包屑。

4.5 AI 智能诊断接入 AI 模型 后端返回的是硬编码字典，前端还有一份硬编码的三档问题列表。
   - resumes.py —`optimize_resume_ai` 全为固定值，未调用`ai_provider`
   - provider.py — 可参照`parse_resume` 增加`optimize_resume` 方法（含 mock 回退）
   - ResumeAnalysis.vue — "严重/中等/建议"三档为写死 HTML，需改为渲染`improvements` /`suggested_modifications`
   - config.py —`AI_MODE` 默认`mock` ，需配置`LLM_API_KEY` 才走真实模型
   - **决策（已定）：接入真实 LLM**（见文末「决策（已确认）」）—— 简历诊断、模拟面试评分/报告、学习路线生成统一走真实模型，保留 mock 作为不可达时的回退

## 新增 6 · 模拟面试（按 JD + 简历生成）

当前只用`job_id` 取岗位标题， 完全忽略`resume_id` ，也没有 JD 输入框。
   - **决策（已定）：JD 来源「两者都支持」** —— 既可从所选岗位自动带出 JD，也支持用户手动粘贴/编辑
   - InterviewCreate.vue — 表单需新增"岗位 JD"输入区（选中岗位后自动填充，可手动修改）
   - InterviewCreate.vue — 提交时需带上 JD 文本
   - interviews.py —`create_interview` 未读取`req.resume_id` （schema 里 已有该字段 ），需加载简历结构化内容 + JD 一起送AI
   - provider.py —`generate_question` 入参缺少简历/JD 上下文

附带发现两处真实 Bug（阻断功能）：
   - 路由不匹配：路由定义为`/personal/interviews/:id/room` （ router/index.ts ），但两处跳转写的是`/session` （InterviewCreate.vue 、 InterviewsList.vue ）→ 进入面试间会 404
   - 评分与报告恒为 mock： provider.py 的`evaluate_answer` /`generate_report` 直接返回假数据，不调用 LLM

## 新增 8 · 学习路线（按 JD 自动生成 + 分阶段）

   - **决策（已定）：JD 来源「两者都支持」** —— 从目标岗位自动带出 JD，同时允许手动粘贴/编辑
   - personal.py —`regenerate_learning_plan` 写死`"Java后端开发工程师"` ，未取用户目标岗位/JD
   - provider.py —`generate_learning_plan` 完全忽略入参，恒返回 mock 任务
   - personal.py —`get_current_learning_plan` 返回扁平任务，无阶段字段
   - LearningRoadmap.vue — 当前"阶段 N"只是数组下标，需改为真正按阶段分组展示待办
   - 数据模型参考 learning.py （如需加 stage 字段）

## 优化 1 · 工作台目标岗位与个人档案对齐

两侧数据同源（都来自`career_preference.target_job_title` ），真正的断点是 登录后缓存的用户信息不会随档案保存刷新 。
   - 左上角展示位： PersonalLayout.vue （侧边用户卡）/ Dashboard.vue （Hero 标题）
   - 保存后未刷新： Profile.vue —`handleSave` 后需调用 authStore.fetchCurrentUser()
   - 后端取值： auth.py （`/auth/me` ）、 personal.py （dashboard）

## 优化 9 · 消息中心常态红点

Navbar.vue —`<el-badge is-dot>` 无条件显示红点。改为按未读数控制（可用`getNotifications` 统计`read=false` 数量），或直接去掉红点。

## 优化 10 · 标题栏用户名随档案更新（当前被注释）

   - Navbar.vue 与 PersonalLayout.vue 读`authStore.user?.name`
   - 同优化 1，需在档案保存后刷新`authStore` （后端 auth.py 已返回`profile.name` ）

## 优化 12 · 注册必填项调整（姓名/邮箱/密码/确认密码）

当前注册表单 没有姓名字段 ，后端用邮箱前缀当姓名。
   - RegisterPersonal.vue — 表单需新增"姓名"输入； form 定义 与 校验逻辑 需同步
   - schemas/auth.py —`RegisterPersonalRequest` 增加`name` ，确认必填项
   - auth.py — 用`req.name` 初始化`PersonalProfile.name` ，替换`email.split("@")[0]`
   - 顺带修复：注册成功跳转`/personal/onboarding` （ RegisterPersonal.vue:119 ）与路由`/onboarding` （ router/index。ts:97 ）不一致，会跳 404

## 决策（已确认）

1. **新增 4.2 · 上传简历展示方式**：采用「**预览**」方案 —— 直接上传至前端显示为可打开的文档。
2. **AI 接入范围**：接入「**真实 LLM**」—— 简历诊断、模拟面试评分/报告、学习路线生成统一接入真实模型；`AI_MODE` 切换为 `real` 并配置 `LLM_API_KEY`，不可达时回退 mock。
3. **新增 6/8 · JD 来源**：「**两者都支持**」—— 既可从所选岗位自动带出 JD，也支持用户手动粘贴/编辑。
4. **AI-KEY 页面配置（2026-09-30）**：「**方案 A 系统级全局配置**」—— 配置存 `system_settings` 表，DB > .env > 默认，登录前可初始化（首次匿名可写，之后仅管理员可改）；适配源码自部署场景，方案 B（每用户独立 Key）已否决。

> 以上决策已确认，**已于本轮全部执行完成**（见文末「执行结果」）。

---

# 执行结果（本轮已完成）

## 新增 4 · 简历中心 ✅

- **4.1 简历优化功能**：新增 `POST /resumes/{id}/optimize/apply` 端点（AI 改写并落库）；`api/index.ts` 新增 `applyOptimization`；`Resumes.vue` 卡片新增「AI 一键优化」按钮，`ResumeAnalysis.vue` 新增「应用优化建议」。
- **4.2 上传本地简历 → 预览**：`Resumes.vue` 的 `handleUploadSuccess` 改为读取真实上传响应 `data.file_url/file_name` 创建简历；新增文档预览弹窗（`iframe` 打开 `file_url`，可新窗口打开）；卡片展示上传文件名可点击预览。
- **4.3 完整度动态计算**：重写 `calculate_completeness`，按「模块存在性 + 条目数量 + 描述字数 + 技能佐证」加权；移除创建时写死的 80，并修复「插入子表后未刷新关系集合导致完整度偏低」的缺陷。
- **4.4 返回简历中心**：`ResumeAnalysis.vue` 顶部新增「← 返回简历中心」。
- **4.5 AI 诊断接入真实 LLM**：`optimize_resume_ai` 改为调用 `ai_provider.optimize_resume`；`ResumeAnalysis.vue` 三档问题列表改为动态渲染 `improvements` / `suggested_modifications`。

## 新增 6 · 模拟面试（JD + 简历）✅

- `InterviewCreate.vue` 新增「岗位 JD」输入区，选择岗位后**自动带出**，支持**手动修改**；提交时携带 `jd_text`，并优先选择默认简历。
- `interviews.py` 的 `create_interview` 现读取 `resume_id`（未选则回退默认简历）与 `jd_text`，出题/评分/报告均注入 JD 与简历上下文；新增 `resume_id` / `jd_text` 字段及启动期安全迁移。
- `provider.py` 的 `generate_question` / `evaluate_answer` / `generate_report` 已接入真实 LLM（含 mock 回退）。
- **修复路由 404**：`InterviewCreate.vue`、`InterviewsList.vue` 的 `/session` 已改为与路由一致的 `/room`。

## 新增 8 · 学习路线（JD + 分阶段）✅

- `regenerate_learning_plan` 改为按用户目标岗位 / 传入 JD 生成，并参考最近一次面试薄弱项；`generate_learning_plan` 接入真实 LLM。
- `LearningTask` 新增 `stage` 字段（含迁移）；`get_current_learning_plan` 返回 `stages` 分阶段聚合。
- `LearningRoadmap.vue` 改为**按阶段分组展示待办**，并新增「依据 JD 生成」弹窗。

## 学习路线增强（2026-09-30）✅

- **模板库混合架构**：新增 `app/data/learning_path_templates.py`（5 个 AI 岗位，源自 `docs/references/AI岗位学习路线与规划.md`），任务带产出物/推荐资源/建议周期；命中模板用骨架 + 薄弱项个性化，未命中回退 LLM（prompt 已要求同结构输出）。`LearningTask` 新增 `deliverable`/`resources_json`/`estimated_weeks` 字段（ensure_schema 迁移）。
- **能力分闭环**：打卡/进度到 100% 均真实发放 `UserCompetency` +2 并写 `CompetencyHistory`（PRACTICE），重复完成幂等；前端文案如实显示实际加分。
- **进度可记录**：前端接入 PATCH `updateTaskProgress` + 进度滑块，中间进度不再只能 0/100；新增 IN_PROGRESS「攻坚中」状态。
- 详见 [update_log.md](./update_log.md) 2026-09-30 条目。

## 优化 1 / 10 · 工作台目标岗位与用户名对齐 ✅

- `Profile.vue` 保存后调用 `authStore.fetchCurrentUser()`，顶部导航与侧边栏的目标岗位、姓名即时刷新。

## 优化 9 · 消息中心红点 ✅

- `Navbar.vue` 红点改为**仅在有未读消息时显示**，否则为普通铃铛图标。

## 优化 12 · 注册必填项 ✅

- `RegisterPersonal.vue` 新增「真实姓名」必填输入与校验；`RegisterPersonalRequest` 新增 `name`（必填）；`auth.py` 用 `req.name` 初始化档案。
- 顺带修复注册成功跳转 `/personal/onboarding` → `/onboarding`（原会 404）。

## AI 引擎配置向导（登录前自配置 API-KEY/URL）✅

- **方案（已定）：方案 A 系统级全局配置**——适配"他人下载源码本地自部署"场景：每个部署实例一份全局配置存本地库，天然即"部署者自己的 Key"；方案 B（每用户独立配置）因需改造 13 处调用点透传身份、且与"登录前配置"矛盾，已否决。
- **后端**：`system_settings` 键值表 + `services/ai_settings.py`（优先级 DB > .env > 默认，缓存 + 保存即失效）；`AIProvider` 动态读取生效配置，未配 Key 回退 mock 不变；`public.py` 新增登录前 `GET/PUT /public/ai-settings` 与 `POST /public/ai-settings/test`（首次匿名可写，已配置后仅管理员可改；Base URL 协议校验；Key 掩码回显）；`admin.py` AI 接口从假数据改为读写真实配置。
- **前端**：新增 `/ai-setup` 向导页（服务商预设 + 测试连接）；`Login.vue` 未配置横幅引导 + 底部入口；`AIService.vue` 保存全字段 + 测试连接。
- 详见 [update_log.md](./update_log.md) 2026-09-30 条目。

## 环境与依赖

- **AI 配置优先级（2026-09-30 起）**：`system_settings` 表（页面配置）> `.env`（`LLM_BASE_URL/LLM_API_KEY/LLM_MODEL`）> 代码默认值。自部署用户可在登录页的"AI 引擎配置"向导中直接填 Key，无需改 `.env`、无需重启。
- `AI_MODE` 默认值与 `.env` / `.env.example` 均切换为 `REAL`；未配置 `LLM_API_KEY` 或调用失败时自动回退 mock。
- `requirements.txt` 新增 `pypdf`、`python-docx`（用于 PDF/DOCX 文本抽取）。
  ⚠️ 本机当前无外网，依赖未能安装；`extract_file_text` 已做优雅降级（回退结构化字段文本），AI 诊断不受阻断。联网后执行 `pip install -r backend/requirements.txt` 即可启用文件文本抽取。

## 验证情况

- 后端：全量字节编译通过；端到端冒烟（注册→诊断→优化→JD+简历建面→答题→报告→分阶段学习路线→按 JD 重生成→消息）全部 200。
- 前端：`npm run build`（含 `vue-tsc` 类型检查）通过。