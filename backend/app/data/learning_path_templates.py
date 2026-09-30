"""岗位学习路线模板库。

来源：docs/references/AI岗位学习路线与规划.md（基于 2026 年 8 月真实招聘 JD 整理）。
用途：当目标岗位命中模板时，以模板骨架（阶段/模块/产出物/推荐资源/周期）为基础，
再交给 LLM 根据面试薄弱项做个性化裁剪；未命中模板时回退纯 LLM 动态生成。

数据结构约定：
- ROLE_TEMPLATES: list，每个岗位含 match_keywords（岗位名/JD 关键词，按顺序优先匹配）、
  role_name、total_duration、stages。
- 每个 stage 含 stage（阶段名）、estimated_weeks（建议周期，"持续"用 0 表示）、tasks。
- 每个 task 字段与 LearningTask 对齐：title / competency_name / priority / reason /
  action_type / deliverable（产出物）/ resources（推荐资源列表）/ estimated_weeks。
"""

ROLE_TEMPLATES = [
    {
        "role_name": "AI Agent 应用开发工程师（智能内控方向）",
        "match_keywords": ["内控", "风控", "智能内控"],
        "total_duration": "6-9 个月",
        "stages": [
            {
                "stage": "第一阶段 · 风控业务基础",
                "estimated_weeks": 5,
                "tasks": [
                    {"title": "掌握反欺诈、反洗钱、信用评估与合规审计体系", "competency_name": "风控业务", "priority": "HIGH", "action_type": "READING", "deliverable": "风控知识图谱", "reason": "风控/内控岗位的业务地基，面试必考风险识别全流程", "estimated_weeks": 2, "resources": ["《智能风控：原理、算法与工程实践》", "《反欺诈体系》"]},
                    {"title": "熟悉电商资金、交易、内容与大促保障场景", "competency_name": "风控业务", "priority": "HIGH", "action_type": "READING", "deliverable": "场景分析报告", "reason": "业务属性极强的岗位，需展示对真实风险场景的理解", "estimated_weeks": 1, "resources": ["《智能风控：原理、算法与工程实践》"]},
                    {"title": "规则引擎实战：Drools/Easy Rules 与自研引擎", "competency_name": "规则引擎", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "规则决策系统", "reason": "传统规则策略 + LLM 推理融合决策是该岗位核心考点", "estimated_weeks": 1, "resources": ["Drools 官方文档", "Easy Rules GitHub"]},
                    {"title": "风控特征工程、异常检测与图计算", "competency_name": "数据分析", "priority": "MEDIUM", "action_type": "COURSE", "deliverable": "风险识别模型", "reason": "打通交易、资金、用户多维度数据建模的能力要求", "estimated_weeks": 1, "resources": ["《智能风控：原理、算法与工程实践》"]},
                ],
            },
            {
                "stage": "第二阶段 · 大数据与分布式",
                "estimated_weeks": 6,
                "tasks": [
                    {"title": "大数据栈：Hive、Spark、Flink、Kafka、HBase", "competency_name": "大数据", "priority": "HIGH", "action_type": "COURSE", "deliverable": "实时风控数据平台", "reason": "JD 硬性要求大数据分布式后端能力", "estimated_weeks": 2, "resources": ["《Spark 快速大数据分析》", "《Flink 基础教程》"]},
                    {"title": "Flink SQL、CEP 复杂事件处理与窗口计算", "competency_name": "实时计算", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "实时风险预警系统", "reason": "双十一峰值海量交易要求毫秒级实时风险识别", "estimated_weeks": 2, "resources": ["《Flink 基础教程》", "Flink 官方文档"]},
                    {"title": "Redis Cluster、Elasticsearch、ClickHouse 分布式存储", "competency_name": "分布式存储", "priority": "MEDIUM", "action_type": "COURSE", "deliverable": "高性能查询层", "reason": "支撑高并发低延迟的风控查询链路", "estimated_weeks": 1, "resources": ["Redis/Elasticsearch/ClickHouse 官方文档"]},
                    {"title": "Go 后端：Gin/Beego、并发、微服务与 gRPC", "competency_name": "Go", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "高并发风控服务", "reason": "JD 要求 Python + Golang 双语言精通", "estimated_weeks": 1, "resources": ["《Go 语言实战》", "《Go 微服务实战》"]},
                ],
            },
            {
                "stage": "第三阶段 · LLM 与风控融合",
                "estimated_weeks": 7,
                "tasks": [
                    {"title": "LLM 基础：Transformer、GPT 架构与 Prompt 工程", "competency_name": "LLM 应用", "priority": "HIGH", "action_type": "COURSE", "deliverable": "风控问答机器人", "reason": "结合 LLM 构建风险识别模型的入门要求", "estimated_weeks": 2, "resources": ["Hugging Face 教程", "Transformer 论文"]},
                    {"title": "模型微调实战：SFT 指令微调、LoRA、QLoRA", "competency_name": "LLM 微调", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "风控垂类模型", "reason": "JD 明确要求 LLM 微调实战与风控专属垂类模型构建", "estimated_weeks": 2, "resources": ["《LoRA》论文", "LLaMA-Factory 项目", "Hugging Face 教程"]},
                    {"title": "Post-training 领域后训练与知识注入", "competency_name": "LLM 微调", "priority": "MEDIUM", "action_type": "READING", "deliverable": "领域适配模型", "reason": "领域后训练是构建风控垂类模型的进阶路径", "estimated_weeks": 1, "resources": ["LLaMA-Factory 项目"]},
                    {"title": "风控知识库 RAG：法规检索与案例匹配", "competency_name": "RAG", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "智能合规助手", "reason": "JD 要求风控知识库 RAG 全链路落地", "estimated_weeks": 2, "resources": ["LlamaIndex 官方教程", "《Building LLM Apps》"]},
                ],
            },
            {
                "stage": "第四阶段 · Agent 与 Workflow",
                "estimated_weeks": 5,
                "tasks": [
                    {"title": "Agent 编排：多步骤风控审计与处置 Workflow", "competency_name": "Agent 开发", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "智能风控 Agent", "reason": "企业级 Agent 与多步骤智能 Workflow 编排是岗位核心职责", "estimated_weeks": 2, "resources": ["LangGraph 官方文档", "LangChain Academy"]},
                    {"title": "风险规则库、合规文档库、历史案例库引擎", "competency_name": "知识库", "priority": "MEDIUM", "action_type": "PROJECT", "deliverable": "风控知识引擎", "reason": "打通知识库与 Agent 决策链路", "estimated_weeks": 1, "resources": ["LlamaIndex 官方教程"]},
                    {"title": "风险识别 → 智能分析 → 自动处置闭环", "competency_name": "Agent 开发", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "自动化风控系统", "reason": "展示端到端业务闭环落地能力", "estimated_weeks": 1, "resources": ["LangGraph 官方文档"]},
                    {"title": "风险归因、决策解释与证据链可解释性", "competency_name": "可解释性", "priority": "MEDIUM", "action_type": "READING", "deliverable": "可解释风控模型", "reason": "JD 明确要求合规判断可解释性方案", "estimated_weeks": 1, "resources": ["《智能风控：原理、算法与工程实践》"]},
                ],
            },
            {
                "stage": "第五阶段 · 工程化与高并发",
                "estimated_weeks": 4,
                "tasks": [
                    {"title": "规则引擎 + LLM 融合决策与延迟优化", "competency_name": "系统设计", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "毫秒级决策引擎", "reason": "高并发低延迟架构优化是岗位硬性要求", "estimated_weeks": 1, "resources": ["《Designing Data-Intensive Applications》"]},
                    {"title": "限流熔断、弹性伸缩与容量规划", "competency_name": "高并发", "priority": "HIGH", "action_type": "COURSE", "deliverable": "大促风控方案", "reason": "双十一大促保障场景的直接考点", "estimated_weeks": 1, "resources": ["Google SRE 书籍"]},
                    {"title": "误判率、漏判率、召回率评测体系", "competency_name": "评测体系", "priority": "MEDIUM", "action_type": "PROJECT", "deliverable": "风控效果评测平台", "reason": "风控效果量化是业务价值证明的关键", "estimated_weeks": 1, "resources": ["《智能风控：原理、算法与工程实践》"]},
                    {"title": "完成 1 次智能内控方向模拟面试并复盘", "competency_name": "综合表达", "priority": "HIGH", "action_type": "INTERVIEW_PRACTICE", "deliverable": "面试薄弱项清单", "reason": "检验风控业务 + LLM 融合 + 高并发的综合表达", "estimated_weeks": 1, "resources": []},
                ],
            },
        ],
    },
    {
        "role_name": "AI Agent 研发工程师（AI Native 创新小组）",
        "match_keywords": ["agent 研发", "ai native", "创新小组"],
        "total_duration": "6-9 个月",
        "stages": [
            {
                "stage": "第一阶段 · 全栈基础夯实",
                "estimated_weeks": 8,
                "tasks": [
                    {"title": "系统设计：设计模式、架构原则、微服务与 DDD", "competency_name": "系统设计", "priority": "HIGH", "action_type": "READING", "deliverable": "Agent 平台架构设计", "reason": "中高级研发岗要求独立架构方案设计能力", "estimated_weeks": 2, "resources": ["《Head First Design Patterns》", "《Clean Architecture》", "《Building Microservices》"]},
                    {"title": "状态机：FSM、HFSM、行为树与 Petri 网", "competency_name": "状态机", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "复杂工作流引擎", "reason": "LangGraph 状态机工作流是岗位核心技术栈", "estimated_weeks": 2, "resources": ["LangGraph 官方文档"]},
                    {"title": "分布式基础：消息队列、分布式锁与 CAP", "competency_name": "分布式系统", "priority": "MEDIUM", "action_type": "COURSE", "deliverable": "分布式任务调度系统", "reason": "支撑多智能体协同调度的工程底座", "estimated_weeks": 2, "resources": ["《分布式系统概念与设计》"]},
                    {"title": "数据存储：关系型、NoSQL、向量与时序数据库", "competency_name": "数据存储", "priority": "MEDIUM", "action_type": "COURSE", "deliverable": "多模态数据存储方案", "reason": "记忆持久化体系依赖多模态存储选型", "estimated_weeks": 2, "resources": ["《Designing Data-Intensive Applications》"]},
                ],
            },
            {
                "stage": "第二阶段 · Agent 核心研发",
                "estimated_weeks": 8,
                "tasks": [
                    {"title": "从零设计 Agent 系统（不依赖现成框架）", "competency_name": "Agent 架构", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "自研 Agent 框架原型", "reason": "JD 明确要求不局限调用开源框架的自主设计能力", "estimated_weeks": 3, "resources": ["ReAct 论文", "Reflexion 论文", "AutoGPT 源码"]},
                    {"title": "分层记忆体系：工作/短期/长期记忆与压缩检索", "competency_name": "记忆系统", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "记忆持久化系统", "reason": "长短时分层记忆持久化是岗位核心技能", "estimated_weeks": 2, "resources": ["《Generative Agents》论文", "LlamaIndex 记忆模块"]},
                    {"title": "通用工具网关：注册、权限、链路追踪与熔断", "competency_name": "工具调用", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "企业级工具网关", "reason": "Function Calling + MCP 协议开发通用工具网关", "estimated_weeks": 2, "resources": ["MCP 协议官方文档", "OpenAI Function Calling 文档"]},
                    {"title": "多智能体通信、任务分配与共识机制", "competency_name": "多智能体", "priority": "MEDIUM", "action_type": "PROJECT", "deliverable": "多 Agent 协作平台", "reason": "多智能体通信与协同调度是中高级岗差异化要求", "estimated_weeks": 1, "resources": ["MetaGPT 论文", "CAMEL 论文"]},
                ],
            },
            {
                "stage": "第三阶段 · 可靠性工程",
                "estimated_weeks": 6,
                "tasks": [
                    {"title": "Trajectory 轨迹追踪与决策链路可视化", "competency_name": "可观测性", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "全链路追踪系统", "reason": "JD 明确要求轨迹追踪、可观测与回放机制", "estimated_weeks": 2, "resources": ["LangSmith 文档", "OpenTelemetry 文档"]},
                    {"title": "回放调试：状态回滚、断点调试与沙箱执行", "competency_name": "调试观测", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "任务回放平台", "reason": "直面大模型不确定性，异常复现是核心能力", "estimated_weeks": 2, "resources": ["《Chaos Engineering》"]},
                    {"title": "埋点设计、指标采集与日志分析", "competency_name": "可观测性", "priority": "MEDIUM", "action_type": "COURSE", "deliverable": "可观测性平台", "reason": "线上运营闭环的基础设施能力", "estimated_weeks": 1, "resources": ["Prometheus + Grafana 文档"]},
                    {"title": "自动降级、异常兜底与人工接管机制", "competency_name": "高可用", "priority": "MEDIUM", "action_type": "READING", "deliverable": "高可用保障方案", "reason": "监控告警、兜底与人工接管是 JD 硬性要求", "estimated_weeks": 1, "resources": ["Google SRE 书籍"]},
                ],
            },
            {
                "stage": "第四阶段 · 评测与运营",
                "estimated_weeks": 5,
                "tasks": [
                    {"title": "分层评测：任务级 + 步骤级指标拆解与归因", "competency_name": "评测体系", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "评测体系设计", "reason": "精细化分层指标是该岗位的关键差异化要求", "estimated_weeks": 2, "resources": ["LangSmith Evaluation", "RAGAS 文档"]},
                    {"title": "离线评测 + 线上观测双向驱动迭代", "competency_name": "数据驱动", "priority": "MEDIUM", "action_type": "PROJECT", "deliverable": "数据驱动优化方案", "reason": "线上运营与策略迭代闭环思维", "estimated_weeks": 1, "resources": ["Google SRE 书籍"]},
                    {"title": "Token 成本核算与推理优化", "competency_name": "成本管控", "priority": "MEDIUM", "action_type": "READING", "deliverable": "成本优化报告", "reason": "成本/复杂度/收益综合判断是方案取舍能力基础", "estimated_weeks": 1, "resources": ["vLLM 文档"]},
                    {"title": "Agent vs 固定流程 vs 单次调用选型框架", "competency_name": "方案设计", "priority": "HIGH", "action_type": "INTERVIEW_PRACTICE", "deliverable": "方案选型方法论", "reason": "面试深挖题：方案取舍与需求评估思维", "estimated_weeks": 1, "resources": []},
                ],
            },
            {
                "stage": "第五阶段 · 前沿跟踪（持续）",
                "estimated_weeks": 0,
                "tasks": [
                    {"title": "每日跟踪 arXiv 最新 Agent 论文并精读", "competency_name": "前沿技术", "priority": "MEDIUM", "action_type": "READING", "deliverable": "论文精读笔记", "reason": "AI 领域迭代极快，持续学习是共性要求", "estimated_weeks": 0, "resources": ["arXiv cs.AI", "ReAct/Reflexion/MetaGPT 论文"]},
                    {"title": "参与 LangChain/AutoGPT/MetaGPT 开源社区", "competency_name": "开源协作", "priority": "LOW", "action_type": "PROJECT", "deliverable": "开源贡献记录", "reason": "展示技术影响力与工程规范沉淀", "estimated_weeks": 0, "resources": ["GitHub 开源项目"]},
                ],
            },
        ],
    },
    {
        "role_name": "AI Agent 开发（滴滴）",
        "match_keywords": ["滴滴"],
        "total_duration": "5-7 个月",
        "stages": [
            {
                "stage": "第一阶段 · 双语言基础",
                "estimated_weeks": 8,
                "tasks": [
                    {"title": "Python 进阶：OOP、函数式、异步与性能优化", "competency_name": "Python", "priority": "HIGH", "action_type": "COURSE", "deliverable": "Python 工具库", "reason": "所有岗位的基础语言要求", "estimated_weeks": 2, "resources": ["《Fluent Python》", "Python 官方文档"]},
                    {"title": "Java 核心：Spring Boot/Cloud、MyBatis、JVM 调优", "competency_name": "Java", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "微服务后端系统", "reason": "JD 要求 Java/Go 分布式后端双重能力", "estimated_weeks": 3, "resources": ["《Spring 实战》", "《深入理解 Java 虚拟机》", "《Java 并发编程实战》"]},
                    {"title": "Go 基础：Goroutine、Channel、Gin 与并发模式", "competency_name": "Go", "priority": "MEDIUM", "action_type": "COURSE", "deliverable": "高并发服务", "reason": "双栈工程能力的 Go 侧要求", "estimated_weeks": 2, "resources": ["《Go 语言高级编程》", "《Go 并发编程实战》"]},
                    {"title": "数据结构与算法：LeetCode 200+ 与系统设计基础", "competency_name": "算法", "priority": "HIGH", "action_type": "INTERVIEW_PRACTICE", "deliverable": "算法能力达标", "reason": "大厂面试必考环节", "estimated_weeks": 1, "resources": ["LeetCode 热题 100"]},
                ],
            },
            {
                "stage": "第二阶段 · 分布式后端",
                "estimated_weeks": 6,
                "tasks": [
                    {"title": "Spring 全家桶：Boot/Cloud/Data/Security", "competency_name": "Java", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "企业级后端服务", "reason": "MySQL 优化与高并发架构的工程底座", "estimated_weeks": 2, "resources": ["《Spring 实战》"]},
                    {"title": "MySQL 索引优化、分库分表与 Redis 集群", "competency_name": "数据库", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "高性能数据层", "reason": "JD 明确要求 MySQL 优化能力", "estimated_weeks": 2, "resources": ["《高性能 MySQL》", "Redis 官方文档"]},
                    {"title": "RPC、消息队列与分布式事务", "competency_name": "分布式系统", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "分布式电商系统", "reason": "Dubbo/gRPC + Kafka/RocketMQ 是岗位标配", "estimated_weeks": 1, "resources": ["《微服务设计》"]},
                    {"title": "缓存、限流熔断、异步处理与负载均衡", "competency_name": "高并发", "priority": "MEDIUM", "action_type": "COURSE", "deliverable": "高并发架构设计", "reason": "高并发高可用架构要求", "estimated_weeks": 1, "resources": ["Google SRE 书籍"]},
                ],
            },
            {
                "stage": "第三阶段 · Agent 核心开发",
                "estimated_weeks": 6,
                "tasks": [
                    {"title": "Agent 架构：感知-决策-行动闭环与任务拆解", "competency_name": "Agent 架构", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "Agent 核心引擎", "reason": "JD 要求自主设计 Agent 底层核心模块", "estimated_weeks": 2, "resources": ["ReAct 论文", "LangGraph 文档"]},
                    {"title": "Function Calling、MCP 协议与工具注册", "competency_name": "工具调用", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "工具接入平台", "reason": "开发适配业务的工具接入层", "estimated_weeks": 2, "resources": ["MCP 协议官方文档"]},
                    {"title": "工作记忆、episodic 与 semantic 记忆体系", "competency_name": "记忆系统", "priority": "MEDIUM", "action_type": "PROJECT", "deliverable": "记忆管理系统", "reason": "长短时记忆体系与目标规划逻辑", "estimated_weeks": 1, "resources": ["LlamaIndex 记忆模块"]},
                    {"title": "多厂商大模型统一调用层（火山/通义/GPT）", "competency_name": "模型适配", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "多模型网关", "reason": "JD 明确要求多厂商大模型适配", "estimated_weeks": 1, "resources": ["火山引擎/通义千问 API 文档"]},
                ],
            },
            {
                "stage": "第四阶段 · 工程优化",
                "estimated_weeks": 4,
                "tasks": [
                    {"title": "限流、缓存、降级、熔断与超时控制", "competency_name": "服务治理", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "resilient 调用层", "reason": "JD 明确列出限流缓存降级的调用策略", "estimated_weeks": 1, "resources": ["Sentinel 文档", "Resilience4j 文档"]},
                    {"title": "上下文裁剪、分层 Prompt 与模板管理", "competency_name": "Prompt 工程", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "Prompt 管理平台", "reason": "上下文裁剪压缩是岗位工程手段要求", "estimated_weeks": 1, "resources": ["OpenAI Prompt Engineering Guide"]},
                    {"title": "推理延迟优化、批处理与流式输出", "competency_name": "性能优化", "priority": "MEDIUM", "action_type": "COURSE", "deliverable": "高性能推理服务", "reason": "线上服务的延迟与吞吐治理", "estimated_weeks": 1, "resources": ["vLLM 文档"]},
                    {"title": "自我验证、事实核查与引用溯源", "competency_name": "幻觉抑制", "priority": "MEDIUM", "action_type": "READING", "deliverable": "可信 AI 系统", "reason": "幻觉抑制方案是 Agent 落地必备能力", "estimated_weeks": 1, "resources": ["SelfCheckGPT 论文", "RAGAS 文档"]},
                ],
            },
            {
                "stage": "第五阶段 · 前沿技术",
                "estimated_weeks": 3,
                "tasks": [
                    {"title": "CoT/ReAct 多步推理与复杂推理 Agent", "competency_name": "前沿技术", "priority": "MEDIUM", "action_type": "PROJECT", "deliverable": "复杂推理 Agent", "reason": "JD 要求 CoT、ReAct 等前沿技术调研与 POC", "estimated_weeks": 1, "resources": ["CoT 论文", "ReAct 论文"]},
                    {"title": "每月跟踪 arXiv 论文与技术博客", "competency_name": "前沿技术", "priority": "LOW", "action_type": "READING", "deliverable": "技术调研报告", "reason": "持续跟踪 AI 领域最新动态", "estimated_weeks": 1, "resources": ["arXiv cs.AI"]},
                    {"title": "快速原型验证与落地评估", "competency_name": "方案设计", "priority": "MEDIUM", "action_type": "PROJECT", "deliverable": "POC 项目集", "reason": "POC 验证能力是滴滴岗位的显性要求", "estimated_weeks": 1, "resources": []},
                ],
            },
        ],
    },
    {
        "role_name": "AI 应用工程师",
        "match_keywords": ["ai 应用工程师", "应用工程师", "ai 应用开发"],
        "total_duration": "3-6 个月",
        "stages": [
            {
                "stage": "第一阶段 · Python 后端基础",
                "estimated_weeks": 6,
                "tasks": [
                    {"title": "Python 进阶：asyncio、类型注解、装饰器与上下文管理器", "competency_name": "Python", "priority": "HIGH", "action_type": "COURSE", "deliverable": "异步爬虫项目", "reason": "大模型应用层工程开发的基础语言要求", "estimated_weeks": 2, "resources": ["《Fluent Python》", "Python asyncio 官方文档"]},
                    {"title": "FastAPI 深度掌握：依赖注入、中间件、后台任务、WebSocket", "competency_name": "FastAPI", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "RESTful API 服务", "reason": "JD 核心要求 Python Web 服务基础", "estimated_weeks": 2, "resources": ["FastAPI 官方文档", "《FastAPI 现代 Python Web 开发》"]},
                    {"title": "SQLAlchemy、Redis 缓存策略与连接池管理", "competency_name": "数据库", "priority": "MEDIUM", "action_type": "PROJECT", "deliverable": "用户系统 + 缓存层", "reason": "数据层与服务缓存的工程基本功", "estimated_weeks": 1, "resources": ["SQLAlchemy 官方文档", "Redis 官方文档"]},
                    {"title": "Docker 容器化、Gunicorn/Uvicorn 与 Nginx 反代", "competency_name": "部署运维", "priority": "MEDIUM", "action_type": "PROJECT", "deliverable": "项目 Docker 化部署", "reason": "线上生成式 AI 落地经验要求部署能力", "estimated_weeks": 1, "resources": ["Docker 官方文档"]},
                ],
            },
            {
                "stage": "第二阶段 · 大模型应用开发",
                "estimated_weeks": 6,
                "tasks": [
                    {"title": "多厂商 LLM API 统一封装（OpenAI/Claude/国产模型）", "competency_name": "LLM 应用", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "多厂商模型网关原型", "reason": "模型网关搭建是岗位核心职责", "estimated_weeks": 1, "resources": ["OpenAI/Claude API 文档", "通义千问开放平台"]},
                    {"title": "Prompt 工程：系统提示词、Few-shot 与 CoT", "competency_name": "Prompt 工程", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "智能客服机器人", "reason": "Prompt 约束与检索增强是 RAG 全链路前置能力", "estimated_weeks": 1, "resources": ["OpenAI Prompt Engineering Guide", "LangChain Academy"]},
                    {"title": "RAG 全链路：向量库、分块、Embedding 与重排序", "competency_name": "RAG", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "企业知识库问答系统", "reason": "JD 明确要求 RAG 全链路优化", "estimated_weeks": 2, "resources": ["LlamaIndex 官方教程", "《Building LLM Apps》", "Milvus/FAISS 文档"]},
                    {"title": "LangChain/LangGraph 核心：工具调用与记忆管理", "competency_name": "Agent 框架", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "多步骤任务 Agent", "reason": "Agent 编排与多步骤任务自动化", "estimated_weeks": 2, "resources": ["LangChain 官方文档", "LangChain Academy 免费课程"]},
                ],
            },
            {
                "stage": "第三阶段 · 工程化与运维",
                "estimated_weeks": 4,
                "tasks": [
                    {"title": "限流熔断、负载均衡与动态路由", "competency_name": "服务治理", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "模型网关生产级实现", "reason": "JD 要求模型网关的负载均衡、超时重试、故障降级", "estimated_weeks": 1, "resources": ["Envoy/Nginx 文档", "Google SRE 书籍"]},
                    {"title": "离线评测指标、在线 A/B 与回归流水线", "competency_name": "评测体系", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "评测平台", "reason": "评测体系与回归机制是岗位显性要求", "estimated_weeks": 1, "resources": ["LangSmith Evaluation", "RAGAS 文档"]},
                    {"title": "Prometheus + Grafana 全链路监控告警", "competency_name": "可观测性", "priority": "MEDIUM", "action_type": "PROJECT", "deliverable": "全链路监控大盘", "reason": "质量、延迟、成本、失败率四维监控告警", "estimated_weeks": 1, "resources": ["Prometheus + Grafana 文档"]},
                    {"title": "Token 用量统计与推理成本分析", "competency_name": "成本管控", "priority": "MEDIUM", "action_type": "READING", "deliverable": "成本优化方案", "reason": "服务 SLA 治理中的成本控制维度", "estimated_weeks": 1, "resources": ["Google SRE 书籍"]},
                ],
            },
            {
                "stage": "第四阶段 · 项目实战（持续）",
                "estimated_weeks": 0,
                "tasks": [
                    {"title": "多模态 AI 应用：文本 + 图文混合业务", "competency_name": "多模态", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "多模态 AI 应用", "reason": "JD 要求兼顾多模态服务落地经验", "estimated_weeks": 0, "resources": ["OpenAI Vision API 文档"]},
                    {"title": "企业级 Agent 工作流平台：可编排、模块化、可复用", "competency_name": "Agent 框架", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "Agent 工作流平台", "reason": "展示服务架构与工程规范化沉淀能力", "estimated_weeks": 0, "resources": ["LangGraph 文档"]},
                    {"title": "大数据 + AI 融合：Spark/Hive 预处理 + 模型推理流水线", "competency_name": "大数据", "priority": "MEDIUM", "action_type": "PROJECT", "deliverable": "数据 + 推理流水线", "reason": "Spark/Hadoop/Hive 大数据经验是加分项", "estimated_weeks": 0, "resources": ["《Spark 快速大数据分析》"]},
                ],
            },
        ],
    },
    {
        "role_name": "AI Agent 开发工程师",
        "match_keywords": ["agent 开发工程师", "agent 开发", "数字员工", "私有化"],
        "total_duration": "4-6 个月",
        "stages": [
            {
                "stage": "第一阶段 · Agent 基础理论",
                "estimated_weeks": 4,
                "tasks": [
                    {"title": "ReAct、CoT、ToT、Reflexion 推理范式", "competency_name": "Agent 架构", "priority": "HIGH", "action_type": "READING", "deliverable": "手写一个 ReAct Agent", "reason": "Agent 核心能力（任务规划/反思纠错）的理论基础", "estimated_weeks": 1, "resources": ["ReAct 论文", "Reflexion 论文"]},
                    {"title": "短时/长时/实体分层记忆系统", "competency_name": "记忆系统", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "分层记忆模块", "reason": "长短记忆是 Agent 核心能力之一", "estimated_weeks": 1, "resources": ["LlamaIndex 记忆模块", "《Generative Agents》论文"]},
                    {"title": "Function Calling、MCP 协议与工具注册发现", "competency_name": "工具调用", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "3-5 个自定义工具", "reason": "自定义 Tool 插件开发（OA/ERP/业务数据库对接）", "estimated_weeks": 1, "resources": ["MCP 协议官方文档", "OpenAI Function Calling 文档"]},
                    {"title": "目标分解、子任务调度与依赖管理", "competency_name": "任务规划", "priority": "MEDIUM", "action_type": "PROJECT", "deliverable": "任务规划器", "reason": "任务规划是 Agent 落地的调度核心", "estimated_weeks": 1, "resources": ["LangGraph 文档"]},
                ],
            },
            {
                "stage": "第二阶段 · 框架深度掌握",
                "estimated_weeks": 5,
                "tasks": [
                    {"title": "LangChain 源码阅读与二次封装", "competency_name": "LangChain", "priority": "HIGH", "action_type": "READING", "deliverable": "通用组件底座", "reason": "JD 要求 LangChain/LlamaIndex 源码级二次封装", "estimated_weeks": 2, "resources": ["LangChain GitHub 源码", "LangChain Cookbook"]},
                    {"title": "LlamaIndex：索引构建、查询引擎与 RAG Pipeline", "competency_name": "LlamaIndex", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "企业文档智能问答系统", "reason": "向量库检索优化与 RAG 全链路能力", "estimated_weeks": 1, "resources": ["LlamaIndex 官方教程"]},
                    {"title": "LangGraph：状态机工作流与条件分支编排", "competency_name": "LangGraph", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "复杂业务流程 Agent", "reason": "多智能体协同与业务流程编排", "estimated_weeks": 1, "resources": ["LangGraph 官方文档"]},
                    {"title": "国产大模型私有化部署与统一调用层", "competency_name": "模型适配", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "多模型统一调用层", "reason": "JD 核心要求国产大模型私有化部署与兼容适配", "estimated_weeks": 1, "resources": ["通义千问 GitHub", "ChatGLM GitHub", "讯飞星火开放平台"]},
                ],
            },
            {
                "stage": "第三阶段 · 业务闭环与部署",
                "estimated_weeks": 4,
                "tasks": [
                    {"title": "OA/ERP 系统对接与业务 API 封装", "competency_name": "业务插件", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "企业自动化工作流", "reason": "企业级落地 Agent 与业务自动化数字员工方向", "estimated_weeks": 1, "resources": ["MCP 协议官方文档"]},
                    {"title": "Hybrid Search、Reranking 与多路召回", "competency_name": "RAG", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "高精度检索系统", "reason": "向量库检索优化、分块策略、重排是显性要求", "estimated_weeks": 1, "resources": ["LlamaIndex 官方教程", "Milvus 文档"]},
                    {"title": "自我一致性检查、事实验证与引用溯源", "competency_name": "幻觉抑制", "priority": "MEDIUM", "action_type": "PROJECT", "deliverable": "幻觉率 < 5% 的问答系统", "reason": "JD 明确要求幻觉抑制方案", "estimated_weeks": 1, "resources": ["SelfCheckGPT 论文", "RAGAS 文档"]},
                    {"title": "Docker Compose、K8s 基础与 CI/CD", "competency_name": "部署运维", "priority": "MEDIUM", "action_type": "PROJECT", "deliverable": "生产环境部署方案", "reason": "要求独立部署服务能力与 Docker/Linux 基础运维", "estimated_weeks": 1, "resources": ["Docker 官方文档", "《Kubernetes 权威指南》"]},
                ],
            },
            {
                "stage": "第四阶段 · 量化评测与交付",
                "estimated_weeks": 3,
                "tasks": [
                    {"title": "任务成功率、幻觉率、召回精度、响应延迟指标", "competency_name": "评测体系", "priority": "HIGH", "action_type": "PROJECT", "deliverable": "自动化评测平台", "reason": "JD 要求 Agent 效果量化指标", "estimated_weeks": 1, "resources": ["RAGAS 文档", "LangSmith Evaluation"]},
                    {"title": "实验设计、指标对比与统计显著性检验", "competency_name": "A/B 测试", "priority": "MEDIUM", "action_type": "PROJECT", "deliverable": "线上实验报告", "reason": "线上 A/B 评测与迭代闭环", "estimated_weeks": 1, "resources": ["Google SRE 书籍"]},
                    {"title": "需求分析、方案设计、POC 验证与落地交付", "competency_name": "客户交付", "priority": "HIGH", "action_type": "INTERVIEW_PRACTICE", "deliverable": "完整项目案例", "reason": "必须有生产上线项目，弱化纯 Demo 竞争力", "estimated_weeks": 1, "resources": []},
                    {"title": "完成 1 次 Agent 开发方向模拟面试并复盘", "competency_name": "综合表达", "priority": "HIGH", "action_type": "INTERVIEW_PRACTICE", "deliverable": "面试薄弱项清单", "reason": "检验业务闭环 + 独立部署的综合表达", "estimated_weeks": 0, "resources": []},
                ],
            },
        ],
    },
]


def match_role_template(job_title: str, jd_text: str = None):
    """按岗位名/JD 关键词匹配模板，命中返回模板 dict，否则返回 None。

    匹配顺序即 ROLE_TEMPLATES 顺序：内控/风控/滴滴等特化岗位优先于泛化岗位，
    避免"AI Agent 开发"误吞"AI Agent 开发（滴滴）"。
    """
    if not job_title:
        return None
    haystack = f"{job_title} {jd_text or ''}".lower()
    for tpl in ROLE_TEMPLATES:
        for kw in tpl["match_keywords"]:
            if kw in haystack:
                return tpl
    return None
