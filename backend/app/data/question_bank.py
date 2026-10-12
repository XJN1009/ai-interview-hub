"""结构化面试题库种子数据（纯数据，不依赖 ORM 模型）。

字段说明：
  job_category   适用岗位大类，与 Job.category 对齐；"通用" 表示跨岗位通用
  question_type  PROFESSIONAL 专业题 / GENERAL 通用题 / STRESS 压力题
  skill_name     考察技能（通用题为"综合素养"）
  stage          面试阶段（专业基础 / 深度探究 / 项目深挖 / 系统设计 / 综合素养 / 压力应对）
  difficulty     EASY / MEDIUM / HARD
  text           题干
  reference_points  参考答案要点（逐题复盘时与候选人作答对照）
  hints          临场答题提示
  time_limit_sec 逐题建议限时（秒）

配比设计参考：专业题 : 通用题 : 压力题 = 5 : 3 : 2（可在组卷引擎按面试模式覆盖）。
"""

QUESTION_BANK_SEED = [
    # ================= === 后端开发 · Java 与并发 === =================
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Java并发",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "请结合底层机制说明 Java 中 volatile 关键字的作用原理。它能保证原子性吗？为什么？",
        "reference_points": [
            "可见性：写操作刷新主内存、读操作从主内存加载，依赖内存屏障（StoreLoad 等）禁止指令重排",
            "有序性：通过插入内存屏障建立 happens-before 关系，典型如双重检查锁单例必须加 volatile",
            "不保证原子性：i++ 是读-改-写三步，需用 AtomicInteger/synchronized/LongAdder",
            "适用场景：状态标志位、DCL 单例；不适用：计数、复合条件判断"
        ],
        "hints": "先讲内存模型与屏障，再明确区分可见性与原子性，最后给出适用场景"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Java并发",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "请聊聊 AQS 的核心设计思想。ReentrantLock 公平锁与非公平锁在实现上有什么区别，为什么默认选择非公平？",
        "reference_points": [
            "核心三要素：volatile int state 表示同步状态、CLH 变体的 FIFO 双向等待队列、模板方法式的 tryAcquire/tryRelease 由子类实现",
            "获取失败后通过 LockSupport.park 挂起线程，前驱节点出队或被唤醒后重试",
            "非公平锁在 tryAcquire 时先直接 CAS 抢一次，不检查队列；公平锁需 hasQueuedPredecessors 判断",
            "非公平性能更优：省去线程唤醒与上下文切换的窗口期，吞吐显著更高，代价是可能的队列饥饿"
        ],
        "hints": "建议画出 state + 队列的结构，再对比两种锁的源码分支差异"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Java并发",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "ThreadPoolExecutor 有哪些核心参数？生产环境中你如何确定线程池大小，为什么阿里规约禁止用 Executors 直接创建？",
        "reference_points": [
            "七大参数：corePoolSize、maximumPoolSize、keepAliveTime、unit、workQueue、threadFactory、RejectedExecutionHandler",
            "执行顺序：核心线程 → 队列 → 非核心线程 → 拒绝策略，注意与直觉不同的地方是先入队再扩容",
            "容量估算：CPU 密集型 N+1，IO 密集型 N×(1+等待时间/计算时间)，最终以压测 TP99 与 CPU 利用率校准",
            "Executors 风险：newFixedThreadPool/newSingleThreadExecutor 用无界 LinkedBlockingQueue 导致 OOM；newCachedThreadPool 允许 Integer.MAX_VALUE 线程数"
        ],
        "hints": "结合一个你实际调过的线程池参数与被压测出来的数据来说明"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Java并发",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "synchronized 的锁升级过程是怎样的？偏向锁、轻量级锁、重量级锁各自的适用场景与撤销代价是什么？",
        "reference_points": [
            "对象头 Mark Word 存储锁状态，升级路径：无锁 → 偏向锁 → 轻量级锁 → 重量级锁",
            "偏向锁：只有一个线程访问，记录线程 ID，再次进入只需比较，无 CAS 开销；批量重撤销/单线程撤销",
            "轻量级锁：多线程交替执行（无真正竞争），CAS 将 Mark Word 复制到栈帧 Lock Record，自旋尝试",
            "重量级锁：自旋超过阈值或竞争明显，膨胀为 monitor，依赖操作系统 mutex，线程阻塞唤醒代价高",
            "撤销代价：偏向锁撤销需要等到安全点（STW），因此在高并发交替竞争场景反而可能关闭偏向锁"
        ],
        "hints": "重点说清 CAS、自旋与内核态阻塞三者的成本梯度"
    },

    # ================= === 后端开发 · MySQL === =================
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "MySQL",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "InnoDB 的聚簇索引与二级索引在底层组织上有什么区别？为什么通常建议使用自增主键？",
        "reference_points": [
            "B+ 树：叶子节点存数据、非叶子只存键，叶子间双向链表相连，层数即 IO 次数（3 层可支撑两千万行）",
            "聚簇索引叶子存整行数据，二级索引叶子存主键值，因此二级索引查询非覆盖字段需要回表",
            "覆盖索引（Using index）可避免回表；最左前缀决定联合索引可用性",
            "自增主键顺序追加，页分裂少、碎片低；UUID 随机插入导致频繁页分裂与写放大"
        ],
        "hints": "可以用一张 EXPLAIN 结果或一条真实慢 SQL 来佐证"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "MySQL",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "请说明 MySQL 的 MVCC 是如何实现的？在可重复读隔离级别下它能否完全解决幻读？",
        "reference_points": [
            "隐藏字段 trx_id、roll_pointer + undo log 版本链 + ReadView（m_ids/min_trx_id/max_trx_id/creator_trx_id）",
            "ReadView 生成时机：RC 每条语句生成一次，RR 事务首次快照读生成后复用",
            "RR 下快照读通过 MVCC 避免幻读，但当前读（for update / update）需要 Next-Key Lock（记录锁 + 间隙锁）来防止插入",
            "经典反例：事务 A 快照读 → 事务 B 插入并提交 → 事务 A 执行 update 命中新行后再快照读，会看到该行，说明并非绝对无幻读"
        ],
        "hints": "把快照读与当前读分开讨论，这是本题的关键区分点"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "MySQL",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "redo log、undo log、binlog 三者分别解决什么问题？两阶段提交为什么是必要的？",
        "reference_points": [
            "redo log：InnoDB 独有，WAL + 环形持久化，保证崩溃恢复与事务持久性（crash-safe）",
            "undo log：记录逻辑反向操作，支撑回滚与 MVCC 版本链",
            "binlog：Server 层归档日志，追加写，用于主从复制与数据恢复/闪回",
            "两阶段提交（prepare → 写 binlog → commit）保证 redo 与 binlog 逻辑一致，否则主从或恢复出的数据会不一致",
            "commit crash 时的恢复规则：redo 已 prepare 且 binlog 完整则提交，binlog 不完整则回滚"
        ],
        "hints": "从“如果只写一个日志会怎样”的角度反证两阶段提交的必要性"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "MySQL",
        "stage": "系统设计", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "订单表数据量增长到十亿级，你会如何做分库分表？请说明分片键选择、扩容迁移与非分片键查询的处理方案。",
        "reference_points": [
            "先评估垂直拆（按业务域）与水平拆（按行），并确认是否可用冷热分离/归档替代",
            "分片键选择：优先高频查询维度（如 user_id 保证“我的订单”单库查询），兼顾数据均匀与热点",
            "路由算法：取模（扩容需全量迁移）、范围（易热点）、一致性哈希/基因法（把 user_id 后几位嵌入 order_id 实现双维度路由）",
            "跨分片查询：异构索引表（ES / TiDB / 宽表）、全局二级索引、或走离线数仓",
            "扩容迁移：双写 + 全量刷 + 数据校验 + 灰度切读，中间件如 ShardingSphere 或自研路由层"
        ],
        "hints": "务必提到分布式 ID、跨库事务与分页排序这三类衍生难题"
    },

    # ================= === 后端开发 · Redis === =================
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Redis",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "在高并发项目中你如何用 Redis 优化性能？缓存与数据库的一致性如何保障？",
        "reference_points": [
            "典型用法：热点数据缓存、分布式会话、计数器/排行榜（ZSet）、分布式锁、库存预扣（Lua 原子）",
            "一致性主流方案是 Cache Aside：读时回填，写时先更新 DB 再删除缓存",
            "为什么删不是更新：并发写导致旧值覆盖新值；且更新缓存浪费算力于低频使用字段",
            "延迟双删 / Canal 订阅 binlog 异步失效，把不一致窗口收敛到毫秒级",
            "兜底：缓存设置合理 TTL、关键读走 DB 强一致或加版本号校验"
        ],
        "hints": "结合量化数据说明收益（如 DB QPS 从 8000 降到 600）"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Redis",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "缓存穿透、击穿、雪崩分别怎么产生？互斥锁与逻辑过期在防击穿上各有什么取舍？",
        "reference_points": [
            "穿透（查不存在的 key）：布隆过滤器拦截 + 空值缓存（短 TTL）+ 参数校验",
            "击穿（热 key 过期瞬间高并发）：互斥锁重建 or 逻辑过期异步重建 or 热点 key 永不过期 + 后台刷新",
            "雪崩（大批 key 同时过期 / 实例宕机）：TTL 加随机抖动、多级缓存、集群高可用、熔断降级与限流",
            "互斥锁：一致性强，但其他线程等待甚至自旋，吞吐下降，存在死锁与超时风险",
            "逻辑过期：无阻塞高吞吐，但会短暂返回旧值，适合对一致性不敏感的热点榜单/详情"
        ],
        "hints": "对比时给出你自己的选型判断，而不是罗列两种方案"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Redis",
        "stage": "专业基础", "difficulty": "EASY", "time_limit_sec": 150,
        "text": "Redis 常见的五种数据结构各自的底层编码与典型应用场景是什么？",
        "reference_points": [
            "String（int/sds/embstr）：计数、缓存对象、分布式锁、Session",
            "List（quicklist/listpack）：简单消息队列、最新动态列表、LRU 列表",
            "Hash（listpack/hashtable）：对象字段级更新（用户信息、商品库存明细）",
            "Set（intset/hashtable）：去重、共同好友交并差、抽奖防重复",
            "ZSet（listpack/skiplist）：排行榜、延迟队列、带权重的滑动窗口限流"
        ],
        "hints": "每种给一个真实业务例子比背名字更有说服力"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Redis",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Redis 是单线程的，为什么还能支撑十万级 QPS？Redis 6.0 引入多线程又是如何解决瓶颈的？",
        "reference_points": [
            "纯内存操作 + 单线程避免锁竞争与上下文切换 + IO 多路复用（epoll）支撑海量连接",
            "渐进式 rehash、ziplist/listpack 紧凑编码、跳跃表等结构设计降低开销",
            "真正瓶颈是网络 IO 与内存带宽，而非 CPU 计算，因此单线程命令执行不是问题",
            "6.0 多线程只用于网络数据的读写与协议解析，命令执行仍是单线程，因此无需加锁且保持语义不变",
            "大 key、热 key、慢命令（KEYS、SORT）才是生产事故主因，应使用 SCAN、拆分与本地缓存"
        ],
        "hints": "强调“执行单线程、网络多线程”这一关键区分"
    },

    # ================= === 后端开发 · 分布式与消息队列 === =================
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Kafka",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "消息队列如何保证消息不丢失、不重复消费、顺序消费？请结合你实际用过的 MQ 说明。",
        "reference_points": [
            "不丢失三段保障：生产端（同步发送 + acks=all + 重试）、Broker（副本机制 min.insync.replicas + 持久化刷盘）、消费端（手动提交 offset）",
            "不重复：MQ 只能保证 at-least-once，需消费端幂等（唯一业务键 + 去重表/Redis SETNX/状态机乐观锁）",
            "顺序：同一业务键路由到同一分区（Kafka key / RocketMQ MessageQueueSelector），且消费者单线程处理该分区",
            "分区再均衡、消费者故障会打破顺序，需要业务层版本号或时间戳兜底",
            "积压处理：扩分区 + 扩消费者、临时转储到更大 topic 旁路消费、跳过非关键消息"
        ],
        "hints": "以“三段式”结构作答，最后补一个你处理过的积压案例"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "分布式事务",
        "stage": "系统设计", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "请对比 2PC、TCC、本地消息表与事务消息（RocketMQ）四种分布式事务方案，说明各自适用场景。",
        "reference_points": [
            "2PC：强一致但同步阻塞、协调者单点、资源长期锁定，适合数据库层面的 XA 短事务",
            "TCC：Try/Confirm/Cancel 业务侵入大，需处理空回滚、悬挂、幂等，适合资金等强一致高价值场景",
            "本地消息表：业务与消息同库事务落表，定时投递 + 消费幂等，实现简单、最终一致，适合大多数解耦场景",
            "RocketMQ 事务消息：半消息 + 本地事务 + 回查，免去自建消息表，适合已有 MQ 体系",
            "选型判断维度：一致性要求、性能吞吐、开发成本、是否需要人工补偿与对账"
        ],
        "hints": "先给结论（多数场景选最终一致），再解释为什么不选强一致"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "分布式锁",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Redis 分布式锁有哪些坑？Redlock 与 Zookeeper 方案如何取舍？锁续期你怎么做？",
        "reference_points": [
            "基础实现：SET key val NX PX ttl，释放用 Lua 判断持有者后删除（避免误删他人锁）",
            "核心风险：业务超时导致锁提前释放 → 需要看门狗续期（Redisson 默认 30s，每 10s 续）",
            "GC 停顿 / 网络分区导致锁失效后两个线程同时持写，Redis 主从异步复制还会在故障切换时丢锁",
            "Redlock：向多数独立节点加锁，需处理时钟漂移；Martin Kleppmann 与 antirez 的争议值得点出",
            "ZK 方案：临时顺序节点 + watch 前驱，天然会话绑定更安全但吞吐低于 Redis；对一致性要求极高选 ZK/etcd，追求性能选 Redis + 业务幂等兜底"
        ],
        "hints": "务必提到“锁不是正确性的全部，业务侧仍需幂等/版本号兜底”"
    },

    # ================= === 后端开发 · JVM 与框架 === =================
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "JVM",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "JVM 如何判断对象可以被回收？G1 与 CMS 的区别是什么，你实际做过哪些调优？",
        "reference_points": [
            "可达性分析（GC Roots：栈帧引用、静态变量、常量、JNI），而非引用计数（无法解决循环引用）",
            "引用分级：强/软/弱/虚，决定回收时机与缓存策略",
            "CMS：标记清除、并发标记有浮动垃圾与内存碎片；G1：Region 化 + 可预测停顿模型 + 优先回收垃圾最多区域",
            "调优思路：先看 GC 日志与监控定位问题（频繁 Full GC / 长停顿），再调堆分代、元空间、GC 算法与业务对象生命周期",
            "常见根因：大对象直入老年代、缓存无界增长、内存泄漏（ThreadLocal 未清理、静态集合）"
        ],
        "hints": "调优题一定要给“现象 → 定位手段 → 参数改动 → 效果数据”的闭环"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Spring Boot",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Spring Boot 的自动装配原理是什么？Starter 是如何生效的？循环依赖 Spring 怎么解决？",
        "reference_points": [
            "@SpringBootApplication 聚合 @EnableAutoConfiguration，通过 @Import(AutoConfigurationImportSelector) 加载候选配置",
            "Spring Boot 2.7+ 读取 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports（旧版为 spring.factories），配合 @Conditional 系列条件装配",
            "Starter 只做依赖聚合 + 自动配置，配置项通过 @ConfigurationProperties 暴露",
            "循环依赖：三级缓存（singletonObjects / earlySingletonObjects / singletonFactories），提前暴露代理对象解决 setter/字段注入的循环",
            "构造器注入的循环依赖无法解决；Boot 2.6+ 默认禁止循环依赖，应通过重构（拆分职责、@Lazy）解决"
        ],
        "hints": "先讲装配链路，再落到你写过的自定义 Starter 实践"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Spring Boot",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "你的接口如何做到幂等？请给出至少两种不同强度的实现方案与适用边界。",
        "reference_points": [
            "天然幂等（查询、状态置为固定值）优先设计成幂等，避免额外开销",
            "Token 机制：先申请幂等号，Redis SETNX + 过期，处理前删除，适合前端重复提交",
            "数据库唯一索引/业务单号约束：最强兜底，插入冲突即视为重复",
            "乐观锁版本号 / 状态机流转（只允许 PENDING→SUCCESS），适合扣减与状态推进",
            "分布式锁 + 去重表：适合外部回调（支付/物流）乱序与重试场景，需考虑回调重试上限与人工对账"
        ],
        "hints": "结合一个真实重复请求事故讲清“为什么这一种方案够用”"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Netty",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Netty 的线程模型是怎样的？如何解决粘包半包？什么是零拷贝，Netty 提供了哪些零拷贝能力？",
        "reference_points": [
            "主从 Reactor：bossGroup 接受连接，workerGroup 处理 IO，业务耗时操作投递到独立业务线程池避免阻塞 EventLoop",
            "一个 Channel 绑定固定 EventLoop，天然串行化避免并发问题；但 Handler 内不可做阻塞调用",
            "粘包半包：定长、分隔符（DelimiterBasedFrameDecoder）、消息头长度字段（LengthFieldBasedFrameDecoder，最常用）",
            "Netty 零拷贝：堆外直接内存、CompositeByteBuf 逻辑合并、slice 共享缓冲区、FileRegion transferTo 文件传输",
            "心跳与空闲检测用 IdleStateHandler，断线重连与写高水位背压需自行处理"
        ],
        "hints": "强调“避免阻塞 EventLoop”这一最容易踩的生产坑"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Elasticsearch",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "ES 的倒排索引原理是什么？为什么深分页性能差，如何正确分页？",
        "reference_points": [
            "分词 → Term Dictionary（FST 前缀树压缩常驻内存）→ Posting List（DocID 列表，Roaring Bitmap 压缩）",
            "写入：buffer + translog，refresh 生成 segment 近实时可见（1s），merge 合并小段，flush 落盘",
            "深分页 from=10000 需各分片取 10010 条汇总排序，协调节点内存与网络放大严重",
            "方案：search_after（游标式，适合翻页）、scroll（适合导出）、限制最大页数 + 业务侧引导筛选",
            "keyword 精确匹配不分词，text 分词；相关性打分 BM25，聚合用 doc_values"
        ],
        "hints": "把“为什么各分片都要取够数据”讲清楚，是本题核心"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Spring Cloud",
        "stage": "系统设计", "difficulty": "MEDIUM", "time_limit_sec": 240,
        "text": "微服务之间调用如何保证高可用？请说明超时、重试、熔断、降级、限流各自解决什么问题。",
        "reference_points": [
            "超时：所有远程调用必须显式设置连接与读取超时，且上游超时应大于下游总耗时",
            "重试：只对幂等接口重试，配合退避（指数 + 抖动）与重试预算，避免重试风暴放大故障",
            "熔断：错误率/慢调用比例超阈值时打开，半开试探恢复，防止级联雪崩",
            "降级：返回兜底数据/缓存/默认值，核心链路优先保障，非核心功能先牺牲",
            "限流：令牌桶/漏桶/滑动窗口，入口按 QPS、资源按并发线程数，配合热点参数与队列排队",
            "还需考虑：线程池/信号量隔离、多活与故障转移、全链路压测与预案演练"
        ],
        "hints": "用一次真实故障的时间线串起这些机制最有说服力"
    },

    # ================= === 前端开发 === =================
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "Vue3",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Vue3 的响应式原理相比 Vue2 有什么变化？ref 与 reactive 的底层差异是什么？",
        "reference_points": [
            "Vue2 用 Object.defineProperty 逐层劫持，无法感知新增/删除属性与数组下标变更，需 $set/$delete",
            "Vue3 用 Proxy + Reflect，可拦截 13 种操作，支持动态属性、数组与 Map/Set，且惰性递归（访问时才 deep reactive）",
            "effect 依赖收集：track 建立 target→key→dep 映射，trigger 精确派发，配合 scheduler 实现异步批量更新",
            "reactive 只能作用于对象，解构会丢失响应式；ref 通过 .value 包装，可用于任意类型，模板中自动解包",
            "toRefs / storeToRefs 用于保持解构后的响应式；shallowRef 适合大数据量列表与实例对象"
        ],
        "hints": "顺带提一下 watchEffect 与 computed 的缓存差异会加分"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "Vue3",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Vue3 的编译优化有哪些？diff 过程中的最长递增子序列算法解决了什么问题？",
        "reference_points": [
            "静态提升（hoistStatic）：静态节点只创建一次，复用 DOM 与 vnode",
            "PatchFlags：编译期标注动态部分（text/class/props），运行时只比对标记，跳过静态内容",
            "Block Tree：把动态节点收集到动态子树数组，跳过整棵静态子树的遍历",
            "事件缓存（cacheHandlers）、预字符串化（static content 合并）",
            "diff 采用异构比较；对于乱序子节点用 getSequence 求最长递增子序列，只移动不在 LIS 上的节点，最小化 DOM 移动次数"
        ],
        "hints": "LIS 部分说明“为什么是移动最少”即可，不必手写完整代码"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "Vue3",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "你如何设计一个大型 Vue 项目的状态管理与请求层？请说明分层与踩过的坑。",
        "reference_points": [
            "Pinia 按业务域拆分 store，避免巨型 store；持久化按需（token/user）而非全量",
            "统一 axios 实例：请求拦截注入 token，响应拦截解包 {code,message,data} 并统一错误提示与 401 跳登录",
            "竞态处理：AbortController / 请求序号丢弃过期响应；重复提交用 loading 或幂等 token",
            "大列表性能：虚拟滚动、分页 vs 无限滚动取舍、组件 keep-alive 与路由懒加载",
            "权限：路由 meta + 全局守卫 + 后端二次校验，前端按钮级权限用指令或 composable"
        ],
        "hints": "挑一个真实线上问题（如竞态导致数据错乱）展开讲"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "TypeScript",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "TypeScript 中 interface 与 type 有什么区别？什么是协变与逆变，为什么它们对类型安全重要？",
        "reference_points": [
            "interface 可声明合并、可 extends，适合对外 API 契约；type 支持联合/交叉/条件/映射类型与工具类型",
            "type 可给原始类型/元组/函数签名起别名，interface 不能表达联合类型",
            "协变：子类型关系在容器上保持（Dog→Animal 则 Dog[]→Animal[]），数组协变在运行时可能不安全",
            "逆变：函数参数位置逆变，(Animal)=>void 可赋给 (Dog)=>void；strictFunctionTypes 才会检查",
            "结构化类型（鸭子类型）意味着只要形状匹配即可赋值，配合 unknown 与类型守卫收窄避免 any 扩散"
        ],
        "hints": "落到“为什么项目里要开 strict 并禁 any”的工程实践"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "Node.js",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Node.js 的事件循环有哪些阶段？setImmediate 与 setTimeout(fn,0) 谁先执行？如何避免阻塞事件循环？",
        "reference_points": [
            "阶段：timers → pending callbacks → idle/prepare → poll（IO 与回调）→ check（setImmediate）→ close callbacks",
            "微任务队列 process.nextTick 优先于 Promise 微任务，在每个宏任务后清空",
            "模块顶层两者顺序不确定（受启动耗时影响，poll 是否已过期）；在 IO 回调内 setImmediate 一定先于 setTimeout(0)",
            "阻塞规避：CPU 密集任务拆分/worker_threads/子进程；大 JSON 与同步 fs API 是常见元凶",
            "背压与内存：stream pipeline、避免无限并发（p-limit）、监控 event loop delay 与堆使用"
        ],
        "hints": "把“IO 回调内”这个确定顺序的场景说清，最能体现真实理解"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "CSS",
        "stage": "专业基础", "difficulty": "EASY", "time_limit_sec": 150,
        "text": "请说明 BFC 的形成条件与应用场景，以及 flex 布局中常见的溢出问题如何解决。",
        "reference_points": [
            "BFC 触发：float 非 none、position absolute/fixed、display flow-root/inline-block/flex/grid/table-cell、overflow 非 visible",
            "应用：清除浮动（父元素高度塌陷）、自适应两栏布局（左侧固定右侧 flow-root 不重叠）、外边距合并隔离",
            "flex 溢出根因：flex-shrink 默认 1 但 min-width/min-height 默认为 auto 导致无法收缩到内容以下",
            "解决：给可收缩项设置 min-width:0 或 overflow:hidden，长文本用 text-overflow/word-break",
            "响应式：clamp()、容器查询（@container）、grid auto-fit minmax 减少断点数量"
        ],
        "hints": "min-width:0 这个点几乎必问，务必答到"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "前端工程化",
        "stage": "系统设计", "difficulty": "MEDIUM", "time_limit_sec": 240,
        "text": "如果让你负责一个前端项目的性能优化，你会怎么建立指标体系并落地？",
        "reference_points": [
            "指标先行：Core Web Vitals（LCP/INP/CLS）+ 首屏 TTFB + JS 错误率，用 RUM 采集真实用户数据而非只看 Lighthouse",
            "加载：路由与组件级代码分割、预加载关键资源、HTTP 缓存 + 内容哈希、CDN、图片格式与尺寸适配、tree-shaking 与依赖替换",
            "渲染：骨架屏、虚拟列表、避免布局抖动（预留尺寸）、长任务拆分（scheduler.yield / requestIdleCallback）",
            "构建：Vite 预构建与持久化缓存、产物体积分析、按需引入组件库、Gzip/Brotli",
            "防劣化：CI 中设置体积与性能预算门禁、灰度发布与回滚、监控告警闭环"
        ],
        "hints": "给出一个“优化前后具体数字”的案例，说服力最强"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "浏览器原理",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "从输入 URL 到页面展示经历了什么？其中哪些环节最容易成为性能瓶颈？",
        "reference_points": [
            "DNS（缓存层级）→ TCP/TLS（RTT 次数）→ 请求 → 响应 → 解析 HTML 构建 DOM、CSSOM 阻塞渲染",
            "脚本阻塞解析：defer 保持顺序延后执行、async 就绪即执行；关键 CSS 内联，preconnect 提前握手",
            "渲染流水线：layout（几何）→ paint（像素）→ composite（图层合成），transform/opacity 只走合成不触发重排",
            "瓶颈常在：串行请求瀑布（先 JS 再接口）、未压缩大资源、首屏同步 JS 体积、字体闪烁、图片未预留尺寸导致 CLS",
            "安全与跨域：同源策略与 CORS 预检、SameSite Cookie、CSRF/XSS 防护"
        ],
        "hints": "不要背链路，重点说清“哪个环节你能优化、怎么优化”"
    },

    # ================= === 人工智能 / 大模型应用 === =================
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "LLM应用",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "你在做 LLM 应用时如何降低幻觉并保证输出可控？请给出体系化的做法。",
        "reference_points": [
            "检索增强（RAG）：给模型可引用的事实来源，并在 prompt 中要求“仅基于给定资料作答，无法回答时明确说明”",
            "结构化约束：few-shot 示例 + JSON Schema/Pydantic 校验 + response_format 强制 JSON，失败重试或降级",
            "任务拆解：把复杂问题拆成多步（规划-执行-校验），让每步上下文更短更聚焦",
            "生成后校验：规则校验 + 小模型/LLM 自评 + 关键事实回查检索结果，不通过则重生成",
            "温度与截断：事实型任务用低温度；控制上下文长度避免“中间遗忘”（lost in the middle），关键信息前置或复述"
        ],
        "hints": "务必提到“校验不通过怎么办”，这是工程成熟度的体现"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "RAG",
        "stage": "系统设计", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "设计一个企业知识库问答系统，你会如何在检索质量与生成成本之间取得平衡？",
        "reference_points": [
            "文档处理：按语义/结构分块（标题层级、代码块完整），重叠窗口，元数据（来源、时间、权限）随块存储",
            "混合检索：向量（语义）+ BM25（关键词/专有名词）召回，再用 rerank 模型精排，显著优于纯向量",
            "查询改写：多查询、HyDE、意图路由（不同库/不同工具），追问澄清歧义问题",
            "上下文压缩与引用：只送相关段落，输出带来源引用便于人工核查，命中不足时拒答",
            "成本控制：小模型做改写/分类、大模型只做最终生成；语义缓存高频问答；离线评测集 + 线上指标（命中率、拒答率、满意度）持续迭代"
        ],
        "hints": "强调评测集与指标体系，没有度量就无法优化"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "LangChain",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "你如何评估一个 LLM 应用的效果？没有标注数据时怎么办？",
        "reference_points": [
            "分层评估：端到端业务指标（完成率、人工接管率）+ 中间环节指标（检索命中率、工具调用成功率、格式合法率）",
            "离线评测集：从真实日志抽样构建 golden set，覆盖典型与边界问题，版本化并回归跑",
            "无标注时：LLM-as-judge（需校验裁判与人工一致性）、规则可判定项优先（是否含引用、是否越界承诺）、A/B 对比新旧 prompt",
            "人工评估：小规模双盲打分，定义清晰评分标准（准确性/完整性/安全性）",
            "线上：灰度 + 用户反馈（点赞点踩）+ 抽样人审，建立坏例回流机制持续补充评测集"
        ],
        "hints": "把“坏例如何回流到评测集”说清楚，这是闭环关键"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "深度学习",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Transformer 的自注意力机制是如何计算的？为什么要引入多头与位置编码？",
        "reference_points": [
            "QKV 线性投影，Attention = softmax(QKᵀ/√d)V；√d 缩放防止点积过大导致梯度消失",
            "因果掩码（decoder）保证只看历史 token；复杂度 O(n²d) 是长序列瓶颈",
            "多头：在不同子空间分别关注（语法、指代、位置模式），拼接后投影，增强表达力",
            "位置编码：注意力本身对顺序置换不变，需注入位置信息（正弦、可学习、RoPE、ALiBi）",
            "工程细节：残差连接 + LayerNorm 稳定深层训练，FFN 提供非线性，KV Cache 降低推理成本"
        ],
        "hints": "能说出 KV Cache 或长上下文优化手段会明显加分"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "Python",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "Python 的 GIL 对多线程有什么影响？CPU 密集与 IO 密集分别该怎么选并发模型？",
        "reference_points": [
            "GIL 使同一进程内仅一个线程执行字节码，CPU 密集多线程无加速甚至更慢（切换开销）",
            "IO 密集仍适用多线程/协程：等待时释放 GIL，网络请求由 C 层扩展并发",
            "CPU 密集：multiprocessing 多进程绕过 GIL，或下沉到 NumPy/C/Rust 扩展、Cython",
            "高并发 IO：asyncio 单线程事件循环 + await，代价是必须全链路异步（同步库会阻塞整个 loop）",
            "选型判断：并发量与内存开销（线程 ~MB 栈 vs 协程 ~KB）、第三方库是否有异步版本、调试复杂度"
        ],
        "hints": "点出“混用同步库会卡死事件循环”这个高频事故"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "FastAPI",
        "stage": "专业基础", "difficulty": "EASY", "time_limit_sec": 150,
        "text": "FastAPI 为什么快？它的 async 端点与 sync 端点在运行时有什么区别？",
        "reference_points": [
            "ASGI 异步框架（非 WSGI 阻塞模型），Starlette 路由 + Pydantic 校验 + 自动生成 OpenAPI",
            "async def 端点跑在事件循环；def 端点会被丢到线程池（anyio）执行，避免阻塞 loop",
            "因此调用阻塞库（requests、同步 DB 驱动）时应该用 def，或改用异步客户端",
            "依赖注入系统（Depends）可复用鉴权与 DB 会话；yield 依赖负责资源释放",
            "性能还依赖 uvicorn worker 数量、连接池、序列化开销与响应模型（response_model 过滤字段）"
        ],
        "hints": "把“def 会走线程池”这个反直觉点讲清楚"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "数据工程",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "模型上线后发现效果明显低于离线评估，你会如何排查？",
        "reference_points": [
            "先确认是否训练/服务偏斜（training-serving skew）：特征口径、缺失值填充、预处理顺序、分词与截断长度是否一致",
            "数据分布漂移：线上输入分布、语种、长度、领域是否变化；对比离线评测集是否代表真实流量",
            "标签泄漏：离线指标虚高（使用了未来信息或目标本身），需按时间切分重跑",
            "工程链路：缓存命中旧结果、超时降级走了兜底模型、prompt 版本未同步、并发导致上下文串扰",
            "定位手段：同一条样本双端对比中间产物（检索结果、prompt、原始输出），建立可观测日志与影子流量回放"
        ],
        "hints": "给出“逐环节对齐中间产物”的方法论比猜原因更重要"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "Prompt工程",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "请谈谈你迭代 prompt 的方法。如何判断一次 prompt 改动是真正的改进？",
        "reference_points": [
            "结构化模板：角色 + 任务 + 输入边界 + 输出格式 + 拒答规则 + few-shot，各部分独立可替换",
            "改动必须可归因：一次只改一个变量，保留基线版本与变更说明（prompt 版本化，像代码一样管理）",
            "判定依据是评测集指标（准确率/格式合法率/拒答正确率），而不是“看起来更顺”，并关注统计显著性",
            "针对性修补坏例：把典型坏例转成 few-shot 或显式规则，警惕规则膨胀互相冲突导致整体退化",
            "成本与稳定性：token 数、时延、模型版本升级后的回归；关键业务保留人工兜底"
        ],
        "hints": "强调“版本化 + 回归评测”，这是从玄学到工程的分水岭"
    },

    # ================= === 大数据 === =================
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "Spark",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Spark 的 shuffle 发生在什么时候？数据倾斜你如何定位与解决？",
        "reference_points": [
            "宽依赖触发 stage 划分与 shuffle（groupByKey/reduceByKey/join/partitionBy），HashAggregate 等也伴随 shuffle",
            "定位：Spark UI 看单个 task 处理数据量与耗时长尾，某些 partition 远大于其余",
            "热点 key 加盐打散：给 key 拼随机前缀做两阶段聚合（局部聚合 + 去前缀全局聚合）",
            "大表 join 小表广播（broadcast join）避免 shuffle；skew join hint 自动拆分热点",
            "其他：过滤无效 key（null/默认值单独处理）、提高并行度、AQE 自适应分区合并、内存与序列化（Kryo）调优"
        ],
        "hints": "一定说清“两阶段聚合”的具体做法，这是高频追问点"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "Flink",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Flink 的 exactly-once 是如何实现的？事件时间与窗口延迟怎么处理？",
        "reference_points": [
            "Checkpoint：Chandy-Lamport 变体的异步屏障快照（Barrier），源端注入 barrier，算端对齐后快照状态，全局一致",
            "端到端精确一次还需源可重放（Kafka offset）+ 支持两阶段提交的 Sink（Checkpoint 时 pre-commit，完成后 commit）",
            "反压会影响 barrier 对齐时间，可用 unaligned checkpoint 缓解",
            "事件时间 + Watermark（乱序程度、idle 检测）驱动窗口触发；allowedLateness 容忍迟到，side output 收集超期数据",
            "状态管理：RocksDB 增量 checkpoint、TTL 清理、大状态需预分区与本地恢复"
        ],
        "hints": "把“barrier 对齐”与“两阶段提交”两层讲清，缺一层就不是端到端"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "Hive",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "Hive 中小文件过多会带来什么问题？如何治理？",
        "reference_points": [
            "NameNode 元数据压力（每文件约 150B 内存）、大量 Map task 启动开销、随机 IO 拉低吞吐",
            "根因：动态分区插入、粒度过细、频繁小批量写入、未合并的中间结果",
            "治理：merge 参数（merge.inputfiles / mapreduce.merge）、合理分区与分桶、定期 compaction",
            "写入侧控制并发与文件大小，采用 ORC/Parquet 列存 + 压缩（Zstd/Snappy）",
            "架构侧：湖仓格式（Hudi/Iceberg）支持小文件自动合并与增量读写"
        ],
        "hints": "结合“你治理过多少表、效果数字”回答最有说服力"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "SQL",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "请用 SQL 求“每个部门薪资前三的员工”，并说明窗口函数与普通 group by 的差异。",
        "reference_points": [
            "ROW_NUMBER()/RANK()/DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC)，外层过滤 rn<=3",
            "三者差异：并列第一时 ROW_NUMBER 强制唯一、RANK 跳号、DENSE_RANK 不跳号，需按业务口径选择",
            "窗口函数保留明细行并可做累计/移动/同比环比（LAG/LEAD/SUM OVER），group by 会压缩行数",
            "性能：分区字段与排序字段决定数据重分布代价，尽量先过滤再开窗、避免全表开窗",
            "NULL 与重复值处理、边界（并列超过 3 人是否都要）需与需求方确认"
        ],
        "hints": "口述 SQL 时保持语法完整，并主动说明并列取法与业务确认"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "数据仓库",
        "stage": "系统设计", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "设计一个支撑 BI 报表与自助取数的数据仓库分层，你会如何建模并保证数据质量？",
        "reference_points": [
            "分层：ODS（贴源）→ DWD（明细事实，清洗标准化）→ DWS（轻度汇总主题宽表）→ ADS（应用层指标），维度表独立",
            "建模：维度建模（星型/雪花），缓慢变化维处理（拉链表/快照），一致性维度与指标口径字典",
            "质量：主键唯一、非空、枚举、波动率、跨表一致性校验，规则前置到调度并阻断下游",
            "血缘与元数据：字段级血缘、任务依赖、指标定义可追溯，变更走评审与影响分析",
            "成本与时效：分区裁剪、增量计算（分区覆盖/merge）、冷热分层、SLA 分级保障核心报表"
        ],
        "hints": "强调“口径统一与指标字典”，这是数仓治理的真正难点"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "数据清洗",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "上游数据源突然变更字段导致下游报表错误，你如何建立防御机制？",
        "reference_points": [
            "契约化：与上游约定 Schema 契约与变更通知流程，接入层做 schema registry 校验",
            "防御式解析：字段缺失/类型异常不静默填默认值，显式标记并进入隔离区（dead letter）",
            "监控：行数、空值率、枚举分布、指标波动率的多维告警，异常自动阻断下游任务",
            "可回滚：数据版本化（分区快照 / 时间旅行），支持按天重跑与幂等覆盖",
            "流程：灰度接入新字段、双跑对比、变更评审与影响面评估，事后复盘补充校验规则"
        ],
        "hints": "把“发现—阻断—回滚—复盘”的闭环讲完整"
    },

    # ================= === 运维 / 云原生 === =================
    {
        "job_category": "系统运维", "question_type": "PROFESSIONAL", "skill_name": "Kubernetes",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Pod 一直处于 Pending 或 CrashLoopBackOff，你的排查思路是什么？",
        "reference_points": [
            "Pending：kubectl describe 看 Events —— 资源不足、节点选择器/亲和性不满足、PVC 未绑定、污点容忍、配额限制",
            "CrashLoopBackOff：kubectl logs --previous 看崩溃前日志，多为启动报错、配置/环境变量缺失、依赖不可达、探针失败",
            "OOMKilled（exit 137）：limits 过低或内存泄漏，需看 GC/堆监控而非盲目调大",
            "探针设计：startupProbe 保护慢启动，readiness 控制流量接入，liveness 只用于真正不可恢复场景（配错会放大故障）",
            "镜像拉取失败（ImagePullBackOff）：镜像地址/凭证/网络；节点层面看 kubelet 日志与磁盘压力驱逐"
        ],
        "hints": "按“事件 → 日志 → 退出码 → 资源配置”的顺序说，体现体系化"
    },
    {
        "job_category": "系统运维", "question_type": "PROFESSIONAL", "skill_name": "Docker",
        "stage": "专业基础", "difficulty": "EASY", "time_limit_sec": 150,
        "text": "如何把一个 Python 服务的镜像做小做安全？请给出具体手段。",
        "reference_points": [
            "多阶段构建：builder 装编译依赖与 wheel，runtime 只拷贝产物，基础镜像用 slim/distroless/alpine（注意 musl 兼容）",
            "层顺序：变动少的（依赖清单）在前，源码在后，最大化构建缓存",
            ".dockerignore 排除 .git、tests、node_modules、本地 venv；pip 用 --no-cache-dir",
            "安全：非 root 用户运行、只读文件系统、固定基础镜像 digest、镜像扫描（Trivy）与最小依赖、不泄露密钥（用 secret 挂载）",
            "体积排查：docker history 看单层大小，常见元凶是 apt 缓存未清理、编译工具链残留、日志文件写入镜像层"
        ],
        "hints": "说一个“从 X GB 压到 Y MB”的真实数字最有效"
    },
    {
        "job_category": "运维架构", "question_type": "PROFESSIONAL", "skill_name": "Prometheus",
        "stage": "系统设计", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "为一个 50 个微服务的系统设计监控告警体系，你会怎么设计指标与告警规则以避免告警风暴？",
        "reference_points": [
            "分层指标：USE（资源利用率/饱和度/错误）看基础设施，RED（请求量/错误/时延）看服务，业务指标看转化",
            "时延用直方图 + histogram_quantile 聚合，禁止对平均值求平均；区分 P50/P95/P99",
            "告警降噪：只对用户可感知症状告警（SLO 错误预算燃尽），把原因类指标作为排查上下文；分级（page/ticket）",
            "风暴治理：告警聚合与抑制（inhibition）、静默窗口、依赖拓扑关联（同一根因只发一条）、限流与去重",
            "配套：结构化日志 + traceId 打通链路追踪、Dashboard 模板化、值班与复盘机制、定期告警有效性评审"
        ],
        "hints": "强调“告警必须可执行”，每条告警都对应一个处置动作"
    },
    {
        "job_category": "运维架构", "question_type": "PROFESSIONAL", "skill_name": "Linux",
        "stage": "深度探究", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "一台服务器 CPU 使用率 100%，你如何定位到具体代码？",
        "reference_points": [
            "top 看是 us（用户态）还是 sy（内核态）/wa（等待 IO）/si（软中断），不同占比指向完全不同的原因",
            "us 高：top -H 找高 CPU 线程 → 转十六进制线程号 → jstack/async-profiler 火焰图定位方法栈",
            "sy 高：频繁上下文切换/系统调用，用 vmstat cs、perf stat 看；si 高多为网络包量或中断不均",
            "wa 高：iostat -x 看 util 与 await，pidstat 定位进程，常见于大量小文件 IO 或刷盘",
            "其他：load 高但 CPU 低多为 D 状态进程（NFS/IO 阻塞）；用 perf top 看热点函数，注意容器内 CPU 配额（cgroup throttling）导致的限流"
        ],
        "hints": "先分类（us/sy/wa/si）再定位，展示的是排查思路而非命令背诵"
    },
    {
        "job_category": "运维架构", "question_type": "PROFESSIONAL", "skill_name": "Go",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Go 的 goroutine 调度模型是什么？channel 与 mutex 你如何选择？常见并发 bug 有哪些？",
        "reference_points": [
            "GMP 模型：G（协程，栈可增长，初始 2KB 左右）、M（OS 线程）、P（逻辑处理器，持有本地运行队列），work stealing 均衡负载",
            "系统调用阻塞时 M 与 P 解绑（hand off），避免整个 P 的队列饿死；GOMAXPROCS 控制并行度",
            "channel 用于传递所有权与协调（生产者消费者、扇入扇出、超时控制）；mutex 用于保护共享状态，语义更直接",
            "常见 bug：goroutine 泄漏（无人接收的 channel 发送、未关闭的 range）、数据竞争（go run -race 检测）、闭包捕获循环变量、WaitGroup Add 位置错误",
            "规范：谁写谁关、通过 context 传递取消与超时、避免无缓冲 channel 死锁、defer unlock 成对"
        ],
        "hints": "提到 go test -race 与 goroutine 泄漏排查（pprof goroutine profile）"
    },
    {
        "job_category": "系统运维", "question_type": "PROFESSIONAL", "skill_name": "CI/CD",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "你们的发布流程是怎样的？如何做到可快速回滚且风险可控？",
        "reference_points": [
            "流水线：lint + 单测 → 构建镜像（固定版本与 digest）→ 集成/契约测试 → 安全与镜像扫描 → 预发验证 → 分批发布",
            "发布策略：滚动（默认）、蓝绿（快速切换与回退）、金丝雀/灰度（按流量比例 + 指标自动判定推进或回滚）",
            "可回滚：保留上一版本镜像与配置、迁移脚本向前兼容（expand-contract 模式，避免不可逆 DDL）、一键回滚演练",
            "风险隔离：特性开关（feature flag）让部署与发布解耦，配置变更同样纳入审计与回滚",
            "度量：变更失败率、恢复时长（MTTR）、部署频率、前置时长（DORA 四指标）驱动流程改进"
        ],
        "hints": "务必提到数据库变更兼容性，这是回滚最容易失手的环节"
    },

    # ================= === 质量保障 === =================
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "测试设计",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "给你一个“优惠券发放”功能，你会如何设计测试用例？",
        "reference_points": [
            "先明确规则与边界：领取次数上限、库存、有效期、叠加互斥、适用商品范围、退款后是否返还",
            "正常路径 + 边界（0/1/上限/上限+1、有效期前后 1 秒、跨天跨时区）+ 异常（重复领取、并发抢券、库存不足、参数篡改）",
            "并发与幂等：多线程同时领取不超发、重复请求不重复发放，验证分布式锁与唯一约束",
            "资金与对账：金额计算精度（分为单位）、优惠后价格与订单一致、异常回滚不产生脏数据",
            "非功能：接口性能与限流、日志与监控可定位、灰度与回滚验证；用等价类/边界值/判定表组织，避免用例重复"
        ],
        "hints": "展示“先问清规则再设计用例”的习惯，比罗列用例更高分"
    },
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "Pytest",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "接口自动化测试如何做到稳定可维护？你如何处理测试数据与环境依赖？",
        "reference_points": [
            "分层：断言层薄、封装层（client + builder）厚，用例只描述业务意图，避免复制粘贴",
            "fixture 管理前置条件与清理，function/module 作用域合理选择；参数化覆盖多组数据",
            "数据自治：每个用例自己造数（工厂 + 唯一标识），不依赖执行顺序与共享脏数据，用后清理",
            "不稳定根因：等待策略（禁止 sleep，用轮询/条件等待）、时间与时区、随机种子、外部依赖未 mock",
            "契约与 mock：下游用契约测试或录制回放；断言避免全字段快照，只断言业务关键字段；失败保留请求响应日志与 traceId"
        ],
        "hints": "重点讲“用例之间零依赖”，这是自动化能否长期跑下去的关键"
    },
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "Selenium",
        "stage": "深度探究", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "UI 自动化测试维护成本高、稳定性差，你认为应该怎么定位它的价值边界？",
        "reference_points": [
            "测试金字塔：大量单测 + 适量接口/契约测试 + 极少量关键路径 E2E，UI 层只覆盖核心链路（登录、下单、支付）",
            "稳定性手段：显式条件等待、Page Object 封装、稳定选择器（data-testid 而非 XPath 层级）、失败自动重试 + 截图/视频/DOM 留档",
            "定位价值：跨浏览器兼容、真实用户旅程回归、发布前冒烟门禁；不适合穷举业务分支",
            "反模式：用 UI 自动化验证细节逻辑、用例互相依赖、断言脆弱（文案/样式）、无人维护的僵尸用例",
            "度量：误报率、执行时长、缺陷发现数；长期发现不了 bug 的套件应精简或下线"
        ],
        "hints": "能主动说出“哪些不该做 UI 自动化”体现判断力"
    },
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "性能测试",
        "stage": "系统设计", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "一次全链路压测你如何组织？如何保证压测数据不污染生产？",
        "reference_points": [
            "目标先行：明确 SLO（TPS、P99、成功率）与容量水位，选择基准/阶梯/尖峰/浸泡（长稳）场景",
            "链路建模：按线上流量比例构造场景与参数化数据，避免只压单接口导致结论失真",
            "数据隔离：影子表/影子库 + 压测标透传（网关到 DB），MQ 与缓存走影子 topic/key，禁止写真实业务表",
            "风险控制：限流熔断规则临时调整需评估、避开业务高峰、准备一键停止与降级预案、通知相关方",
            "结果分析：定位瓶颈（应用 CPU/GC、DB 慢查询与连接池、下游依赖、网络与带宽），给出容量结论与优化项，优化后回归验证"
        ],
        "hints": "强调“压测标全链路透传”，这是不污染生产的唯一可靠做法"
    },

    # ================= === 客户端 === =================
    {
        "job_category": "客户端", "question_type": "PROFESSIONAL", "skill_name": "Android",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Android 内存泄漏常见原因有哪些？你如何定位与治理？",
        "reference_points": [
            "典型泄漏：Activity/Context 被静态集合或单例持有、非静态内部类持有外部 Activity、Handler/匿名监听未反注册、未关闭的 Cursor/IO",
            "生命周期：配置变更（旋转）导致重建，ViewModel 与 onRetainNonConfigurationInstance 用于跨重建保存",
            "定位：LeakCanary 自动检测并输出引用链，配合 Profiler 看堆增长与 GC 后是否回落",
            "治理：用 Application Context、弱引用 + 生命周期感知（lifecycleScope 自动取消协程）、统一注册/注销封装",
            "大图与列表：图片采样与复用池、RecyclerView 复用与 DiffUtil、避免主线程 IO 与过度绘制"
        ],
        "hints": "给出“引用链怎么读”的具体例子最加分"
    },
    {
        "job_category": "客户端", "question_type": "PROFESSIONAL", "skill_name": "Flutter",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "Flutter 的三棵树（Widget/Element/RenderObject）分别做什么？setState 之后发生了什么？",
        "reference_points": [
            "Widget 是不可变配置（重建廉价）、Element 管理生命周期与位置、RenderObject 负责布局绘制（昂贵，尽量复用）",
            "setState 标记 Element dirty → 帧回调 build 新 Widget 子树 → Element 按 runtimeType 与 key 决定复用或重建 → 脏化 RenderObject 重新 layout/paint/composite",
            "key 的作用：在列表顺序变化时正确复用状态（ValueKey/ObjectKey/GlobalKey 慎用）",
            "性能优化：拆分小 Widget 缩小重建范围、const 构造、列表用 ListView.builder、避免 build 中做耗时计算与新建对象",
            "RepaintBoundary 隔离重绘区域；isolate 处理 CPU 密集任务避免掉帧"
        ],
        "hints": "把“为什么 Widget 可以随便重建”讲清楚"
    },
    {
        "job_category": "客户端", "question_type": "PROFESSIONAL", "skill_name": "Kotlin",
        "stage": "深度探究", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Kotlin 协程与线程有什么本质区别？结构化并发解决了什么问题？",
        "reference_points": [
            "协程是运行在线程上的轻量任务，挂起（suspend）不阻塞线程，切换成本远低于线程；百万协程可跑在少量线程上",
            "Dispatchers：Main/IO/Default/Unconfined，挂起函数本身不切线程，需显式 withContext",
            "结构化并发：协程必须挂在 CoroutineScope 下，作用域结束自动取消所有子任务，避免“泄漏的异步任务”",
            "SupervisorJob 让兄弟任务失败互不影响；coroutineScope 保证内部子任务全部完成才返回",
            "取消是协作式的：需检查 isActive 或响应 CancellationException，finally 中用 withContext(NonCancellable) 做清理"
        ],
        "hints": "提到“挂起函数不自动切线程”这个高频误解"
    },

    # ================= === 系统底层 / C++ === =================
    {
        "job_category": "系统底层", "question_type": "PROFESSIONAL", "skill_name": "C++",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "请说明 C++ 的内存分区与 RAII 思想，以及移动语义解决了什么问题。",
        "reference_points": [
            "分区：栈（自动、局部对象）、堆（new/make_unique）、全局/静态区、常量区、内存映射区；泄漏与越界多发生在堆与栈帧外访问",
            "RAII：资源生命周期绑定对象作用域，析构自动释放，配合 unique_ptr/shared_ptr/lock_guard 消除手动释放",
            "shared_ptr 计数非线程安全（控制块原子、引用计数本身需注意循环引用，用 weak_ptr 打破）",
            "移动语义：右值引用避免深拷贝（vector 扩容、返回大对象），std::move 只是转为左值为右值，真正的收益在移动构造/赋值实现",
            "被移动后对象处于有效但未指定状态，只能重新赋值或析构；完美转发（forward）保留值类别"
        ],
        "hints": "结合一次真实性能改进（拷贝转移动后的耗时变化）说明"
    },
    {
        "job_category": "系统底层", "question_type": "PROFESSIONAL", "skill_name": "Raft",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Raft 如何选出 Leader 并保证日志一致？为什么已提交的日志一定被后续所有 Leader 包含？",
        "reference_points": [
            "三种角色与任期（term）单调递增；Follower 选举超时未收到心跳则自增 term 转 Candidate 发起投票",
            "一票一任期 + 多数派（quorum）当选，随机超时打散降低选票分裂",
            "日志复制：Leader 追加并并行发送 AppendEntries，多数派确认后提交（推进 commitIndex）再应用到状态机",
            "安全性三条：选举限制（只有日志足够新的节点能当选）、Leader 唯一写入口、只提交当前任期的日志（间接提交需再提交一条当前任期日志）",
            "多数派交集非空 → 已提交日志必然存在于任何新 Leader 的日志中；日志匹配特性保证一致性"
        ],
        "hints": "能讲清“多数派相交”这一不变量，说明真正理解了安全性"
    },
    {
        "job_category": "系统底层", "question_type": "PROFESSIONAL", "skill_name": "网络",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "TCP 三次握手为什么不能是两次？TIME_WAIT 过多怎么处理？",
        "reference_points": [
            "两次握手无法让服务端确认客户端的初始序列号，历史重复 SYN 会建立无效连接并浪费资源；同时双方需确认彼此的 ISN",
            "TIME_WAIT 是主动关闭方等待 2MSL，保证最后 ACK 可达且让旧报文在网络中消亡",
            "过多成因：短连接频繁主动关闭（客户端或未启用 keep-alive 的服务端），排查调用方而非盲目调参",
            "缓解：连接池与长连接复用、调 tcp_tw_reuse（客户端侧）、合理 backlog 与 accept 模型、负载均衡层保持长连接",
            "注意 tcp_abort_on_overflow 等参数会引入错误，SYN flood 场景应关注 syncookies 而非随意调整"
        ],
        "hints": "先讲协议正确性，再讲工程处置，顺序不要颠倒"
    },

    # ================= === 信息安全 === =================
    {
        "job_category": "信息安全", "question_type": "PROFESSIONAL", "skill_name": "Web安全",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "XSS、CSRF、SQL 注入、SSRF 分别如何防御？请说明为什么“转义输出”比“过滤输入”更可靠。",
        "reference_points": [
            "XSS：按上下文输出编码（HTML/属性/JS/URL）、CSP 白名单、HttpOnly Cookie、富文本用成熟净化库并服务端二次校验",
            "CSRF：SameSite Cookie + 一次性 CSRF Token / 自定义请求头校验，关键操作二次确认；不依赖 Referer 单独判断",
            "SQL 注入：参数化查询（预编译）为根本，最小权限账号、ORM 而非拼接、WAF 只是纵深防御",
            "SSRF：出网白名单 + 禁止内网与云元数据地址、禁用重定向跟随、独立低权限代理出网",
            "过滤输入易被绕过（编码、上下文差异、协议特性），且破坏正常业务；输出编码在危险发生点做防护，语义明确"
        ],
        "hints": "每类给一个“最核心的一条措施”，别平铺罗列"
    },
    {
        "job_category": "信息安全", "question_type": "PROFESSIONAL", "skill_name": "权限治理",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "如何系统性发现越权访问（水平/垂直）漏洞？你在项目中怎么建立防护？",
        "reference_points": [
            "水平越权：资源 ID 可枚举 + 未校验归属；垂直越权：前端隐藏入口但后端未鉴权",
            "排查方法：用低权限账号携带高权限/他人资源 ID 重放请求；对 ID 做遍历与差集比对；网关日志审计无鉴权调用的接口清单",
            "防护：所有数据访问统一走带 owner 条件的仓储层（默认过滤而非逐接口记得加），接口级权限注解 + 资源级二次校验",
            "ID 设计：对外用不可枚举的 UUID/雪花 ID 或加签 ID，降低探测面（但不能替代鉴权）",
            "工程保障：鉴权中间件统一兜底、契约测试覆盖未授权用例、上线前权限矩阵评审、定期红队扫描"
        ],
        "hints": "强调“默认安全（fail-closed）”的架构性防护，而不是靠人记得写判断"
    },
    {
        "job_category": "信息安全", "question_type": "PROFESSIONAL", "skill_name": "数据合规",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "处理用户简历、手机号等个人信息，你在脱敏、加密与留存策略上会怎么做？",
        "reference_points": [
            "分级分类：识别敏感字段（身份证、手机号、住址、薪资），按等级确定加密与访问控制强度",
            "存储：可逆需求用字段级加密（KMS 托管密钥、密钥与数据分离），仅需比对用 HMAC/哈希加盐索引",
            "展示与日志：默认掩码（138****8000）、导出与查询留痕、日志与埋点禁止明文 PII，测试环境用合成数据",
            "访问控制：最小权限 + 二次授权、按用途授权（企业仅在候选人授权后可见联系方式）、可撤回同意",
            "留存与销毁：明确保留期限与到期删除/匿名化，支持用户导出与注销（被遗忘权），备份同样纳入删除策略"
        ],
        "hints": "结合“授权可见 + 可撤回”的业务流程讲，比只讲算法更专业"
    },

    # ================= === 通用题（跨岗位） === =================
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "EASY", "time_limit_sec": 120,
        "text": "请用两分钟介绍你自己，重点说明与目标岗位最相关的一段经历。",
        "reference_points": [
            "结构清晰：现状/背景 → 与岗位最相关的一段经历 → 可量化的成果 → 为什么匹配这个岗位",
            "围绕岗位 JD 的能力关键词组织内容，而不是流水账式罗列课程与社团",
            "成果量化：做了什么、指标变化多少、自己承担的具体角色",
            "控制在 2 分钟内，结尾主动把话题引向自己最能证明能力的项目"
        ],
        "hints": "提前准备一个 30 秒版本和 2 分钟版本，切忌背诵感"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 240,
        "text": "介绍一个你最有成就感的项目，说明你负责的部分、遇到的最大困难以及最终结果。",
        "reference_points": [
            "用 STAR：情境（业务目标与约束）→ 任务（你的职责边界）→ 行动（关键技术/方案选择与取舍）→ 结果（量化收益）",
            "困难要具体到“卡在哪一步、试了哪些路、为什么最终选它”，体现真实参与",
            "主动说明自己的不足与返工，比只讲成功更可信",
            "结果给出可核查的数字（性能提升、耗时下降、用户量），并说明数据如何统计得到",
            "准备好被追问细节：某个参数为什么这么设、某段代码谁写的、下一步会怎么改"
        ],
        "hints": "面试官考察的是深度与真实性，宁可讲小切口也不要讲宏大空话"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "项目中你与同事（或上下游）产生过技术分歧吗？你是怎么推动达成一致的？",
        "reference_points": [
            "选真实冲突，先客观复述双方立场与各自合理性，不贬低对方",
            "关键动作：回到共同目标与判断标准（数据、用户体验、维护成本），把“我觉得”变成“我们验证一下”",
            "推动方式：小范围实验/压测数据、书面方案对比、拉相关方评审、必要时向上升级但不越级对抗",
            "结果与关系维护：即使最终采纳对方方案也全力执行，事后复盘沉淀规范",
            "体现成熟度：能承认自己判断失误，并说明从中学到了什么"
        ],
        "hints": "考察协作与情绪管理，避免把自己塑造成“一直正确”的人"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "说一次你失败或犯错的经历，你事后如何复盘，改变了什么？",
        "reference_points": [
            "选真实且有代价的失败，明确自己应承担的责任部分，不甩锅给环境或他人",
            "说清后果（延期、返工、线上问题）与当时为什么判断失误（信息不足、侥幸心理、未验证假设）",
            "复盘落到机制：加了什么检查清单、自动化校验、评审环节，让同类问题不再依赖个人细心",
            "展示改变已被验证：后续同类任务的具体做法与结果",
            "态度：坦然但不自我贬低，聚焦成长"
        ],
        "hints": "这题最忌“我的缺点是太追求完美”式伪失败"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "EASY", "time_limit_sec": 120,
        "text": "近期你在主动学习什么？通过什么方式学，怎么确认自己真的学会了？",
        "reference_points": [
            "有具体在学的技术/领域与明确动机（岗位需要或项目卡点），不是泛泛而谈“看书”",
            "学习路径：官方文档/源码 → 动手做小项目 → 输出（笔记、分享、博客）→ 反馈修正",
            "检验标准：能否不查资料实现、能否讲给别人听、能否处理异常与边界场景",
            "把学习成果与实际产出关联（用新学的技术解决了什么问题）",
            "体现持续性与方法，而非一次性的突击"
        ],
        "hints": "举一个“学到能上手”的具体证据，比列书单有效"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "你的职业规划是什么？为什么选择我们这个岗位？",
        "reference_points": [
            "短期（1-2 年）能力目标具体可验证（如独立负责某类模块/打通某条链路），不喊“成为专家”的空口号",
            "中长期方向与岗位成长路径一致，说明你了解这个岗位实际做什么",
            "选择理由落到该业务/技术栈/团队特点的具体事实（产品形态、技术挑战、岗位要求），而非“公司很大很有名”",
            "诚实说明自身与要求的差距及补齐计划，展现自我认知",
            "避免暴露“只把这里当跳板”或“完全不了解岗位”的信号"
        ],
        "hints": "提前研究岗位 JD 与公司产品，把理由说具体"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "如果同时有多个任务且截止时间冲突，你如何安排？",
        "reference_points": [
            "先澄清：任务目标、真实截止时间、可交付的最小范围与依赖关系，避免按表面要求硬扛",
            "排序依据：影响面 × 紧急度 × 阻塞他人程度，优先做会阻塞他人的事",
            "主动沟通：及早暴露风险与取舍，向上申请调整范围或时间，而不是最后一刻才说做不完",
            "执行手段：拆分与并行、降低非关键任务标准、争取资源或复用已有方案、设置中间检查点",
            "复盘：识别为什么会出现冲突（估算偏差、需求变更），改进后续排期方式"
        ],
        "hints": "核心是“及时沟通取舍”，不是“我能加班全做完”"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 120,
        "text": "你觉得自己最大的优势与最需要改进的地方分别是什么？",
        "reference_points": [
            "优势要有证据支撑（具体事例或他人反馈），并与岗位核心要求相关",
            "不足要真实、可控、且已在改进：说明它带来的具体困扰与正在采取的措施、初步效果",
            "避免套路化缺点（过于追求完美、工作太投入），也避免暴露岗位致命短板（如后端岗说自己逻辑差）",
            "展现自我认知的客观性：能区分“能力不足”与“经验不足”",
            "语气平稳，不过度自夸也不自我贬损"
        ],
        "hints": "面试官会追问举例，准备好支撑材料"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "EASY", "time_limit_sec": 120,
        "text": "你如何快速上手一个不熟悉的技术栈或一个陌生的大型项目？",
        "reference_points": [
            "先建立地图：读文档/架构说明、跑通本地环境、看部署与调用链路，再挑一条最简单的业务链路端到端追代码",
            "动手优先：用一个小需求或修 bug 作为切入点，通过改动验证理解，而不是只读代码",
            "善用资源：问对人（先查再问，带着自己的假设问）、看提交历史与 issue 理解设计动机",
            "输出结构化笔记与疑问清单，及时与导师/同事对齐认知偏差",
            "识别风险区：先改影响面小的地方，理解测试与发布流程后再动核心逻辑"
        ],
        "hints": "给一个真实的上手案例和时间线"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "你在团队中通常扮演什么角色？举一个你主动补位的例子。",
        "reference_points": [
            "自我定位清晰（推动者/执行者/协调者/技术攻坚），并说明这种定位的适用与不适用场景",
            "补位例子要有具体情境：谁不在、风险是什么、你做了什么超出职责的事、结果如何",
            "说明补位的边界：临时补位同时推动长期机制（文档、规范、交接），不鼓励常态化越位",
            "体现对他人贡献的认可，不抢功",
            "主动补位与“不守边界”的区别在于是否沟通对齐"
        ],
        "hints": "考察责任心与协作意识，避免只讲个人技术贡献"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 120,
        "text": "如果入职后发现岗位内容与你的预期不一致，你会怎么办？",
        "reference_points": [
            "先核实与理解：确认岗位真实职责、团队目标与自己预期的差距来源（信息不对称还是临时安排）",
            "主动沟通：与主管对齐期望与成长路径，争取能发挥所长的切入点，而不是消极等待或私下抱怨",
            "寻找价值：即使偏基础的 work 也能找到改进空间（自动化、规范化、沉淀文档）",
            "设定观察期与判断标准，若长期确实不匹配再理性决策，避免情绪化离职",
            "体现成熟度：不承诺“完全无所谓”，也不表现出只挑活干"
        ],
        "hints": "考察稳定性与沟通成熟度，诚实且积极的答案最优"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "EASY", "time_limit_sec": 60,
        "text": "你有什么想问我们的？",
        "reference_points": [
            "准备 2-3 个有信息量的问题：团队当前最大的技术/业务挑战、这个岗位前三个月的成功标准、代码评审与成长机制",
            "避免只问薪资福利与不加班（可留到 HR 环节），也不要问官网能查到的基础信息",
            "可基于面试过程中的具体回答追问，体现你在认真听",
            "问题反映你的关注层次：技术挑战与成长 > 流程制度 > 待遇",
            "结尾简短表达对岗位的兴趣与匹配点"
        ],
        "hints": "这是最后的加分机会，千万不要说“没有问题”"
    },

    # ================= === 压力题 === =================
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 90,
        "text": "你简历上这个项目看起来很简单，说实话我认为它的技术含量不高，你怎么看？",
        "reference_points": [
            "先稳定情绪，不辩解不贬低面试官：认可对方视角的合理性（规模/复杂度确实有限）",
            "用事实补充深度：具体说清难点在哪、自己做过哪些超出表面的优化与权衡",
            "诚实承认边界：如果是校园项目，坦率说明约束条件，并指出若在生产环境会怎么改",
            "把话题引向能力迁移：从这段经历中提炼的可复用方法（排查思路、性能分析、协作）",
            "结尾保持自信而不自负，语气平稳、不攻击问题本身"
        ],
        "hints": "考察情绪管理与自我认知，切忌慌乱或反击"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 90,
        "text": "刚才那道题你答了五分钟还是没说到关键点，是不是这块基础其实没掌握？",
        "reference_points": [
            "不被标签带情绪：先明确回应“我理解你的顾虑”，再请求用 60 秒重新组织核心结论",
            "立刻给出结构化答案：先结论、再依据、最后边界，展示你能抓住重点",
            "诚实区分：是“知道但表达绕了”还是“确实不熟”，后者要坦承并给出补学计划",
            "把压力转为行动：主动提出可以现场写伪代码或举一个实际案例来证明",
            "全程保持语速平稳，不重复解释自己为什么慢"
        ],
        "hints": "关键动作是“重新组织并给出结论”，不是继续解释"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 120,
        "text": "线上系统在你负责期间出了严重故障造成资损，你现在第一件要做的事是什么？后续怎么处理？",
        "reference_points": [
            "第一优先级是止血恢复：按预案降级/回滚/切流，控制影响面，同时同步相关方与升级通报",
            "保护现场与证据：保留日志、监控快照、变更记录，不在恢复前破坏性排查",
            "恢复后做时间线复盘：故障引入点、发现耗时、处置耗时、影响量化（订单/金额/用户数）",
            "根因用“五个为什么”追到机制层面，改进项分短期修复与长期防御（校验、灰度、监控、演练）",
            "责任态度：不推诿，明确自己该承担的部分，同时避免个人英雄主义，推动系统性改进与对账补偿"
        ],
        "hints": "顺序错了会严重扣分：先止血，再定责，最后复盘改进"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "MEDIUM", "time_limit_sec": 90,
        "text": "我现在告诉你，你的表现排在今天所有候选人最后，你还有什么想说的？",
        "reference_points": [
            "不被激将、不自我否定：可以先说“这个反馈我记下了”，再问清具体是哪些环节未达预期",
            "把焦点从情绪转到信息：主动请求指出短板，展现可教练性（coachability）",
            "对确实薄弱的环节给出具体补强动作与时间，而不是空喊“我会努力”",
            "重申与岗位最相关的一两个证据，不纠缠、不哀求",
            "结尾体面：无论结果如何都感谢反馈，保持职业感"
        ],
        "hints": "这题没有标准答案，考察的是被否定时的反应模式"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 120,
        "text": "假设你写的方案被架构师全盘否定，而会后你发现他的方案有明显性能隐患，你会怎么做？",
        "reference_points": [
            "先反思：自己的方案被否是否因为考虑不周，架构师可能有你不知道的约束（成本、团队、历史包袱）",
            "用证据而非观点沟通：做一个最小可复现的压测或数据推演，量化隐患与影响面",
            "私下、对事不对人地提出：给出“隐患 + 数据 + 备选缓解方案”，而不是“你错了”",
            "尊重决策权：若对方仍坚持，执行并留痕（书面记录风险与假设），同时设置监控验证",
            "长期机制：推动方案评审模板纳入性能与容量评估项，让风险在评审阶段暴露"
        ],
        "hints": "考察向上沟通与职业成熟度，“越级告状”和“沉默执行”都是低分答案"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 90,
        "text": "请用 30 秒说服我，为什么我们要录用一个在这轮面试中暴露出这么多问题的候选人？",
        "reference_points": [
            "30 秒内必须有结构：一句定位（我带来的核心价值）+ 两个证据 + 一个短板与补强计划",
            "直面问题不回避：把暴露的短板归因为经验/训练量而非能力上限，并给出可验证的改进路径",
            "强调可迁移性与成长速度：举一个“从零到能用”的真实时间线作为证据",
            "与岗位需求绑定：说明团队当前最需要什么，你恰好能提供什么（哪怕需要一点时间）",
            "语气坚定、简洁，不乞求也不过度承诺"
        ],
        "hints": "计时压力题，超时会直接扣分，务必练到 30 秒内说完"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "MEDIUM", "time_limit_sec": 120,
        "text": "你只有五分钟时间向 CEO 汇报一个他完全不关心细节的技术风险，你会怎么说？",
        "reference_points": [
            "结论先行：一句话说清风险是什么、对业务的影响（钱/用户/合规）、需要他做什么决策",
            "用业务语言翻译技术：不说“缓存击穿”，说“大促期间有 30% 概率下单失败，影响约 XX 万元 GMV”",
            "给选项而非开放问题：方案 A/B 的投入、收益、剩余风险与建议，明确所需资源与时间",
            "量化不确定性：概率、影响范围、最坏情况与兜底措施",
            "严格控制时间，留出 1 分钟给提问，准备一页纸或一个数字支撑"
        ],
        "hints": "考察信息压缩与向上沟通，切忌陷入技术细节"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 90,
        "text": "如果入职三个月你负责的需求连续延期两次，主管开始不信任你，你会怎么做？",
        "reference_points": [
            "先自省归因：延期是估算偏差、需求变更、依赖阻塞还是能力短板，用数据还原事实",
            "主动沟通而非等待：向主管同步根因与改进计划，明确可验证的小目标重建信任",
            "改进动作具体化：拆分任务粒度、每日/每两天同步进度、风险提前暴露、把不确定项先做技术验证",
            "寻求反馈与帮助：结对、请同事评审估算，避免独自硬扛再次失手",
            "用连续的小兑现重建信用，同时管理承诺范围（不轻易答应做不到的时间）"
        ],
        "hints": "核心是“主动 + 可验证的小承诺”，不是表忠心"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "MEDIUM", "time_limit_sec": 120,
        "text": "现场写一段代码：给一个可能为 null 的嵌套对象链取值，并说明你会如何避免 NPE 在项目中反复出现。",
        "reference_points": [
            "局部处理：Optional 链式 orElse/orElseThrow、Kotlin 安全调用 ?. 与 ?:、Java 判空提前返回",
            "边界处校验：外部输入/反序列化在入口做校验（Bean Validation、schema 校验），内部信任契约",
            "数据模型设计：用空对象模式（Null Object）、默认值集合（Collections.emptyList）替代 null 返回",
            "工程手段：@NonNull/@Nullable 注解 + 静态检查（NullAway/ErrorProne/IDE 检查）、单测覆盖空值分支",
            "监控兜底：全局异常处理与告警，把重复出现的 NPE 当作设计缺陷治理而非逐处补 if"
        ],
        "hints": "先给出可运行代码，再上升到机制，展示工程视野"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 90,
        "text": "我打断你一下：你说的这些我在你简历里找不到任何支撑，你是不是在编？",
        "reference_points": [
            "保持镇定，不慌不怒：先确认对方具体指哪一部分，避免笼统辩解",
            "给出可核查的证据：仓库链接、部署地址、监控截图、数据口径、可联系的同事/导师",
            "若确实表述夸大，立刻承认并纠正范围（“这里准确说法是……”），诚实比面子重要",
            "不攻击面试官的质疑，主动提出可现场演示或补充材料",
            "把话题拉回能力本身：用一两个可当场验证的问题重新建立信任"
        ],
        "hints": "这题考察诚信与情绪，含糊其辞或过度激动都会出局"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "MEDIUM", "time_limit_sec": 120,
        "text": "客户在大群里公开投诉你负责的模块有严重问题，措辞很难听，你的前 30 分钟做什么？",
        "reference_points": [
            "先处理事实与影响，不处理情绪：不在群里对线，第一时间私聊/电话承接并确认具体问题与影响范围",
            "公开回应简短专业：感谢反馈 + 已定位中 + 明确下次同步时间，把沟通引导到可控渠道",
            "内部快速拉通：确认是否真为缺陷、能否回滚/降级、给出临时方案与预计恢复时间",
            "按约定时间同步进展，即使未解决也保持节奏，避免信息真空放大不满",
            "事后复盘：把客户诉求转成需求或缺陷单，补充监控与用例，避免同类问题复发"
        ],
        "hints": "考察情绪管理与对外沟通，切忌“先自证清白”"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 90,
        "text": "接下来请连续回答三个问题，每个不超过 20 秒，第一题：你最近一次被人指出错误是什么时候？",
        "reference_points": [
            "高压快节奏下先给答案再补上下文，不要开场铺垫或请求思考时间过长",
            "选真实具体的事件（时间、场景、谁指出、错在哪），拒绝泛泛而谈",
            "第二句说明你当时的反应与后续动作（是否当场承认、如何修正）",
            "第三句给改变：加了什么检查机制，之后是否再犯",
            "全程保持节奏与眼神稳定，答完即停，不拖长解释"
        ],
        "hints": "这题真正考的是节奏控制与简洁表达，内容真实即可"
    },

    # =====================================================================
    # 非技术岗位专业题（扩展行业覆盖）：产品 / 运营 / 销售 / 人力 / 财务 / 市场 / 设计 / 客户成功
    # 通用题与压力题沿用"通用"大类，此处仅补各岗位大类的 PROFESSIONAL 配额。
    # =====================================================================

    # ================= === 产品经理 === =================
    {
        "job_category": "产品经理", "question_type": "PROFESSIONAL", "skill_name": "需求优先级",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "作为产品经理，当多个业务方同时提出需求而研发资源有限时，你如何决定优先级？请介绍你用过的优先级框架及一次真实的取舍。",
        "reference_points": [
            "价值与成本双维评估：业务价值（收入/留存/战略对齐）、用户价值、实现成本与机会成本",
            "框架落地：RICE（触达/影响/信心/投入）、KANO（基本/期望/兴奋）、MoSCoW、价值-复杂度矩阵，说明各自适用场景",
            "透明地管理预期：给业务方公开的排序标准与替代方案（分期、临时方案），而非黑箱拍板",
            "与目标绑定：把需求挂到北极星指标/OKR，减少主观拉扯",
            "闭环复盘：上线后回看当初的优先级判断是否兑现价值，校准下次评估"
        ],
        "hints": "面试官想听真实取舍案例，而不是只背框架名词"
    },
    {
        "job_category": "产品经理", "question_type": "PROFESSIONAL", "skill_name": "用户洞察",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "你如何判断一个“用户反馈的需求”是真实痛点还是伪需求？请说明你的验证方法。",
        "reference_points": [
            "区分“用户说的”与“用户要的”：追问场景、频率、当前替代方案与痛点强度（5 Whys）",
            "定量验证：用埋点/漏斗看该路径的真实使用与流失，判断是个例还是普遍",
            "定性验证：用户访谈、可用性测试，观察行为而非只听陈述",
            "最小成本试错：MVP/落地页/灰度实验，用真实转化数据代替主观判断",
            "警惕幸存者偏差：明确“不做”的判据，避免被最吵的用户带偏"
        ],
        "hints": "强调“验证”而非“拍脑袋”，展示数据与用户双驱动"
    },
    {
        "job_category": "产品经理", "question_type": "PROFESSIONAL", "skill_name": "数据分析",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "某功能上线一周后核心指标不升反降，你如何排查并做出决策？",
        "reference_points": [
            "先确认数据可信：埋点是否正确、口径是否一致、是否达到统计显著性与样本量",
            "分层下钻：按新老用户/渠道/机型/地域/时间段拆解，判断是全局下降还是局部",
            "建立假设并验证：功能本身、交互改动、性能、文案、灰度比例、外部因素（节假日/活动）",
            "结合定性：客服反馈、用户访谈、录屏回放看真实卡点",
            "决策机制：触及回滚阈值先止损回滚，否则小流量继续验证，避免沉没成本绑架"
        ],
        "hints": "考察结构化拆解与止损决断，不是急于找研发背锅"
    },
    {
        "job_category": "产品经理", "question_type": "PROFESSIONAL", "skill_name": "跨团队协作",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "研发认为你的需求“技术上不合理”并拒绝推进，你会怎么处理？",
        "reference_points": [
            "先理解约束：是真不可行还是成本高，请教技术原理，避免外行指挥内行",
            "回到目标：对齐需求要解决的用户/业务问题，寻找技术可达的替代方案达成同一目标",
            "用价值换资源：量化收益与影响面，必要时拉上级/业务方共同排优先级",
            "分期与折中：用 MVP 先验证价值，降低一次性技术投入",
            "维护关系：对事不对人，尊重专业判断，沉淀协作机制（研发早期介入评审）"
        ],
        "hints": "展示影响力而非职权，避免“我老板说了算”式答案"
    },

    # ================= === 用户运营 === =================
    {
        "job_category": "用户运营", "question_type": "PROFESSIONAL", "skill_name": "用户分层",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "请介绍你做过的用户分层/分群方法，以及针对不同层级如何设计差异化的运营策略。",
        "reference_points": [
            "分层模型：RFM（最近/频次/金额）、生命周期（新增-成长-成熟-衰退-流失）、AARRR、价值分层",
            "数据驱动圈人：定义可量化的标签与阈值，落地成可运营的人群包",
            "差异化策略：高价值留存权益、沉睡召回、新手指引、流失预警干预",
            "指标绑定：每层明确北极星（留存率/复购/召回率），避免为分层而分层",
            "闭环迭代：用 AB 实验验证策略有效性，动态调整分层口径"
        ],
        "hints": "要有具体分层口径，不是泛泛而谈“精细化运营”"
    },
    {
        "job_category": "用户运营", "question_type": "PROFESSIONAL", "skill_name": "增长实验",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "设计一个提升新用户次日留存的运营方案，并说明你如何验证它真的有效。",
        "reference_points": [
            "先定位流失原因：看新用户在 D1 前的关键行为断点，结合用户访谈",
            "假设驱动：找到 aha moment 关键行为，设计引导（新手任务/权益/触达节奏）",
            "实验设计：随机分流、对照组、样本量与显著性、单一变量",
            "指标体系：主指标次留，护栏指标（ARPU/投诉/卸载）防止顾此失彼",
            "迭代与规模化：有效则放量并沉淀 SOP，无效则回看假设是否成立"
        ],
        "hints": "强调因果验证（对照实验），而不是“上了就涨了”"
    },
    {
        "job_category": "用户运营", "question_type": "PROFESSIONAL", "skill_name": "活动复盘",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "一场线上活动 ROI 不达预期，你会如何复盘并改进？",
        "reference_points": [
            "还原目标与漏斗：曝光-参与-转化-留存-复购逐环节对比预期",
            "归因拆解：流量质量、选品/权益吸引力、玩法复杂度、时机、渠道",
            "成本结构复盘：补贴/流量/人力投入与 GMV/新增/留存的真实产出",
            "区分短期与长期：警惕羊毛党虚高，看留存与 LTV",
            "输出可复用结论：沉淀活动模板与红线，下次用 A/B 验证改进点"
        ],
        "hints": "复盘要落到机制改进，而不是甩锅给流量"
    },
    {
        "job_category": "用户运营", "question_type": "PROFESSIONAL", "skill_name": "私域运营",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "如何衡量私域社群的真实价值，而不是只看群数量？",
        "reference_points": [
            "价值指标：活跃率、内容互动、转化/GMV 贡献、复购、客服成本下降、NPS",
            "归因方法：社群专属优惠码/链路追踪，隔离社群带来的真实增量",
            "健康度监控：退群率、静音率、水群比，识别虚假繁荣",
            "分层运营价值：KOC 培育、精准触达替代广撒网以降本",
            "长期视角：把社群当作留存与复购资产，而非一次性拉新渠道"
        ],
        "hints": "考察反虚荣指标意识"
    },

    # ================= === 销售商务 === =================
    {
        "job_category": "销售商务", "question_type": "PROFESSIONAL", "skill_name": "销售漏斗",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "请描述你从线索到成交的完整打法，你如何管理销售漏斗与转化率？",
        "reference_points": [
            "漏斗阶段划分：线索-商机-需求确认-方案-谈判-赢单，各阶段定义清晰",
            "关键指标：各阶段转化率、销售周期、客单价、赢单率",
            "线索分级：按预算/决策权/需求/时间（BANT）筛掉低质线索，聚焦高潜",
            "推进动作：每个商机明确下一步与退出标准，避免“僵尸商机”虚增管道",
            "复盘与预测：用历史转化率做管道预测，识别卡点环节补动作"
        ],
        "hints": "要有量化漏斗意识，而不是“我关系好能喝”"
    },
    {
        "job_category": "销售商务", "question_type": "PROFESSIONAL", "skill_name": "异议处理",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "客户说“你们价格太贵了”，你会怎么应对？",
        "reference_points": [
            "先探询真实异议：贵是相对预算、相对竞品，还是价值未被感知，用提问澄清",
            "重构价值锚点：从价格转向 ROI、总拥有成本、差异化收益与风险规避",
            "用案例与数据佐证：同行业客户的量化收益，降低决策不确定性",
            "灵活让步策略：不轻易降价，用服务/账期/分期/增值交换，保护价格体系",
            "识别决策链与预算周期，必要时调整方案以匹配预算"
        ],
        "hints": "考察价值销售而非价格战"
    },
    {
        "job_category": "销售商务", "question_type": "PROFESSIONAL", "skill_name": "大客户攻坚",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "如何拿下一个决策链复杂的 B 端大客户？",
        "reference_points": [
            "绘制决策地图：使用者、技术把关、经济买家、决策者、内线（Champion），识别各自诉求差异",
            "分层价值传递：对使用者讲效率、对 IT 讲安全可控、对老板讲战略与 ROI",
            "培育内线：找到 Champion 帮你推进信息流通与内部背书",
            "长周期节奏管理：设定里程碑、多次接触、内容与案例持续渗透",
            "风险与合规：招投标规则、竞品卡位、预算审批节点，提前布局"
        ],
        "hints": "考察复杂销售的系统化打法，而非单点关系"
    },
    {
        "job_category": "销售商务", "question_type": "PROFESSIONAL", "skill_name": "业绩抗压",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "连续两个月没有完成业绩指标，你会怎么做？",
        "reference_points": [
            "数据归因：拆解漏斗看是线索量、转化率还是客单价问题，区分市场/产品/个人因素",
            "主动求助与复盘：向 top sales 学话术、请主管陪访、复盘丢单原因",
            "管道重建：短期补线索（活动/转介绍），中期提转化（方案打磨、跟进节奏）",
            "过程指标管理：把不可控的结果转为可控的拜访/演示/报价数量",
            "心态与诚信：不造假、不压单骗指标，聚焦可持续改善"
        ],
        "hints": "考察抗压下的自我诊断与行动力"
    },

    # ================= === 人力资源 === =================
    {
        "job_category": "人力资源", "question_type": "PROFESSIONAL", "skill_name": "招聘效能",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "如何提升一个难招岗位的招聘达成率与招聘质量？",
        "reference_points": [
            "岗位画像对齐：与用人部门明确硬性/软性要求与优先级，校准薪资带宽",
            "渠道组合与漏斗：各渠道 ROI（简历量/到面率/offer 率），聚焦高质渠道",
            "雇主品牌与卖点：提炼岗位吸引点，优化 JD 与候选人体验",
            "流程效率：缩短反馈周期、减少候选人流失，统一面试官评估标准",
            "数据复盘：到面率、offer 接受率、试用期留存，定位卡点"
        ],
        "hints": "考察全流程视角，不只是“多搜简历”"
    },
    {
        "job_category": "人力资源", "question_type": "PROFESSIONAL", "skill_name": "绩效体系",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "KPI 与 OKR 有什么区别？在什么样的组织情境下你会推荐哪一种？",
        "reference_points": [
            "本质区别：KPI 是关键结果指标、自上而下、与考核薪酬强挂钩；OKR 是目标+关键结果、鼓励对齐与野心、常与考核解耦",
            "适用情境：成熟稳定/强执行岗位用 KPI；创新/探索/需跨部门对齐用 OKR",
            "OKR 落地要点：公开透明、挑战性目标、周期性复盘，避免退化为打分工具",
            "各自风险：KPI 易导致博弈与短期行为；OKR 若与薪酬强绑会失去野心",
            "组合使用：底层用 KPI 保底线，上层用 OKR 牵引突破"
        ],
        "hints": "考察对机制设计权衡的理解，而非名词解释"
    },
    {
        "job_category": "人力资源", "question_type": "PROFESSIONAL", "skill_name": "员工关系",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "公司要优化一名绩效不达标的员工，作为 HR 你如何合规且妥善地处理？",
        "reference_points": [
            "先厘清法律路径：绩效不达标不等于可单方解除，需培训或调岗后仍不胜任，注意举证与程序",
            "证据与流程留痕：绩效记录、改进计划（PIP）、沟通记录、制度公示",
            "优先协商解除：N+1 补偿、协商一致，降低仲裁风险与团队负面影响",
            "沟通艺术与尊重：给员工体面，避免歧视性/侮辱性理由",
            "风险评估：特殊群体（孕期/工伤/医疗期）保护，测算成本与舆情"
        ],
        "hints": "考察合规意识与人文底线，切忌“直接辞退”"
    },
    {
        "job_category": "人力资源", "question_type": "PROFESSIONAL", "skill_name": "人才发展",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "如何搭建一套有效的员工培训与人才梯队体系？",
        "reference_points": [
            "需求诊断：从业务战略与能力差距出发，而不是拍脑袋开课",
            "分层设计：新员工融入、专业序列、管理序列、高潜梯队差异化培养",
            "70-20-10 法则：以岗位实践为主、导师与复盘为辅、课堂培训为引",
            "效果评估：柯氏四级（反应/学习/行为/结果），关联业务指标",
            "机制保障：任职资格、晋升通道、人才盘点九宫格与继任计划"
        ],
        "hints": "考察体系化思维，避免“多办培训”"
    },

    # ================= === 财务审计 === =================
    {
        "job_category": "财务审计", "question_type": "PROFESSIONAL", "skill_name": "财务报表",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "三大财务报表的关系是什么？为什么一家公司利润为正却可能出现资金链断裂？",
        "reference_points": [
            "三表勾稽：利润表反映经营成果、资产负债表反映财务状况、现金流量表反映现金收支，净利润转入留存收益、现金变动连接资产负债",
            "权责发生制 vs 收付实现制：确认利润不等于收到现金",
            "盈利却断流的原因：应收账款高企、存货积压、激进确认收入、大量资本开支、短债长投",
            "关注现金流质量：经营性现金流与净利润长期背离是危险信号",
            "营运资本管理：账期错配、过度扩张、分红/还本压力"
        ],
        "hints": "考察对“利润≠现金”这一核心理解"
    },
    {
        "job_category": "财务审计", "question_type": "PROFESSIONAL", "skill_name": "成本分析",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "你如何分析一个产品的盈利能力，并据此给出定价建议？",
        "reference_points": [
            "成本结构拆分：固定成本 vs 变动成本、直接 vs 间接，建立单位经济模型（Unit Economics）",
            "关键指标：毛利率、贡献毛利、盈亏平衡点、CAC/LTV",
            "定价逻辑：成本加成、价值定价、竞争导向，结合需求价格弹性",
            "敏感性分析：销量/成本/价格变动对利润的影响",
            "战略取舍：引流品与利润品的组合，避免只看单品毛利"
        ],
        "hints": "要有单位经济模型意识"
    },
    {
        "job_category": "财务审计", "question_type": "PROFESSIONAL", "skill_name": "内控审计",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "如果你发现某部门存在费用报销舞弊的迹象，你会如何调查与处置？",
        "reference_points": [
            "保护证据与保密：小范围、留痕，避免打草惊蛇与证据灭失",
            "数据分析定位异常：拆单规避审批、连号发票、非工作时间、同一供应商高频、金额阈值聚集",
            "穿行测试与抽样复核：核对发票真伪、审批链、业务真实性",
            "访谈与事实认定：给当事人申辩机会，客观中立，不主观定罪",
            "处置与整改：依规处理、追偿，完善制度（审批矩阵、系统校验、轮岗、举报机制）"
        ],
        "hints": "考察职业审慎与合规程序"
    },
    {
        "job_category": "财务审计", "question_type": "PROFESSIONAL", "skill_name": "预算管理",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "如何编制一份既科学又能被业务部门接受的年度预算？",
        "reference_points": [
            "方法选择：增量预算 vs 零基预算 vs 滚动预算，按业务成熟度选用",
            "自上而下与自下而上结合：战略目标分解 + 业务实际填报，多轮对齐",
            "假设透明：把驱动因子（增长、单价、人效）显性化，便于复盘",
            "弹性机制：预留机动、季度滚动调整，避免预算僵化",
            "责任与激励：预算与考核挂钩但防博弈，强调业财融合沟通"
        ],
        "hints": "考察业财协同，而非纯数字游戏"
    },

    # ================= === 市场品牌 === =================
    {
        "job_category": "市场品牌", "question_type": "PROFESSIONAL", "skill_name": "品牌定位",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "为一个新消费品牌做定位，你会怎么做？你如何衡量定位是否成功？",
        "reference_points": [
            "STP：市场细分、目标人群选择、差异化定位",
            "竞争格局与空白：找可占领的心智差异点，避免同质化卖点",
            "定位表述：目标人群 + 品类 + 核心差异 + 支撑理由（RTB）",
            "落地一致性：产品、价格、渠道、传播围绕定位形成合力",
            "衡量指标：品牌认知度、第一提及率、搜索指数、溢价能力、复购与 NPS"
        ],
        "hints": "强调心智占位与一致性，不是喊口号"
    },
    {
        "job_category": "市场品牌", "question_type": "PROFESSIONAL", "skill_name": "投放增长",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "预算有限时，你如何在多渠道投放中分配预算并持续优化 ROI？",
        "reference_points": [
            "从目标人群的媒介习惯出发选渠道，而非跟风",
            "小步快跑测试：多渠道小额跑量看 CAC 与转化质量，再向高 ROI 渠道倾斜",
            "全漏斗视角：种草/曝光渠道与效果/收割渠道的配比，避免只看末端 ROI",
            "归因与增量：多触点归因/增量实验看真实贡献，警惕渠道抢归因",
            "动态优化：素材迭代、出价与人群调优、频次控制，持续降本"
        ],
        "hints": "考察增量思维与归因严谨性"
    },
    {
        "job_category": "市场品牌", "question_type": "PROFESSIONAL", "skill_name": "内容营销",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "如何策划一次能带来有效销售线索的内容营销活动？",
        "reference_points": [
            "明确目标人群与漏斗位置（拉新/培育/转化），内容服务于阶段目标",
            "价值主张：用解决真实痛点的内容（干货/案例/工具）换取留资",
            "渠道与分发：自有/赢得/付费媒体组合，SEO/社媒/KOL 协同",
            "转化路径设计：落地页、CTA、线索评分与后续培育流程",
            "效果度量：线索量、MQL/SQL 转化、单线索成本、内容 ROI"
        ],
        "hints": "内容要挂到线索与转化，而非只看阅读量"
    },
    {
        "job_category": "市场品牌", "question_type": "PROFESSIONAL", "skill_name": "危机公关",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "品牌突然在社交媒体遭遇负面舆情，你会如何应对？",
        "reference_points": [
            "快速分级与监测：判断影响范围与真实性，建立舆情监控",
            "黄金时间响应：先表态关注与调查，避免沉默发酵或傲慢回应",
            "事实为基、真诚为先：不删堵硬压，给出可验证的处理与改进",
            "统一口径与渠道：官方发声、客服话术、内部对齐，防次生危机",
            "事后修复：跟踪解决、口碑修复、复盘机制改进"
        ],
        "hints": "考察真诚与速度，切忌“删帖控评”式应对"
    },

    # ================= === 交互视觉设计 === =================
    {
        "job_category": "交互视觉设计", "question_type": "PROFESSIONAL", "skill_name": "设计流程",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "请介绍你完成一个产品设计需求的完整流程与方法论。",
        "reference_points": [
            "双钻模型：发现-定义（问题域）+ 发展-交付（方案域）",
            "需求理解：与 PM/研发对齐目标、约束、用户场景，看数据与反馈",
            "设计执行：信息架构、交互流程、原型、视觉规范、组件复用",
            "验证迭代：可用性测试、设计走查、灰度看行为数据，据反馈优化",
            "交付与协作：标注、切图、走查保证开发还原度"
        ],
        "hints": "展示以用户为中心且有验证闭环"
    },
    {
        "job_category": "交互视觉设计", "question_type": "PROFESSIONAL", "skill_name": "设计决策",
        "stage": "深度探究", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "当业务目标（如强曝光广告位）与用户体验冲突时，你如何取舍并推动决策？",
        "reference_points": [
            "回到长期价值：短期收益 vs 留存/口碑/LTV 的权衡，用数据说话",
            "寻找双赢方案：更自然的植入、频次控制、场景化触发",
            "建立护栏指标：用体验指标（跳出率、投诉、留存）量化伤害",
            "用证据推动：A/B 实验对比不同强度方案的业务与体验影响",
            "设计原则与底线：明确不可退让的核心体验，其余可协商"
        ],
        "hints": "考察用数据与实验沟通，而非主观坚持审美"
    },
    {
        "job_category": "交互视觉设计", "question_type": "PROFESSIONAL", "skill_name": "设计系统",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "为什么要建设计系统？你会如何推动它在团队真正落地？",
        "reference_points": [
            "价值：一致性、效率（组件复用）、降低沟通与研发成本、可扩展",
            "构成：设计 token、组件库、规范文档、模式指南",
            "落地策略：从高频页面切入、与前端共建组件、渐进迁移而非一次重构",
            "治理机制：版本管理、贡献流程、设计与研发协同维护",
            "度量成效：设计/研发提效、一致性走查问题下降"
        ],
        "hints": "强调落地与治理，不只是画一套组件库"
    },
    {
        "job_category": "交互视觉设计", "question_type": "PROFESSIONAL", "skill_name": "交互优化",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "举一个你通过优化交互细节显著提升转化或体验的案例。",
        "reference_points": [
            "定位问题：用漏斗数据/热力图/用户反馈找到具体卡点",
            "洞察根因：认知负荷、操作成本、反馈缺失、信任不足",
            "方案与依据：为什么这样改（减少步骤、即时反馈、默认值、进度提示）",
            "量化结果：改动前后关键指标对比（转化率/完成率/时长）",
            "沉淀方法：把经验抽象为可复用的规范"
        ],
        "hints": "用 STAR 结构 + 数据讲清价值"
    },

    # ================= === 客户成功 === =================
    {
        "job_category": "客户成功", "question_type": "PROFESSIONAL", "skill_name": "客户健康度",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "如何构建客户健康度评分体系，提前识别流失风险？",
        "reference_points": [
            "多维指标：产品使用（登录/活跃/功能渗透）、服务（工单/NPS）、商务（续约/付款/合同到期）",
            "领先 vs 滞后指标：使用下滑、关键人变动是领先信号",
            "分层运营：按 ARR/规模分级，对高风险客户主动干预",
            "阈值与自动化：规则触发预警与任务，避免人工漏判",
            "校准迭代：用实际续约结果回看模型的有效性"
        ],
        "hints": "强调预测性，而不是事后救火"
    },
    {
        "job_category": "客户成功", "question_type": "PROFESSIONAL", "skill_name": "续约增购",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "如何提升 SaaS 客户的续费率，并创造增购机会？",
        "reference_points": [
            "价值交付为核心：确保客户达成业务目标（QBR、成功计划、里程碑）",
            "全生命周期管理：onboarding 快速见效、日常活跃、续约前价值回顾",
            "识别增购信号：用量接近上限、新团队/新场景、ROI 已被验证",
            "关系经营：多干系人覆盖、Champion 培育，降低单点依赖",
            "数据驱动对话：用使用与业务成果数据支撑续约/扩容谈判"
        ],
        "hints": "续约是价值问题，不是到期催单"
    },
    {
        "job_category": "客户成功", "question_type": "PROFESSIONAL", "skill_name": "客户挽留",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "一个重要客户因产品问题非常不满并提出解约，你会如何处理？",
        "reference_points": [
            "先接情绪与事实：主动倾听、共情，快速确认问题与业务影响",
            "拉通内部：与产品/研发定级，给出临时方案与修复时间表",
            "价值挽留：回顾客户已获得的成果，提供补偿/服务/成功计划重建信心",
            "升级与跟进：明确 owner、定期同步进展，兑现承诺",
            "复盘机制：把个案转为产品/流程改进，防止复发"
        ],
        "hints": "考察跨部门拉通与信任修复"
    },
    {
        "job_category": "客户成功", "question_type": "PROFESSIONAL", "skill_name": "客户导入",
        "stage": "专业基础", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "如何设计新客户的 onboarding 流程，让客户尽快获得价值（缩短 time to value）？",
        "reference_points": [
            "明确成功定义：与客户对齐业务目标与关键场景",
            "结构化路径：账号/权限、核心功能上手、首个里程碑、价值验证节点",
            "缩短 TTV：聚焦 aha moment 关键动作，避免一次性灌输全部功能",
            "触达节奏：邮件/培训/1v1/自动化引导组合，按进度分层",
            "度量：激活率、首值达成时间、早期留存，持续优化流程"
        ],
        "hints": "核心是尽快兑现价值，而非功能罗列"
    },

    # =====================================================================
    # v2 扩充批次 P0：技术四大类补齐「每技能 EASY/MEDIUM/HARD 各 1 题」
    # （后端 18 / 前端 11 / 人工智能 16 / 大数据 12，共 57 题）
    # aliases 用于与岗位技能的归一化匹配，避免依赖子串巧合。
    # =====================================================================

    # ================= === 后端开发 · 补齐 === =================
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Java并发",
        "aliases": "Java,多线程,线程,并发编程,JUC", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "进程和线程有什么区别？在 Java 中创建一个线程有哪几种方式，你实际会选哪种？",
        "reference_points": [
            "进程是资源分配的基本单位、线程是 CPU 调度的基本单位；线程共享进程的堆与方法区，各自独立栈与程序计数器",
            "线程切换比进程切换轻量：进程切换要换页表与地址空间，线程切换只需换栈与寄存器",
            "创建方式：继承 Thread、实现 Runnable、实现 Callable + FutureTask（可拿返回值）、提交给线程池",
            "生产上应使用线程池而不是 new Thread：复用线程、控制并发数、便于监控与统一拒绝策略",
            "区分 start() 与 run()：start 会启动新线程由 JVM 调度，直接调 run 只是当前线程里的普通方法调用"
        ],
        "hints": "别只背概念，最后要落到线程池的工程实践上"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "MySQL",
        "aliases": "MySQL,数据库,SQL,InnoDB", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "一条 SQL 从客户端发出到返回结果，MySQL 内部经历了哪些阶段？",
        "reference_points": [
            "连接层：建立连接、身份认证、权限校验，连接由线程池/连接池复用（show processlist 可见）",
            "Server 层：解析器做词法语法分析、预处理器校验表与列，生成解析树",
            "优化器：基于统计信息与代价模型选择索引与连接顺序，生成执行计划（EXPLAIN 可看）",
            "执行器：按计划调用存储引擎接口逐行取数，做过滤、排序、聚合",
            "存储引擎层（InnoDB）：通过 B+ 树定位数据，必要时回表，配合 buffer pool 减少磁盘 IO",
            "查询缓存（8.0 已移除）说明：这也提示缓存粒度粗导致失效频繁，是它被弃用的原因"
        ],
        "hints": "分层讲清楚，并强调「优化器决定走哪个索引」这一点"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Kafka",
        "aliases": "Kafka,消息队列,MQ,消息中间件", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "Kafka 为什么能支撑很高的吞吐量？请从存储、网络与并发三个角度说明。",
        "reference_points": [
            "存储：顺序追加写磁盘远快于随机写；依赖 OS page cache，读操作常直接命中缓存",
            "网络：使用零拷贝（sendfile）避免内核态与用户态之间的多次数据拷贝",
            "客户端：producer 批量发送 + 压缩（batch.size、linger.ms、snappy/lz4/zstd）显著摊薄单条开销",
            "并发：Topic 按 partition 水平扩展，分区之间可并行读写，消费者组按分区并行消费",
            "索引：稀疏索引 + 分段日志（segment），用少量索引定位到目标位置，减少扫描",
            "总结：把随机写变顺序写、把多次拷贝变零拷贝、把串行变并行，三者叠加带来高吞吐"
        ],
        "hints": "三个角度都要说到，最后给一句概括"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Kafka",
        "aliases": "Kafka,消息队列,MQ,消息中间件,消息不丢,exactly-once", "stage": "深度探究",
        "difficulty": "HARD", "time_limit_sec": 240,
        "text": "如何保证 Kafka 消息不丢失、尽量不重复？请从生产端、Broker 端、消费端分别说明。",
        "reference_points": [
            "生产端：acks=all（或 -1）+ retries 足够大 + max.in.flight.requests 受控；开启幂等 producer（enable.idempotence=true）防重试导致的重复",
            "Broker 端：replication.factor ≥ 3、min.insync.replicas ≥ 2，并关闭 unclean.leader.election.enable，避免选到落后副本丢数据",
            "Broker 端：合理 flush 策略与多副本同步，注意「未刷盘宕机」与「副本不足拒绝写入」的取舍",
            "消费端：关闭自动提交，业务处理成功后手动提交 offset，避免「先提交后处理」丢消息",
            "端到端精确一次：需配合 Kafka 事务（跨分区原子写 + 消费-处理-生产在同一事务）或下游幂等写",
            "工程兜底：消息带全局唯一 ID，消费端按 ID 做幂等（去重表/唯一索引/Redis SETNX），把 at-least-once 收敛为业务上的 exactly-once"
        ],
        "hints": "三段式回答，最后一定要落到「重复不可避免，靠幂等收敛」"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "分布式事务",
        "aliases": "分布式事务,2PC,TCC,Saga,最终一致性,事务消息", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是分布式事务？在什么场景下必须考虑它，常见的实现思路有哪几类？",
        "reference_points": [
            "定义：一次业务操作需要跨多个数据库或服务修改数据，本地事务的 ACID 无法覆盖，需要额外机制保证整体一致",
            "典型场景：订单扣库存 + 扣余额 + 发券分属不同服务；跨库写入；本地库与缓存/MQ 的一致性",
            "强一致类：2PC/XA（同步阻塞、协调者单点）、TCC（Try-Confirm-Cancel，业务侵入大但性能好）",
            "最终一致类：本地消息表、RocketMQ 事务消息、Saga（长事务补偿）、最大努力通知",
            "选型依据：一致性要求、性能与可用性、业务侵入成本；多数互联网场景选最终一致性",
            "共同前提：必须可重试、可补偿，所有参与方接口幂等"
        ],
        "hints": "先讲清问题本质，再分类介绍方案，最后给选型标准"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "分布式事务",
        "aliases": "分布式事务,本地消息表,事务消息,最终一致性,幂等", "stage": "深度探究",
        "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "本地消息表与事务消息分别是如何实现最终一致性的？两者各有什么代价？",
        "reference_points": [
            "本地消息表：业务数据与「待发送消息」写在同一本地事务里，保证两者要么都成功要么都失败",
            "本地消息表：定时任务/独立投递线程扫描未发送消息并投递，成功后更新状态；失败则重试",
            "事务消息（如 RocketMQ）：先发半消息，Broker 暂存不可见；本地事务执行后 commit/rollback；超时未决由 Broker 回查本地事务状态",
            "消费端保障：消息可能重复投递，消费端必须按业务唯一键幂等",
            "代价对比：本地消息表实现简单、不依赖 MQ 特性，但需要额外的表与投递任务；事务消息省掉自建表，但强依赖 MQ 支持回查、且回查逻辑需自行实现",
            "共同风险：消息积压、死信处理、消息顺序问题（需按业务键分区）"
        ],
        "hints": "两种方案都要说清「靠什么保证不丢」和「代价是什么」"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "分布式锁",
        "aliases": "分布式锁,Redis锁,Redisson,ZooKeeper", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "为什么需要分布式锁？单机的 synchronized 为什么不够用？",
        "reference_points": [
            "synchronized/ReentrantLock 的锁状态在单个 JVM 内，多实例部署时各进程互不可见，无法互斥",
            "典型场景：秒杀扣库存、定时任务只允许一个实例执行、防止重复下单",
            "常见实现：Redis（SET NX）、ZooKeeper（临时顺序节点）、数据库（唯一索引/乐观锁）",
            "基本要求：互斥、避免死锁（必须有超时或会话机制）、可重入、高可用、性能可接受",
            "补充：能不用分布式锁就不用（如用唯一索引或幂等设计替代），锁是复杂度的来源"
        ],
        "hints": "先说清「锁范围」这个本质，再说要求与实现选项"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "分布式锁",
        "aliases": "分布式锁,Redis锁,Redisson,看门狗,Redlock", "stage": "深度探究", "difficulty": "MEDIUM",
        "time_limit_sec": 180,
        "text": "用 Redis 实现分布式锁要避开哪些坑？请说明每个坑的成因与解法。",
        "reference_points": [
            "加锁原子性：必须用 SET key value NX PX ttl 一条命令完成「判断 + 设置 + 过期」，不能用 setnx + expire 两步",
            "误删他人锁：value 存放本次持有者的唯一标识，释放时用 Lua 脚本「先比对 value 再删除」，保证原子",
            "业务超时导致锁提前失效：评估业务耗时，或使用看门狗（Redisson）自动续期；续期必须在持锁线程存活期间进行",
            "可重入：用 Hash 结构记录持有者与重入次数，或直接使用 Redisson 的 RLock",
            "主从切换风险：主节点加锁后未同步即宕机，从节点升主会导致锁失效；Redlock 试图缓解但存在争议，强一致场景建议用 ZooKeeper/etcd",
            "兜底：即使锁失效，业务层也应通过幂等或乐观锁保证正确性，不能把正确性完全押在锁上"
        ],
        "hints": "逐个坑说清成因+解法，最后强调「锁不是正确性的唯一防线」"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "JVM",
        "aliases": "JVM,内存模型,堆,元空间,GC", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "JVM 的内存区域是如何划分的？哪些是线程私有、哪些是线程共享？",
        "reference_points": [
            "线程私有：程序计数器（当前字节码行号）、虚拟机栈（栈帧：局部变量表、操作数栈、动态链接、返回地址）、本地方法栈",
            "线程共享：堆（对象实例）、方法区（JDK8 起由元空间实现，存类元信息、常量、静态变量）",
            "堆内分区：新生代（Eden + Survivor S0/S1）与老年代，默认比例可调；对象优先在 Eden 分配",
            "直接内存：NIO 的 DirectByteBuffer，不归堆管但受本地内存限制，异常同样报 OutOfMemoryError",
            "OOM 表现差异：堆溢出、元空间溢出、栈深度溢出（StackOverflowError）、无法创建线程等，对应不同根因"
        ],
        "hints": "按「私有/共享」两条线划分，最后补三种内存异常的区别"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "JVM",
        "aliases": "JVM,GC,Full GC,内存泄漏,jstat,MAT", "stage": "深度探究", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "线上服务频繁 Full GC，你会如何排查并优化？",
        "reference_points": [
            "先量化再动手：开启并分析 GC 日志（频率、单次耗时、回收前后堆占用、各代回收效果）",
            "区分「内存泄漏」与「参数不合理 / 突发流量」：观察 Full GC 后老年代占用是否回落，不回落实为泄漏",
            "定位手段：jstat 看趋势，jmap + MAT/VisualVM 对比 heap dump 找大对象与 GC Roots 引用链",
            "常见根因：无界缓存（静态 Map、Guava/本地缓存未设上限）、监听器/ThreadLocal 未清理、长生命周期集合持续增长、一次性加载大文件",
            "参数与收集器：合理设置 -Xmx 与新生代比例（避免过小导致对象过早晋升）、-XX:MaxTenuringThreshold、存活对象大时选 G1/ZGC 并调 -XX:MaxGCPauseMillis",
            "验证与防复发：压测复现、上线后持续监控 GC 指标与告警，代码层增加缓存上限与过期策略"
        ],
        "hints": "强调「先量化、再区分泄漏与参数问题」，不要一上来就调参数"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Spring Boot",
        "aliases": "Spring Boot,SpringBoot,自动配置,starter", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "Spring Boot 的自动配置是如何实现的？为什么它能做到「引入依赖即生效」？",
        "reference_points": [
            "@SpringBootApplication 是三合一：@SpringBootConfiguration + @EnableAutoConfiguration + @ComponentScan",
            "@EnableAutoConfiguration 通过 @Import 引入 AutoConfigurationImportSelector，读取 META-INF/spring.factories（2.7+ 为 AutoConfiguration.imports）得到候选配置类",
            "候选类并非全部生效：由 @ConditionalOnClass / @ConditionalOnMissingBean / @ConditionalOnProperty 等条件注解按环境筛选",
            "生效结果可从外部化配置绑定：@ConfigurationProperties 把 application.yml 的配置映射为对象",
            "调试手段：启动加 --debug 输出自动配置报告，区分 Positive/Negative matches",
            "「引入依赖即生效」的本质：约定优于配置 + 条件装配 + 合理的默认值"
        ],
        "hints": "把 three-in-one、候选加载、条件筛选、配置绑定串成一条链路"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Spring Boot",
        "aliases": "Spring Boot,SpringBoot,starter,自动装配,SPI", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如果要为公司内部中间件封装一个 Spring Boot Starter，你会怎么设计？需要考虑哪些问题？",
        "reference_points": [
            "结构：自动配置类 + 配置属性类（@ConfigurationProperties 前缀统一命名）+ META-INF 自动配置注册文件",
            "开放覆盖能力：配置类上用 @ConditionalOnMissingBean，允许业务方用自定义 Bean 覆盖默认实现",
            "开关与降级：@ConditionalOnProperty 提供 enabled 开关；未配置必要参数时给出明确报错或安全默认值",
            "依赖收敛：把 starter 拆成「starter 空壳（只拉依赖）」+「autoconfigure（真正逻辑）」，避免传递不必要的依赖，避免与业务版本冲突",
            "可观测与易用：暴露健康检查/指标，提供 IDE 可提示的配置元数据（additional-spring-configuration-metadata.json），编写 README 与最小示例",
            "避免的问题：启动期做重活（拖慢启动）、循环依赖、全局静态状态、日志体系冲突"
        ],
        "hints": "要体现「可覆盖、可开关、依赖收敛」这三个工程要点"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Netty",
        "aliases": "Netty,NIO,Reactor,事件循环", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "Netty 相比 JDK 原生 NIO 解决了哪些问题？为什么它成为网络框架的事实标准？",
        "reference_points": [
            "封装了多路复用 + Reactor 线程模型（bossGroup 收连接、workerGroup 处理 IO），业务方无需手写 Selector 循环",
            "规避 JDK NIO 已知缺陷：epoll 空轮询导致 CPU 100% 的 bug、Selector 关闭异常等",
            "内存管理：ByteBuf 支持堆内/堆外与池化，读写指针分离（readerIndex/writerIndex）比 ByteBuffer 的 flip 更不易出错",
            "可扩展的 pipeline：编解码、心跳、日志、限流都以 ChannelHandler 插件式串联",
            "内置粘包拆包解码器、心跳检测、优雅关闭等生产必备能力",
            "生态成熟：Dubbo、RocketMQ、gRPC-Java、Elasticsearch 等都基于 Netty"
        ],
        "hints": "从「线程模型、内存、pipeline、内置能力」四点说，比只讲 API 更显层次"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Netty",
        "aliases": "Netty,粘包,拆包,半包,LengthFieldBasedFrameDecoder", "stage": "深度探究",
        "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "TCP 粘包与拆包是怎么产生的？Netty 提供了哪些解决方式，你会怎么选？",
        "reference_points": [
            "根本原因：TCP 是面向字节流的协议，不保留应用层消息边界；发送端合并小包（Nagle）、接收端按缓冲区读取都会打破边界",
            "表现：一次读取收到多个完整消息（粘包）、或只收到半个消息（拆包/半包）",
            "解法本质：在应用层协议里显式定界——固定长度、特殊分隔符、长度字段前缀",
            "Netty 支持：FixedLengthFrameDecoder、DelimiterBasedFrameDecoder、LengthFieldBasedFrameDecoder（最常用，需正确设置 lengthFieldOffset/lengthFieldLength/lengthAdjustment）",
            "自定义协议建议：魔数 + 版本 + 序列化方式 + 长度 + 消息体，配合 MessageToByteEncoder/ByteToMessageDecoder",
            "易错点：解码器顺序要放在业务 handler 之前；ByteToMessageDecoder 需处理「读到的数据不完整」时 resetReaderIndex 并等待更多数据"
        ],
        "hints": "先讲清「字节流没有边界」，再说解法，最后给一个你实际用过的协议格式"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Elasticsearch",
        "aliases": "Elasticsearch,ES,倒排索引,全文检索,Lucene", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是倒排索引？它为什么比「逐条文档扫描关键词」快得多？",
        "reference_points": [
            "正排是「文档 → 内容」，倒排是「词项（term）→ 包含它的文档列表（posting list）」，直接由词定位文档",
            "写入时对字段分词并做标准化（小写、去停用词、词干），建立 term 字典与 posting list",
            "复杂度：从 O(文档数 × 文档长度) 的扫描，降为「查词项 → 取交集」的集合运算",
            "加速结构：term 字典用 FST/前缀树压缩存储，posting list 用跳表支持快速求交与跳跃",
            "配套：doc_values 列式存储支撑排序与聚合；segment 不可变 + 缓存提升查询效率",
            "代价：需要额外存储、写入时建索引有开销、分词器选择直接影响召回质量"
        ],
        "hints": "核心是把「扫描」换成「查词典」，并补一句代价"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Elasticsearch",
        "aliases": "Elasticsearch,ES,分片,shard,ILM,深分页", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "ES 集群如何做容量规划与性能优化？请分别从索引设计、写入与查询三个角度说明。",
        "reference_points": [
            "索引设计：主分片数一旦创建不可改，需按数据量与增长预估；单分片建议 10~50GB，分片过多会放大集群元数据与查询扇出开销",
            "副本与可用性：副本数影响查询并发与容灾，写多读少可少副本；cluster.routing.allocation 避免热点集中",
            "写入优化：用 _bulk 批量、适当调大 refresh_interval（如 30s）、translog 落盘策略、写入期先关副本后回补",
            "查询优化：避免 from+size 深分页（改用 search_after 或 scroll）、优先用 filter（可缓存）、只取需要的字段（_source 过滤）、避免大量 wildcard/正则",
            "mapping 治理：显式定义字段类型，避免 dynamic mapping 导致字段爆炸（fields 数量上限保护），keyword/text 按用途选择",
            "冷热分层与 ILM：热节点 SSD、温冷节点大盘存储，按时间滚动索引并自动下架/删除，配合 force merge 减小 segment 数"
        ],
        "hints": "三个角度要有具体参数与取舍，别停留在名词"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Spring Cloud",
        "aliases": "Spring Cloud,Eureka,Nacos,服务注册,服务发现", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是服务注册与发现？微服务架构下为什么必须有它？",
        "reference_points": [
            "问题来源：实例地址随扩缩容、重启、迁移而动态变化，调用方无法写死 IP 列表",
            "注册：服务启动后把自身（服务名、IP、端口、元数据）写入注册中心，并通过心跳/TTL 续约",
            "发现：调用方按服务名从注册中心拿到健康实例列表（客户端发现），或经网关/负载均衡转发（服务端发现）",
            "配套能力：健康检查自动摘除故障实例、权重与灰度路由、与配置中心协同实现动态配置",
            "常见实现：Eureka（AP）、Nacos（AP/CP 可切）、Consul、ZooKeeper；K8s 环境下常用 Service + DNS 替代",
            "风险点：注册中心本身要集群高可用；缓存与推送延迟会造成短暂的脏地址，需要客户端重试与容错"
        ],
        "hints": "从「地址动态变化」这个痛点切入，再讲注册/发现/健康检查"
    },
    {
        "job_category": "后端开发", "question_type": "PROFESSIONAL", "skill_name": "Spring Cloud",
        "aliases": "Spring Cloud,熔断,降级,Sentinel,Resilience4j,限流,雪崩", "stage": "系统设计",
        "difficulty": "HARD", "time_limit_sec": 240,
        "text": "微服务调用链中如何做容错与降级？请说明超时、重试、熔断、隔离、限流各自的作用与陷阱。",
        "reference_points": [
            "超时：必须显式设置且逐层递减（上游超时应大于下游），否则线程被长期占用导致级联阻塞",
            "重试：仅对幂等操作重试，设置最大次数与退避；盲目重试会放大下游压力，形成「重试风暴」",
            "熔断：状态机 关闭→打开→半开，按错误率/慢调用比例触发；打开期间快速失败，半开放少量流量探测恢复",
            "隔离：线程池隔离或信号量隔离，把不同依赖限制在各自资源池内，避免一个慢依赖拖垮全部线程",
            "限流：按 QPS/并发/热点参数限制入口流量，保护自身；常用令牌桶、漏桶、滑动窗口",
            "降级：拒绝或返回兜底（缓存值、默认值、排队提示），优先保核心链路可用；需与业务方约定降级后的语义",
            "配套：全链路监控与告警、压测验证熔断阈值、避免「配置了但从未验证」"
        ],
        "hints": "六项能力要讲出各自「挡什么风险」和「用错会怎样」"
    },

    # ================= === 前端开发 · 补齐 === =================
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "Vue3",
        "aliases": "Vue3,Vue,ref,reactive,响应式", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "Vue 3 中 ref 与 reactive 有什么区别？分别适合什么场景？",
        "reference_points": [
            "ref 可包装任意类型（含基本类型），通过 .value 访问；在模板中会自动解包，无需写 .value",
            "reactive 只能接收对象/数组，返回 Proxy，直接访问属性；对基本类型无效",
            "解构陷阱：直接解构 reactive 对象会丢失响应性，需要用 toRefs / toRef 或改用 ref",
            "替换整体对象：ref 可以直接 .value = newObj，reactive 不能整体替换（会断开代理）",
            "实践建议：基本类型、需要整体替换、需要跨组件传递时用 ref；表达一个内聚的对象状态时用 reactive",
            "性能相关：shallowRef / shallowReactive 可避免深层代理，适合大对象或第三方实例"
        ],
        "hints": "要点出「解构丢响应性」和「reactive 不能整体替换」这两个实际坑"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "TypeScript",
        "aliases": "TypeScript,TS,interface,type,类型系统", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "TypeScript 中 interface 与 type 有什么区别？你会在什么场景下选哪一个？",
        "reference_points": [
            "interface 支持声明合并（同名接口自动合并、便于扩展第三方类型），type 同名字面量会报错",
            "type 能力更强：可表达联合、交叉、元组、条件类型、映射类型、模板字面量类型",
            "interface 用 extends 继承，type 用 & 交叉；交叉在冲突属性上可能得到 never，需要注意",
            "两者在对象结构描述上大多可互换；都只在编译期存在，运行时被擦除",
            "选型建议：描述对象结构/需要开放扩展（如组件 Props、第三方库补充）用 interface；需要类型运算/联合/别名用 type",
            "团队约定优先：项目内保持一致比「哪个更好」更重要"
        ],
        "hints": "最后落到「团队约定」，能体现协作意识"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "TypeScript",
        "aliases": "TypeScript,TS,泛型,条件类型,infer,类型推导", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何用泛型与条件类型设计一个类型安全的 API 客户端？请说明关键类型技巧。",
        "reference_points": [
            "用泛型约束表达「入参决定出参」：请求类型 TReq 与响应类型 TResp 一一对应，避免返回值退化为 any",
            "条件类型 + infer：从已有 schema 中提取泛型参数（如 ExtractedResp<T> = T extends Api<infer R> ? R : never）",
            "映射类型 + keyof：根据接口定义表批量生成方法签名，减少手写重复",
            "重载或泛型默认值：为常见调用提供便捷签名，同时保留底层通用能力",
            "错误通道类型化：区分业务错误与网络错误，返回 Result<T, E> 或抛出类型化异常，避免调用方靠字符串匹配",
            "与后端契约同步：用 openapi-typescript 等从 OpenAPI 生成类型，靠 CI 校验避免前后端漂移",
            "防「类型体操过度」：可读性优先，复杂类型要写单测（如 dtslint/tsd）验证"
        ],
        "hints": "重点是「类型从契约生成 + 编译期就能发现前后端不一致」"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "Node.js",
        "aliases": "Node,Node.js,事件循环,libuv,非阻塞IO", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "Node.js 为什么适合高并发 IO 场景？它的单线程模型有什么代价？",
        "reference_points": [
            "主线程运行事件循环，IO 操作交给操作系统或 libuv 线程池（文件、DNS 等），完成后以回调/事件回到主线程",
            "非阻塞使得等待 IO 的时间可以处理其他请求，同样硬件下能承载更多并发连接，适合网关/BFF/实时通信",
            "代价一：CPU 密集型任务会阻塞事件循环，导致所有请求变慢，需拆分到 worker_threads 或独立服务",
            "代价二：单进程无法利用多核，生产用 cluster / PM2 / 容器多副本",
            "工程要点：用流（stream）处理大文件避免一次性读入内存、关注背压、监控事件循环延迟",
            "常见误区：以为「单线程就是快」，实际瓶颈常在数据库与外部依赖"
        ],
        "hints": "既要讲优势也要讲代价，体现权衡意识"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "Node.js",
        "aliases": "Node,Node.js,内存泄漏,heap snapshot,性能排查,火焰图", "stage": "深度探究",
        "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "线上 Node 服务内存持续上涨或 CPU 飙高，你会如何排查？",
        "reference_points": [
            "先建立观测：接入内存/事件循环延迟/CPU 指标，确认是持续增长（泄漏）还是突发（流量或死循环）",
            "内存排查：--inspect 连接 DevTools，取多个时间点的 heap snapshot 做对比，看哪类对象在持续增长",
            "常见泄漏根因：全局或模块级 Map/数组缓存无上限、事件监听器未移除、定时器未 clear、闭包持有大对象、Promise 链堆积",
            "CPU 排查：--prof + --prof-process，或用 0.11.x 的 clinic flame / 0x 生成火焰图，定位热点函数",
            "事件循环延迟：用 perf_hooks.monitorEventLoopDelay 或 event-loop-lag 判断是否被同步任务阻塞",
            "线上手段：预置 heapdump 触发接口（注意鉴权与磁盘）、配置 OOM 自动 dump，结合日志与变更记录定位",
            "修复验证：压测复现 → 上线后观察内存曲线是否平稳"
        ],
        "hints": "要给出「观测 → 取证 → 定位 → 验证」的完整闭环，而非罗列工具"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "CSS",
        "aliases": "CSS,响应式,flex,grid,媒体查询,布局", "stage": "专业基础", "difficulty": "MEDIUM",
        "time_limit_sec": 180,
        "text": "如何实现响应式布局？Flex、Grid 与媒体查询你如何选择？",
        "reference_points": [
            "移动优先：先写小屏样式，再用 min-width 递增断点覆盖，避免大量覆盖式代码",
            "Flex 适合一维布局（行或列的对齐与分配），Grid 适合二维布局（行列同时控制），二者常组合使用",
            "自适应能力：clamp() 控制字号、minmax(0, 1fr) 防溢出、auto-fit/auto-fill + repeat 实现卡片自动换行",
            "媒体查询 vs 容器查询：组件复用场景下容器查询（@container）比视口级媒体查询更合理",
            "配套细节：图片用 srcset/sizes 或 picture、字体用相对单位、表格与长文本的溢出处理",
            "验收要点：真机与多分辨率验证，避免横向滚动、点击区域过小、固定像素导致的错位"
        ],
        "hints": "点出「一维 Flex、二维 Grid」，并提一句容器查询会加分"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "CSS",
        "aliases": "CSS,重排,重绘,合成层,transform,性能", "stage": "深度探究", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "什么是重排（Reflow）与重绘（Repaint）？你会如何减少它们带来的性能损耗？",
        "reference_points": [
            "渲染流水线：解析 → 样式计算 → 布局（Layout/重排）→ 绘制（Paint/重绘）→ 合成（Composite）",
            "重排触发：几何属性变化（width/height/margin/position）、增删可见节点、读取布局属性导致的强制同步布局",
            "重绘触发：仅颜色/背景/可见性等不影响布局的样式变化，开销小于重排但仍消耗绘制资源",
            "合成层优化：transform、opacity 可只走合成阶段，避免重排重绘；合理使用 will-change 提前提升图层",
            "批量化操作：集中修改样式（先改 class 再统一应用）、用 DocumentFragment 批量插入、避免在循环中交替读写布局属性",
            "隔离与代价：contain / content-visibility 限制影响范围；但图层过多会增加内存与合成开销，will-change 不可滥用",
            "定位手段：DevTools Performance 面板录制，识别 Layout/Paint 耗时与强制同步布局警告"
        ],
        "hints": "要有流水线的整体视角，并指出优化手段的代价"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "前端工程化",
        "aliases": "前端工程化,依赖管理,npm,package.json,lock", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "package.json 中 dependencies 与 devDependencies 有什么区别？版本号里的 ^ 与 ~ 是什么含义？",
        "reference_points": [
            "dependencies 是运行时依赖（打包进产物或线上运行需要），devDependencies 是开发/构建/测试期依赖（如 eslint、vite、类型包）",
            "区分的意义：生产安装可用 --production 减少体积与攻击面；构建产物不应依赖 devDependencies 里的包",
            "peerDependencies 用于插件/库声明宿主版本要求（如组件库要求 vue ^3），避免重复安装或版本冲突",
            "^1.2.3 允许升级到 1.x 的最新版（不改变主版本），~1.2.3 只允许 1.2.x 的补丁升级",
            "lock 文件（package-lock.json / pnpm-lock.yaml）锁定完整依赖树，保证团队与 CI 构建可复现，应提交到仓库",
            "实践建议：CI 用 npm ci / pnpm i --frozen-lockfile 严格按 lock 安装，并定期用审计工具处理漏洞"
        ],
        "hints": "别只说定义，要落到「构建产物依赖边界」和 lock 的可复现性"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "前端工程化",
        "aliases": "前端工程化,CI/CD,发布流程,灰度,回滚,sourcemap", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何设计前端 CI/CD 与多环境发布流程？请说明质量门禁、产物管理与回滚策略。",
        "reference_points": [
            "提交与门禁：提交规范（commitlint）+ 分支策略 + PR 上跑 lint、类型检查、单测、构建，任一失败阻断合并",
            "构建产物：静态资源用内容哈希命名，配合 CDN 长缓存（immutable）；index.html 短缓存或不缓存，避免版本错配",
            "多环境：环境差异用构建期变量或运行时配置注入（config.js / window.__ENV__），禁止把测试地址硬编码进产物",
            "发布策略：先预发验证，再灰度（按用户/地域/百分比切流），灰度期重点看前端错误率与关键转化指标",
            "回滚：保留最近若干版本的制品，回滚只需切换 CDN 版本或网关路由，秒级生效；配合后端接口的向后兼容避免新旧前端混跑出错",
            "可观测：接入错误监控并上传 sourcemap（仅内部可访问），记录版本号与用户标识便于定位",
            "依赖与安全：锁文件保证可复现、定期更新依赖并扫描漏洞、避免构建脚本引入不可信源"
        ],
        "hints": "重点讲「灰度 + 秒级回滚 + 新旧版本共存」这三件事"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "浏览器原理",
        "aliases": "浏览器,DNS,渲染流程,关键渲染路径,defer,async", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "从输入 URL 到页面展示出来，中间经历了哪些主要阶段？",
        "reference_points": [
            "网络阶段：URL 解析 → DNS 查询（浏览器/系统/本地 DNS 缓存）→ 建立 TCP（含 TLS 握手）→ 发送 HTTP 请求 → 接收响应",
            "浏览器解析：HTML 自上而下解析构建 DOM；遇到 CSS 构建 CSSOM（CSS 阻塞渲染）；二者合成渲染树（Render Tree）",
            "布局与绘制：Layout 计算几何位置 → Paint 生成绘制指令 → Composite 合成图层交给 GPU 上屏",
            "JS 的影响：普通 script 会阻塞 DOM 解析，defer 延后到解析完成后按序执行，async 下载完即执行且顺序不定",
            "首屏关键路径：关键资源的体积与串行请求数直接决定 FCP/LCP，优化方向是减少关键资源、提前预连接/预加载",
            "补充：现代浏览器有预加载扫描器、HTTP/2 多路复用、缓存命中可跳过网络阶段"
        ],
        "hints": "按「网络 → 解析 → 布局绘制 → 合成」讲，最后提关键渲染路径"
    },
    {
        "job_category": "前端开发", "question_type": "PROFESSIONAL", "skill_name": "浏览器原理",
        "aliases": "浏览器,HTTP缓存,强缓存,协商缓存,Cache-Control,ETag", "stage": "深度探究",
        "difficulty": "HARD", "time_limit_sec": 240,
        "text": "浏览器的 HTTP 缓存机制是怎样的？你会如何为不同类型资源设计缓存策略？",
        "reference_points": [
            "强缓存：Cache-Control（max-age、immutable、no-store、no-cache）与 Expires；命中则直接用本地副本，不发请求",
            "协商缓存：首次响应带 Last-Modified/ETag，再次请求带 If-Modified-Since/If-None-Match，未变化则返回 304 复用本地副本",
            "优先级：Cache-Control 优先于 Expires；ETag 比 Last-Modified 更精确（可识别内容未变但时间变了的情况）",
            "存储位置：memory cache 与 disk cache，浏览器按资源大小与类型自行决定；刷新（F5）与强制刷新（Ctrl+F5）行为不同",
            "策略设计：带内容哈希的 JS/CSS/字体设一年 + immutable；HTML 设 no-cache 或很短 max-age，保证入口能拿到新版本",
            "分层缓存：CDN 边缘节点、Service Worker、浏览器三级配合；CDN 缓存 key 与刷新/预热流程要纳入发布规范",
            "常见坑：忘记给 HTML 禁缓存导致发版后仍加载旧资源；URL 不变但内容变了却设长缓存；跨域与 Vary 头配置引发命中率下降"
        ],
        "hints": "要有「分层 + 按资源类型区分」的体系化回答，并说出一个踩过的坑"
    },

    # ================= === 人工智能 · 补齐 === =================
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "LLM应用",
        "aliases": "LLM,大模型,幻觉,hallucination,提示工程", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是大模型的「幻觉」？工程上有哪些常见缓解手段？",
        "reference_points": [
            "定义：模型生成了看似合理但与事实、给定材料或常识不符的内容，本质是基于概率续写而非查询事实库",
            "检索增强（RAG）：把企业知识/文档检索结果作为上下文，让回答有依据，是最常用的缓解手段",
            "提示约束：明确要求「仅依据给定材料回答、材料中没有就说不知道」，给出结构化输出格式",
            "输出校验：关键字段做规则或二次模型校验、要求给出引用出处，便于人工复核",
            "采样参数：降低 temperature/top_p 可减少发散，但会牺牲多样性，需按场景权衡",
            "产品兜底：高风险场景（医疗、法律、金额）必须有人工确认或明确免责说明，不把模型输出当事实源",
            "评估：准备带标准答案的评测集，定期统计幻觉率而不是凭感觉判断"
        ],
        "hints": "要区分「模型能力问题」与「产品兜底设计」，后者更能体现工程思维"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "LLM应用",
        "aliases": "LLM,大模型,知识库问答,RAG,Agent,方案设计", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "请为一个企业内部知识库问答系统设计完整技术方案，说明关键选型与风险。",
        "reference_points": [
            "先明确目标与指标：准确率/召回率、答案可溯源、首字时延、单次成本、覆盖的知识范围，并据此定验收标准",
            "数据接入：文档解析（PDF/Word/网页/表格）、分块策略（按语义/标题层级 + 重叠）、元数据（部门、密级、更新时间）",
            "检索链路：向量检索 + 关键词检索混合召回 → 重排（rerank）→ 上下文组装，控制 token 预算与去重",
            "权限与合规：按用户身份过滤可检索范围（行级权限），密级数据不入外部模型，敏感信息脱敏与审计日志",
            "生成层：提示中要求引用来源、无依据则拒答；结构化输出便于前端展示引用片段",
            "评估与迭代：建评测集（含边界与拒答样例），离线跑回归；线上收集点赞/点踩与人工抽检，形成闭环",
            "风险：幻觉被当作制度依据、时效性过期内容、提示注入攻击（文档中藏指令）、成本与并发突增",
            "可选增强：多轮对话的指代消解、答案缓存、按热门问题预生成、工具调用（查实时数据）"
        ],
        "hints": "要覆盖「数据 → 检索 → 生成 → 评估 → 安全」全链路，并给出风险清单"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "RAG",
        "aliases": "RAG,检索增强,向量检索,embedding,知识库", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "RAG 的基本流程是什么？它解决了什么问题，与微调相比各有什么取舍？",
        "reference_points": [
            "索引阶段：文档解析 → 分块（chunking）→ 向量化（embedding）→ 存入向量库，并可同时建关键词索引",
            "检索阶段：把用户问题向量化，召回 top-k 相关片段，可加关键词召回与重排提升精度",
            "生成阶段：把片段与问题组装成提示交给模型，要求基于材料作答并给出引用",
            "解决的问题：知识时效性（改文档即可更新，无需重训）、可溯源、降低幻觉、成本远低于持续微调",
            "RAG vs 微调：RAG 适合「知识类、更新频繁、需要引用」；微调适合「改变输出风格/格式、领域术语习惯、压缩提示」；两者可叠加",
            "关键认知：RAG 效果上限主要由检索质量决定，检索不到就无从生成"
        ],
        "hints": "最后一句「效果上限由检索质量决定」是这题的加分点"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "RAG",
        "aliases": "RAG,检索,召回,rerank,混合检索,分块", "stage": "深度探究", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "线上 RAG 系统检索结果不准，你会如何定位并优化？",
        "reference_points": [
            "先分层定位：是「该片段没被召回」还是「召回了但排序靠后」还是「召回对了但模型没用」——三者优化方向完全不同",
            "建立评估：标注问题-标准片段对，用 recall@k、MRR、命中率衡量检索环节，用答案准确率衡量端到端",
            "分块优化：按语义/标题切分、设置重叠、chunk 过大稀释语义或过小丢上下文；重要表格与列表单独处理并保留标题层级",
            "检索优化：向量模型换用更强或多语言适配版本；引入 BM25 混合检索提升专有名词、编号、代码等精确匹配能力",
            "查询侧优化：query 改写/扩展、同义与缩写归一、多路召回合并、HyDE（先生成假设答案再检索）",
            "重排：加 cross-encoder rerank 模型，只对 top-N 精排，兼顾效果与延迟",
            "过滤与元数据：按时间/部门/密级过滤，避免召回过期或无权内容；对重复文档做去重",
            "端到端打磨：控制上下文长度与顺序（把最相关内容放两端），提示中明确要求引用，必要时给 few-shot 示例"
        ],
        "hints": "一定要先区分「没召回 / 排序差 / 模型不用」三种情况"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "LangChain",
        "aliases": "LangChain,LLM框架,Chain,Agent,编排", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "LangChain 主要解决什么问题？它的核心抽象有哪些？",
        "reference_points": [
            "定位：为 LLM 应用提供统一抽象与编排能力，屏蔽不同模型供应商与工具的差异",
            "核心抽象：模型（LLM/ChatModel/Embeddings）、提示模板（PromptTemplate）、输出解析器（OutputParser）",
            "检索相关：DocumentLoader、TextSplitter、VectorStore、Retriever，构成 RAG 标准件",
            "编排与智能体：Chain（固定流程）、Tool（外部能力）、Agent（模型自主决定调用哪个工具）、Memory（对话状态）",
            "价值：快速搭原型、便于替换供应商、内置大量社区集成",
            "局限：抽象层级多导致调试困难、版本迭代快 API 变动频繁、复杂场景常需绕开框架或用 LangGraph 做显式状态机",
            "判断：简单流水线可自写几十行更可控；需要多工具/多轮规划时框架收益明显"
        ],
        "hints": "既说价值也说局限，最后给「什么时候不用它」的判断"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "LangChain",
        "aliases": "LangChain,Agent,多步规划,工具调用,trace", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何构建一个可靠、可控的多步骤 Agent？请说明规划、工具、状态与安全上的设计要点。",
        "reference_points": [
            "工具设计：接口语义清晰、参数有 schema 校验、写操作必须幂等或可回滚、按最小权限授权（只读/只写分离）",
            "规划控制：明确最大步数、超时与成本预算，超过即终止并返回已得结果，防止无限循环与费用失控",
            "状态管理：显式维护任务状态与中间结果（考虑用状态机/LangGraph 而非纯自由对话），便于恢复与调试",
            "错误处理：工具失败要捕获并让模型看到错误信息再决策；设置重试上限与退避，区分可重试与不可重试错误",
            "可观测：全链路 trace（输入输出、耗时、token、工具调用），能回放失败案例；记录模型版本与提示版本",
            "评估：准备任务级评测集（成功率、步数、成本、危险动作次数），回归验证提示或模型升级的影响",
            "安全：防提示注入（不信任检索内容与用户输入）、危险操作需人工确认、输出过滤，避免越权调用工具",
            "人机协同：关键节点（付款、删除、对外发送）引入人工审批，而不是全自动执行"
        ],
        "hints": "重点在「可控」：步数/成本上限、状态可恢复、危险动作要人工确认"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "深度学习",
        "aliases": "深度学习,过拟合,正则化,Dropout,泛化", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是过拟合？如何判断模型是否过拟合，又有哪些缓解手段？",
        "reference_points": [
            "定义：模型在训练集上表现很好但在验证/测试集上明显变差，本质是学到了训练数据中的噪声与偶然模式",
            "判断：对比训练与验证的损失/指标曲线，验证指标先降后升即为典型信号；同时看两者差距是否持续扩大",
            "数据侧：增加数据量、数据增强、清洗错误标注、缓解类别不平衡",
            "模型侧：降低模型复杂度（层数/参数量）、加入 L1/L2 正则与 Dropout、BatchNorm",
            "训练侧：早停（Early Stopping）、交叉验证、学习率与批次大小调优",
            "注意：验证集划分要防止泄漏（同一用户/同一时间段的数据不能跨训练与验证），否则指标不可信"
        ],
        "hints": "别忘了「数据泄漏会让判断失真」这个容易忽略的点"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "深度学习",
        "aliases": "深度学习,Transformer,自注意力,attention,位置编码", "stage": "深度探究",
        "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Transformer 的自注意力机制是如何工作的？相比 RNN 它为什么成为主流？",
        "reference_points": [
            "核心计算：每个位置由输入线性变换得到 Q、K、V；用 Q 与所有 K 做点积再除以 sqrt(d_k) 得到注意力权重，softmax 归一化后对 V 加权求和",
            "缩放的原因：维度大时点积方差变大，softmax 会进入饱和区导致梯度消失，除以 sqrt(d_k) 稳定梯度",
            "多头注意力：把表示切到多个子空间并行计算，让模型同时关注语法、指代、语义等不同关系，再拼接融合",
            "位置信息：注意力本身无序，需要位置编码（正弦式或可学习）或 RoPE 注入顺序信息",
            "相比 RNN：可完全并行计算，训练效率高；任意两位置的路径长度为 O(1)，长依赖建模更好，缓解梯度消失",
            "代价：复杂度随序列长度呈 O(n²)，长文本显存与算力开销大，因此出现稀疏注意力、线性注意力、滑动窗口等优化",
            "工程配套：残差连接 + LayerNorm 保证深层可训练；预训练 + 微调范式使其易于迁移"
        ],
        "hints": "公式要点到 QKV/缩放/多头/位置编码，并说出 O(n²) 这个代价"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "Python",
        "aliases": "Python,列表,元组,深浅拷贝,可变对象", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "Python 中列表与元组有什么区别？深拷贝与浅拷贝又分别是什么？",
        "reference_points": [
            "列表可变、元组不可变；元组可作为字典键（可哈希），列表不行；元组内存更小、创建更快",
            "不可变只到顶层：元组里若含列表，仍可通过列表修改内容",
            "浅拷贝（copy()、list()、切片）只复制最外层容器，嵌套的可变对象仍被共享",
            "深拷贝（copy.deepcopy）递归复制，嵌套对象也独立；代价是性能开销，且循环引用需特殊处理",
            "常见坑：函数默认参数用可变对象（def f(a=[])）会在多次调用间复用同一列表",
            "补充：赋值（b = a）根本不是拷贝，两者指向同一对象；用 is 判身份、== 判值"
        ],
        "hints": "要主动提「默认参数陷阱」，这是高频实际 bug"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "Python",
        "aliases": "Python,GIL,多线程,多进程,并发,asyncio", "stage": "深度探究", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "Python 的 GIL 是什么？它如何影响并发编程？你会如何选择并发模型？",
        "reference_points": [
            "定义：CPython 解释器中一把全局互斥锁，保证同一时刻只有一个线程执行 Python 字节码",
            "存在原因：简化内存管理与 C 扩展的线程安全；并不代表线程安全，业务层仍需加锁保护共享数据",
            "影响：CPU 密集型多线程无法利用多核，甚至因切换开销更慢；IO 密集场景下阻塞调用会释放 GIL，多线程仍有效",
            "选型：CPU 密集 → multiprocessing / 多进程（或用 C 扩展、numpy 等释放 GIL 的库）；IO 密集且高并发 → asyncio 协程；IO 密集但依赖同步库 → 线程池",
            "混合场景：进程池 + 每进程内事件循环，或用 Celery 之类的分布式任务队列横向扩展",
            "趋势：Python 3.12+ 推进 per-interpreter GIL，3.13 提供实验性的 no-GIL 构建，但生态兼容仍需时间",
            "实践提醒：不要为了「并发」盲目上多线程，先确认瓶颈在 CPU 还是 IO"
        ],
        "hints": "核心是「按 CPU 密集 / IO 密集分流」，并提一句 no-GIL 进展"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "FastAPI",
        "aliases": "FastAPI,依赖注入,Depends,Python Web", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "FastAPI 的依赖注入是怎么用的？它带来哪些好处？",
        "reference_points": [
            "用法：用 Depends() 声明依赖（函数或类），FastAPI 在请求时自动解析并注入，无需手写工厂与传递",
            "典型场景：数据库会话管理、当前登录用户解析、权限校验、分页参数、公共配置",
            "可组合：依赖可以依赖其他依赖，形成层级；也可对同一依赖声明多个（如多角色校验）",
            "资源清理：用 yield 形式的依赖，请求结束后执行 finally 中的清理（如关闭会话）",
            "可测试性：测试时用 app.dependency_overrides 覆盖依赖，注入假实现，避免真实数据库或外部服务",
            "与 Pydantic 协同：依赖的返回值会自动参与校验与文档（OpenAPI）生成"
        ],
        "hints": "要提到 dependency_overrides 这个测试利器"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "FastAPI",
        "aliases": "FastAPI,asyncio,异步,阻塞,event loop,高并发", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何用 FastAPI 支撑高并发接口？异步编程里有哪些容易踩的坑？",
        "reference_points": [
            "最关键的坑：async def 里调用阻塞函数（同步 requests、同步 ORM、time.sleep、大文件读写）会卡住整个事件循环，所有请求一起变慢",
            "正确做法：阻塞调用改为异步库（httpx、asyncpg），或用 run_in_threadpool / asyncio.to_thread 交给线程池",
            "纯 CPU 密集任务不应放在 Web 进程里，交给独立 worker 或任务队列",
            "资源与超时：数据库连接池大小要与并发匹配，所有外部调用设置超时，避免线程/连接被长期占用",
            "进程模型：uvicorn/gunicorn 起多 worker 利用多核，结合容器水平扩展；注意 worker 内的连接池是各自独立的",
            "保护自身：限流、请求体大小限制、背压与 429/503 快速失败，避免过载雪崩",
            "可观测：记录请求耗时分布与事件循环延迟，压测（locust/k6）验证而不是凭感觉",
            "优雅关闭：处理 SIGTERM，等在途请求完成或超时后再退出，避免滚动发布时大量失败"
        ],
        "hints": "一句话说到本质：async 里不能有阻塞调用"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "数据工程",
        "aliases": "数据工程,ETL,ELT,数据管道,数仓", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "ETL 与 ELT 有什么区别？在什么情况下你会选择 ELT？",
        "reference_points": [
            "ETL：先抽取、再在中间层转换、最后加载入仓；转换发生在数仓之外的处理引擎上",
            "ELT：先原样加载入仓（或数据湖），再利用数仓/湖仓自身的算力做转换；转换发生在目标端",
            "ELT 适合：云数据仓库算力弹性且便宜、源数据量大希望保留原始明细、需要快速接入新数据源",
            "ETL 适合：目标存储算力有限、合规要求敏感数据必须先脱敏/裁剪后再入仓、转换逻辑复杂且需外部工具",
            "共性要求：数据质量校验、增量抽取与幂等重跑、血缘与元数据管理",
            "现实选择：多数现代栈采用「原始层原样保留（ELT）+ 上层按层加工」，兼顾可追溯与性能"
        ],
        "hints": "关键区别是「转换发生在哪里」，并给出各自适用条件"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "数据工程",
        "aliases": "数据工程,数据管道,幂等,数据质量,调度,血缘", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何设计一条稳定可靠的数据管道？请说明幂等、调度、质量与故障恢复上的设计要点。",
        "reference_points": [
            "分层与职责：ODS 贴源保留、DWD 明细清洗、DWS 轻度汇总、ADS 面向应用；层间依赖单向，不跨层引用",
            "幂等与可重跑：按业务日期/批次分区覆盖写入，任务可安全重跑；避免「追加写」导致重复数据",
            "增量与水位：记录上次同步位点（时间戳/自增 ID/binlog 位点），处理迟到与乱序数据（保留可回补窗口）",
            "调度与依赖：用 Airflow/DolphinScheduler 等编排，显式声明任务依赖，设置 SLA 监控与超时告警",
            "数据质量：分层校验（入仓、加工、出表）——非空、唯一、枚举合法、值域、环比波动、上下游行数与金额对账，失败即阻断下游并告警",
            "故障恢复：失败任务一键重跑、支持按分区回补；重要链路做双写或结果比对，避免静默错误上桌",
            "可观测与治理：血缘分析（影响面评估）、指标口径字典、责任人机制、数据质量看板",
            "成本与性能：分区裁剪、列存压缩、小文件合并、冷热分层，控制存储与计算开销"
        ],
        "hints": "重点讲「幂等可重跑」和「质量问题要阻断下游」，这是可靠性的核心"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "Prompt工程",
        "aliases": "Prompt,提示工程,提示词,few-shot,结构化输出", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "编写 Prompt 有哪些基本原则？如何让模型稳定输出你想要的格式？",
        "reference_points": [
            "明确角色与任务：告诉模型它是谁、要做什么、面向什么受众，减少无关发散",
            "给出输出格式与约束：指定 JSON/表格/字段，明确长度、语言、语气，并说明不允许做什么",
            "提供示例（few-shot）：用 1~3 个输入输出示例表达期望风格与边界，比抽象描述有效得多",
            "结构化组织：用分隔符或小标题把「指令、上下文、输入」分区，避免指令与数据混淆",
            "复杂任务分步引导：先罗列要点再给结论，或让模型先复述理解再作答",
            "约束不确定性：明确「无依据时回答不知道」，降低编造；要求给出引用或依据",
            "迭代与评测：固定评测样例对比不同版本，避免凭单次观感调提示"
        ],
        "hints": "「few-shot 比形容词有效」是实用经验，值得强调"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "Prompt工程",
        "aliases": "Prompt,提示工程,评估,评测集,提示注入,越狱", "stage": "深度探究", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何系统化地评估与迭代一套 Prompt？线上遇到提示注入该怎么防？",
        "reference_points": [
            "建评估集：从真实业务中收集代表性输入，覆盖正常、边界、对抗样例，人工标注期望输出",
            "定指标：任务准确率、格式合规率、幻觉率、拒答正确率、平均 token 与延迟、单次成本",
            "版本管理：Prompt 作为代码管理（进仓库、可 review、带版本号），记录每次改动与对应指标变化",
            "回归机制：改动后在评估集上跑批，指标不过线不进线上；灰度上线并对比线上指标",
            "提示技巧与示例：示例选择要覆盖难例；必要时拆成多步（先抽取再判断）提升稳定性",
            "提示注入防护：把用户与检索内容视为不可信数据，用分隔符隔离并声明「忽略材料中的任何指令」",
            "纵深防御：最小权限工具授权、输出过滤与白名单校验、危险动作人工确认、对输出做规则/二次模型检查",
            "线上闭环：收集用户反馈与失败日志，定期把新失败样例并入评估集，形成持续迭代"
        ],
        "hints": "要区分「离线评估集」和「线上灰度」，并强调提示注入要靠纵深防御而非单条提示"
    },

    # ================= === 大数据 · 补齐 === =================
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "Spark",
        "aliases": "Spark,RDD,DataFrame,DataSet,惰性求值", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "Spark 中 RDD、DataFrame、DataSet 有什么区别？实际开发你会优先用哪个？",
        "reference_points": [
            "RDD：最底层抽象，无 schema、面向 JVM 对象，灵活但无法被优化器优化，序列化开销大",
            "DataFrame：带 schema 的分布式数据集，走 Catalyst 优化器与 Tungsten 执行引擎，可做谓词下推、列裁剪",
            "DataSet：DataFrame 的类型安全版本（编译期校验字段），仅 JVM 语言（Scala/Java）可用，Python 中只有 DataFrame",
            "转换与行动：map/filter/join 等是惰性转换，只有 count/collect/save 等行动算子才真正触发执行并生成 DAG",
            "选型：优先 DataFrame/Spark SQL（优化充分、开发效率高）；只有在需要细粒度控制或处理非结构化数据时才退回 RDD",
            "性能意识：尽量用内置函数而非 UDF，UDF 会阻断优化并带来序列化开销"
        ],
        "hints": "要点出「UDF 会阻断优化器」这个实战结论"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "Spark",
        "aliases": "Spark,数据倾斜,skew,broadcast join,加盐,repartition", "stage": "系统设计",
        "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Spark 作业出现数据倾斜，你会如何定位与解决？",
        "reference_points": [
            "定位：打开 Spark UI 看 Stage 中 task 的耗时与输入数据量分布，少数 task 明显偏大即为倾斜；对比 shuffle read size 与记录数",
            "常见成因：join/groupBy 的 key 分布不均、热点 key（如 null、默认值、大商户）、join 一侧包含大量重复键",
            "小表广播：小表用 broadcast join 避免 shuffle，直接消除该 join 的倾斜",
            "热点 key 单独处理：把占比极高的 key 过滤出来单独计算，再与其他结果合并",
            "加盐打散：对倾斜 key 加随机前缀先做两阶段聚合（局部聚合后再去前缀合并），或对两侧同时加盐（需扩容另一侧）",
            "提高并行度：适度增加 shuffle 分区数，让每个 task 数据量更小（注意分区过多会带来小文件与调度开销）",
            "引擎侧：开启 AQE（spark.sql.adaptive.enabled）让其自动合并小分区并处理倾斜 join",
            "不要做的事：盲目 repartition 或全量 collect，可能让问题更糟"
        ],
        "hints": "要有「先定位、再按成因选方案」的层次，把 broadcast 与加盐讲清楚"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "Flink",
        "aliases": "Flink,Spark Streaming,流处理,事件时间,水位线", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "Flink 与 Spark Streaming 的核心区别是什么？各自的适用场景如何？",
        "reference_points": [
            "处理模型：Flink 是原生流处理（每条记录即处理），Spark Streaming 本质是微批（按时间窗口切分小批次）",
            "延迟：Flink 可达毫秒/亚秒级，Spark Streaming 受批次间隔限制通常在秒级",
            "时间语义：Flink 区分事件时间与处理时间，用 Watermark 处理乱序，窗口语义更完整",
            "状态与容错：Flink 内置有状态计算与基于 Checkpoint/Savepoint 的精确一次保障，状态可管理、可迁移",
            "选型：低延迟、复杂事件处理、CEP、实时风控与实时特征 → Flink；已重度使用 Spark 生态、准实时（秒级）且与离线逻辑复用 → Spark Structured Streaming",
            "生态与成本：Spark 统一批流、团队学习成本低；Flink 运维与状态调优要求更高"
        ],
        "hints": "核心是「原生流 vs 微批」，最后给选型建议而非只讲概念"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "Flink",
        "aliases": "Flink,Checkpoint,状态后端,barrier,状态,RocksDB", "stage": "深度探究",
        "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Flink 的 Checkpoint 机制是如何工作的？它如何保证精确一次语义？",
        "reference_points": [
            "基本原理：借鉴 Chandy-Lamport 算法，JobManager 周期性注入 Barrier，Barrier 随数据流向下游传递",
            "对齐：算子收到所有输入流的同一编号 Barrier 后才做快照（对齐），保证快照是一致性切面；反压会拖慢 Checkpoint",
            "状态后端：Memory/FileSystem/RocksDB，状态大时用 RocksDB 增量 Checkpoint 降低开销",
            "端到端精确一次：需要 Source 可重放（如 Kafka offset）+ 状态一致性快照 + Sink 支持事务或幂等（两阶段提交 Sink）",
            "恢复：从最近一次成功 Checkpoint 恢复状态并从记录的位点重放，作业内状态与位点保持同一快照因此不重不漏",
            "运维关注点：Checkpoint 间隔与超时、状态大小与增长趋势、失败次数与耗时，超时频繁需排查反压与状态膨胀",
            "Savepoint：面向升级/迁移的手动快照，与 Checkpoint 用途不同"
        ],
        "hints": "三个必要条件（可重放 Source、一致性状态、事务/幂等 Sink）一定要说全"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "Hive",
        "aliases": "Hive,内部表,外部表,分区,元数据", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "Hive 的内部表与外部表有什么区别？生产上你会怎么选择？",
        "reference_points": [
            "内部表（Managed Table）：drop 时同时删除元数据与 HDFS 上的数据",
            "外部表（External Table）：drop 时只删元数据，数据文件保留，需手动清理",
            "关键差异在于「数据所有权」：外部表认为数据不由 Hive 独占，适合多引擎共享或与其他系统共用的数据",
            "生产建议：原始数据层（ODS）与需要被 Spark/Presto 等共享的表用外部表，避免误删伤及源头；中间计算表可用内部表便于自动清理",
            "配套概念：分区裁剪（按 dt/region 分区）与分桶（便于抽样与 join 优化）直接决定查询性能",
            "补充：Hive 只负责元数据与 SQL 解析，实际执行落在计算引擎（MapReduce/Tez/Spark）"
        ],
        "hints": "一句话总结差异：数据归谁所有、drop 会不会删数据"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "Hive",
        "aliases": "Hive,慢SQL,执行计划,小文件,map join,ORC", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "一个 Hive SQL 跑得特别慢，你会如何排查与优化？",
        "reference_points": [
            "先看执行计划与算子：EXPLAIN（或 EXPLAIN EXTENDED）确认 stage 数、是否发生全表扫描、join 方式与是否走了分区裁剪",
            "分区与谓词下推：确保 where 条件命中分区字段，避免在分区字段上使用函数导致无法裁剪",
            "小文件问题：大量小文件会让 task 数暴增、调度与打开文件开销大，需先合并（或写入时控制并行度与压缩）",
            "join 优化：小表用 map join（广播）避免 shuffle；大表 join 注意数据倾斜，热点 key 加盐或单独处理",
            "存储格式：改用 ORC/Parquet 列存 + 合适压缩（zstd/snappy），配合列裁剪与向量化执行",
            "资源与并行度：调整 reducer 数量、内存与并行度参数（结合数据量估算，避免过多小 task 或过少导致长尾）",
            "数据倾斜：查看 task 耗时分布，局部聚合（先 group by 加盐再合并）是常用手段",
            "长期治理：把高频慢查询沉淀为分层宽表或预聚合表，而不是每次都即席重算"
        ],
        "hints": "要有「先看执行计划」的习惯，最后落到分层预聚合的长期治理"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "SQL",
        "aliases": "SQL,索引,数据库,查询优化,B+树", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是索引？为什么索引能加速查询？它的代价是什么？",
        "reference_points": [
            "本质：为某一列（或组合列）额外维护一份有序的数据结构（常见 B+ 树），用空间与维护成本换取查找效率",
            "加速原理：把全表扫描 O(n) 变为树高次的 O(log n) 定位，大幅减少读取的数据页数量",
            "代价一：写入变慢——每次 insert/update/delete 都要同步维护索引，事务开销变大",
            "代价二：占用额外存储空间；索引过多还会干扰优化器选择与加载进 buffer pool 的效率",
            "使用要点：最左前缀原则（联合索引）、区分度高的列优先、避免在索引列上做函数运算或隐式类型转换导致失效",
            "补充：覆盖索引可避免回表；选择合适的索引比「越多越好」更重要"
        ],
        "hints": "要有「用空间和写入成本换读性能」的权衡表达"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "SQL",
        "aliases": "SQL,慢查询,执行计划,explain,索引优化", "stage": "深度探究", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "线上有一条慢 SQL，请给出你的完整排查与优化流程。",
        "reference_points": [
            "先复现与量化：从慢查询日志取出完整语句与参数，在预发环境用真实参数执行并记录耗时与扫描行数",
            "看执行计划：EXPLAIN/EXPLAIN ANALYZE 关注 type（是否 all/index/ref/range）、key（实际用的索引）、rows（预估扫描行数）、Extra（是否 using filesort/temporary）",
            "定位根因：缺少合适索引、索引失效（函数/隐式转换/前导列未用）、回表过多、join 顺序不当、排序与分组无法用索引、深分页",
            "SQL 改写：避免 select *、把子查询改成 join、用 EXISTS 替代 IN（视情况）、分页用游标/延迟关联替代大 offset",
            "索引调整：按查询模式建联合索引并保证最左前缀，覆盖索引消除回表；用完之后评估冗余索引是否可以删除",
            "统计信息：确认统计信息是否过期导致优化器误判（更新统计信息或强制索引）",
            "架构层面：热点数据加缓存、读写分离、大表分库分表或归档历史数据",
            "验证与防复发：改动前后做对比压测，把慢查询纳入监控与告警，上线前 review SQL"
        ],
        "hints": "要有完整闭环：复现 → 执行计划 → 根因 → 改写/索引 → 验证"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "数据仓库",
        "aliases": "数据仓库,数仓分层,ODS,DWD,DWS,ADS", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "为什么数据仓库要分层？ODS、DWD、DWS、ADS 分别承担什么职责？",
        "reference_points": [
            "分层价值：解耦与复用（加工逻辑只写一次）、降低重复计算成本、便于定位问题与权限管理、新需求可基于已有中间层快速响应",
            "ODS：贴源层，保持与原业务系统一致的结构与粒度，只做必要的同步与轻微清洗，便于回溯",
            "DWD：明细层，做清洗、去重、维度退化与一致性处理，形成统一口径的明细事实",
            "DWS：汇总层，按主题/维度做轻度聚合，形成宽表，供多部门复用",
            "ADS：应用层，面向具体报表、指标与大屏，按业务需求组织，可直接对接 BI",
            "原则：层间单向依赖，不跨层引用；表命名与责任人明确；公共维度保持一致（一致性维度）",
            "补充：分层不是越多越好，小团队可从 ODS+DWD+ADS 三层起步"
        ],
        "hints": "讲清「每层解决什么问题」，最后补一句「分层不是越多越好」"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "数据仓库",
        "aliases": "数据仓库,维度建模,星型模型,雪花模型,事实表,SCD", "stage": "深度探究",
        "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "什么是维度建模？星型模型与雪花模型如何选择？",
        "reference_points": [
            "核心概念：事实表存度量与维度外键（可加性指标），维度表存描述性属性，便于按维度切片分析",
            "星型模型：维度表不做规范化、适当冗余，join 层数少、查询性能好、易理解，是数仓主流选择",
            "雪花模型：维度进一步规范化拆表，节省存储、减少冗余，但 join 变多、查询复杂、性能更差",
            "选型依据：以查询性能与易用性优先选星型；存储成本敏感或维度层次复杂、变更频繁时可局部雪花化",
            "缓慢变化维（SCD）：类型 1 直接覆盖、类型 2 保留历史版本（加生效/失效时间，可做历史回溯），按业务是否需要追溯历史选用",
            "一致性维度与总线矩阵：跨主题复用同一套维度定义，避免同名不同义",
            "落地提醒：建模要基于实际查询模式，而不是把业务库表照搬过来"
        ],
        "hints": "要落到「按查询模式决定」，并提一句 SCD 类型 2 的适用场景"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "数据清洗",
        "aliases": "数据清洗,缺失值,异常值,去重,标准化", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "数据清洗通常要处理哪些问题？处理时要注意什么？",
        "reference_points": [
            "缺失值：区分随机缺失与系统性缺失；可删除、均值/中位数填充、前向填充或标记为未知（避免用填充值掩盖问题）",
            "异常值：用分位数、3σ、业务阈值识别；先判断是错误数据还是真实极端值，不要一律删除",
            "重复数据：按业务主键或组合键去重，保留最新或最完整的一条，并记录去重规则",
            "格式与标准化：时间格式统一、单位统一、枚举值归一（如「男/男性/1」统一）、编码与字符集处理",
            "文本清洗：去空白、去特殊字符、统一大小写，注意不要误删有意义的符号",
            "关键原则：清洗规则要显式记录并可追溯（规则即文档），保留原始层数据，清洗过程可重跑",
            "风险：过度清洗会引入偏差；填充与删除都会改变分布，需评估对下游指标的影响"
        ],
        "hints": "强调「保留原始层 + 规则可追溯」，这是可治理性的关键"
    },
    {
        "job_category": "大数据", "question_type": "PROFESSIONAL", "skill_name": "数据清洗",
        "aliases": "数据清洗,数据质量,口径,校验,血缘,告警", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "面对来源多、口径不一致的数据，如何建立一套可信的数据质量体系？",
        "reference_points": [
            "先统一定义：建立指标字典与数据标准（字段含义、单位、枚举、口径、责任人），从源头消除「同名不同义」",
            "质量维度建模：完整性、唯一性、及时性、一致性、有效性、准确性，逐维度定义可执行的规则与阈值",
            "分层校验与关卡：入仓校验（结构、格式、主键唯一）→ 加工校验（口径一致性、勾稽对账）→ 出表校验（指标波动、上下游行数与金额对账）",
            "失败即阻断：关键校验失败要阻断下游任务并立即告警，避免错误数据静默上桌",
            "波动监控：与历史同期/环比对比，用统计阈值识别异常，而不是只看固定阈值",
            "归因与闭环：告警要带责任人与处置指引，形成「发现-定位-修复-复盘」闭环，并记录问题台账",
            "血缘与影响分析：上游变更时能快速算出受影响的下游报表与任务",
            "度量与运营：输出数据质量分看板，纳入日常运营考核，避免体系建完无人维护"
        ],
        "hints": "要点出「失败阻断下游」和「血缘影响分析」，这两条最能体现体系化"
    },

    # === 补齐：RAG / FastAPI / 数据工程 的原题难度非 MEDIUM（分别为 HARD/HARD/EASY），此处补中档 ===
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "RAG",
        "aliases": "RAG,分块,chunking,向量库,embedding,HNSW", "stage": "专业基础", "difficulty": "MEDIUM",
        "time_limit_sec": 180,
        "text": "在 RAG 中你如何设计文档分块策略、又如何选择向量库与索引？",
        "reference_points": [
            "分块粒度：过小会丢失上下文、过大则语义被稀释且浪费 token，需按文档类型（制度条款、FAQ、技术手册）分别设定",
            "切分方式：优先按结构（标题层级、段落、表格边界）与语义切分，而不是固定字符数硬切",
            "重叠与元数据：块间保留 10%~20% 重叠避免语义断裂；每块带来源、标题路径、更新时间等元数据以支持过滤与引用展示",
            "特殊内容：表格与代码块整体保留并补充标题，避免被切断后失去意义",
            "向量库选型：小规模可用 pgvector/Redis 复用现有基础设施；数据量大或要求高吞吐再上 Milvus/Qdrant/ES kNN，重点评估运维成本与生态",
            "索引类型权衡：HNSW 召回高但内存占用大、IVF/PQ 省内存但精度与调参成本更高；按召回目标与延迟预算选择",
            "成本与迭代：embedding 维度与模型规模影响成本；分块与索引参数应有评估集驱动，而不是凭直觉固定"
        ],
        "hints": "分块与选型两块都要讲，最后强调「用评估集驱动参数」"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "FastAPI",
        "aliases": "FastAPI,中间件,中间件洋葱模型,异常处理,请求生命周期", "stage": "深度探究",
        "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "FastAPI 的请求生命周期是怎样的？中间件、依赖与异常处理分别在什么时机执行？",
        "reference_points": [
            "整体流程：ASGI 服务器接收 → 中间件（洋葱模型：请求先进后出，响应后进先出）→ 路由匹配 → 依赖解析与校验 → 端点函数 → 响应模型序列化 → 返回",
            "依赖解析：在端点函数执行前完成，可嵌套；依赖中抛出的异常同样会进入异常处理流程",
            "校验失败：请求体/参数不符合 Pydantic 模型时返回 422，由框架统一处理，不需要手写",
            "异常处理：HTTPException 与自定义异常处理器（@app.exception_handler）按类型匹配；注意请求校验错误专用的 RequestValidationError 处理器",
            "中间件与依赖的差异：中间件的 try/except 能覆盖依赖与端点抛出的异常，而依赖内部的异常无法被「依赖自身之外的中间件顺序」之外捕获——实际排查时要先确认异常发生在哪一层",
            "后台任务：BackgroundTasks 在响应返回之后执行，适合发通知、写日志，不适合长耗时或需要返回结果的任务",
            "可观测接入点：请求 ID、耗时统计、鉴权通常放在中间件；业务级校验放在依赖"
        ],
        "hints": "把「洋葱模型」和「异常在哪一层被捕获」讲清楚，这是排查问题的关键"
    },
    {
        "job_category": "人工智能", "question_type": "PROFESSIONAL", "skill_name": "数据工程",
        "aliases": "数据工程,特征工程,特征一致性,Feature Store,训练服务偏差", "stage": "深度探究",
        "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "如何保证离线训练用的特征与线上推理时计算的特征完全一致？",
        "reference_points": [
            "问题本质：训练-服务偏差（train-serving skew）——离线用批处理算、线上用实时算，两套代码或两套口径必然产生差异",
            "统一计算逻辑：同一份特征定义与转换代码在离线与线上复用（尽量共用实现或至少共用配置与测试用例）",
            "时间点正确性：构造训练集时必须按「当时的可得信息」取值（point-in-time join），否则会把未来信息泄漏进特征，导致离线虚高",
            "Feature Store：统一注册特征，提供离线存储（历史，用于训练回填）与在线存储（最新值，用于低延迟查询），保证同源",
            "一致性校验：抽样对比同一实体在离线与线上计算出的特征值，差异超阈值即告警",
            "上线后监控：监控特征分布漂移、缺失率与取值范围，异常时定位是上游数据问题还是计算逻辑变更",
            "变更管理：特征口径变更要走版本管理与回填流程，避免新旧特征混用"
        ],
        "hints": "要说出「point-in-time 避免泄漏」和「离线在线抽样比对」两个可落地手段"
    },

    # =====================================================================
    # v2 扩充批次 P0-3b：非技术 8 类补齐「每技能 EASY/MEDIUM/HARD 各 1 题」
    # （产品/运营/销售/人力/财务/市场/设计/客户成功，各 8 题，共 64 题）
    # =====================================================================

    # ================= === 产品经理 === =================
    {
        "job_category": "产品经理", "question_type": "PROFESSIONAL", "skill_name": "需求优先级",
        "aliases": "需求管理,需求池,需求评审,PRD", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "需求来源很多很杂，你如何管理需求收集与评审流程？",
        "reference_points": [
            "统一入口：所有需求走同一个池子（工单/表格/系统），避免散落在群聊与私聊里被遗忘",
            "来源分类：用户反馈、数据洞察、业务方、销售/客服、老板战略，分别标注来源与提出人",
            "状态流转：待评估 → 已评估 → 已排期 → 开发中 → 已上线 → 已拒绝，每个状态有明确准入条件",
            "定期评审：固定节奏的需求评审会，集中评估而非随时插队，减少研发被打断",
            "拒绝也要闭环：给出拒绝理由与替代方案，并同步给提出人，避免反复重提",
            "留痕与追溯：记录每个需求的决策依据，便于后续复盘「当初为什么这么做」"
        ],
        "hints": "重点是「统一入口 + 状态流转 + 拒绝也闭环」，别只讲怎么排序"
    },
    {
        "job_category": "产品经理", "question_type": "PROFESSIONAL", "skill_name": "需求优先级",
        "aliases": "需求优先级,RICE,WSJF,需求排序,排期", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何建立一套可量化、可复用、多方都认的需求优先级机制？",
        "reference_points": [
            "与目标强绑定：所有需求先回答「服务于哪个北极星指标或战略方向」，脱离目标的直接出局",
            "统一评分模型：选定 RICE 或 WSJF 等模型，公开评分维度与权重，让排序可被检验而非靠话语权",
            "平衡短期与长期：为战略投入与技术债预留固定配额（如每迭代 20%），避免被紧急需求挤空",
            "区分事实与假设：每个评分项标注数据来源与置信度，低置信度的先做小成本验证而不是直接排期",
            "机制化落地：评审委员会 + 固定节奏 + 明确的争议升级路径（谁在什么条件下有一票决定权）",
            "反脆弱设计：定期回看排序准确率（做完的需求是否真的产生了预期价值），据此校准权重",
            "常见退化的信号：机制沦为事后背书、所有人都给自己打满分、没人愿意认领低分需求"
        ],
        "hints": "要讲清「可量化 + 有争议解决路径 + 会自我校准」，这是机制能否活下来的关键"
    },
    {
        "job_category": "产品经理", "question_type": "PROFESSIONAL", "skill_name": "用户洞察",
        "aliases": "用户调研,用户访谈,需求验证,用户研究", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "做用户访谈时，你会怎么设计问题？",
        "reference_points": [
            "问过去的具体行为，不问未来的意愿：\"你上次遇到这个问题是怎么做的\" 远优于 \"你会不会用这个功能\"",
            "避免引导性和假设性问题（\"你是不是觉得这个很难用\"），改用开放式提问",
            "用追问挖深：连续问为什么（5 Whys），把表层抱怨追到真实场景与动机",
            "关注场景五要素：什么时候、在哪里、和谁、想做什么、结果如何",
            "样本要分层：重度/轻度/流失用户都要覆盖，避免只访谈满意用户",
            "三角验证：访谈结论要用埋点数据或问卷交叉验证，不能只凭几次对话下结论"
        ],
        "hints": "核心是「问行为不问意愿」，最后提一句三角验证"
    },
    {
        "job_category": "产品经理", "question_type": "PROFESSIONAL", "skill_name": "用户洞察",
        "aliases": "用户洞察,用户画像,用户旅程,洞察体系", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何建立可持续的用户洞察体系，而不是依赖零散访谈？",
        "reference_points": [
            "多源输入：定量（埋点、漏斗、留存）与定性（访谈、可用性测试、客服工单、销售反馈、应用商店评论）持续汇入同一处",
            "用户分层的动态维护：画像不是一次性交付物，需按行为与生命周期定期刷新",
            "建立用户旅程地图：识别关键触点与情绪低谷，把洞察落到具体环节而不是抽象标签",
            "双向闭环：数据发现问题 → 定性解释原因 → 形成假设 → 需求或实验验证 → 结果回流更新洞察",
            "洞察资产化：沉淀为可检索的洞察库（场景、原话、证据、结论），跨团队可复用而不是烂在个人手里",
            "警惕确认偏误：主动寻找反例与负面样本，避免只收集支持既有观点的证据",
            "组织保障：有明确的 owner 与固定节奏（如月度洞察评审），否则体系会自然荒废"
        ],
        "hints": "要有「多源输入 → 闭环验证 → 资产化」的结构，并主动提防确认偏误"
    },
    {
        "job_category": "产品经理", "question_type": "PROFESSIONAL", "skill_name": "跨团队协作",
        "aliases": "跨团队协作,需求评审,沟通协调,RACI", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "需求评审会上，研发和测试都不认同你的方案，你会怎么办？",
        "reference_points": [
            "先听完再回应：完整听取反对意见并复述确认，避免在误解上争论",
            "区分两种不同意：不理解（缺背景信息）还是不认同（有实质分歧），前者补上下文，后者找分歧根因",
            "把讨论拉回问题层：重新对齐要解决的用户问题与目标，方案只是手段，可以换",
            "对事不对人：用数据、用户原话或技术约束作为论据，而不是\"业务方要求\"",
            "控制会议节奏：无法当场达成一致的记录为待确认项，约定会后跟进时间与决策人",
            "避免当场强推或情绪化，那只会让后续协作更难"
        ],
        "hints": "给出「不理解 vs 不认同」的区分会显得很有实战经验"
    },
    {
        "job_category": "产品经理", "question_type": "PROFESSIONAL", "skill_name": "跨团队协作",
        "aliases": "跨团队协作,项目管理,RACI,干系人管理,里程碑", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "跨研发、设计、运营、法务多个团队推进一个大型项目，如何保证不延期也不扯皮？",
        "reference_points": [
            "唯一 owner：明确一个总负责人（不是委员会），其他人按 RACI 定义自己是执行、被咨询还是被通知",
            "目标对齐：把各部门的成功标准收敛到同一组业务指标上，而不是各说各话",
            "依赖与关键路径：拆出里程碑，显式标出跨团队依赖与外部约束（如法务审核周期），管理关键路径而非平均分配关注度",
            "固定节奏：周会或看板同步进度、风险与阻塞，风险清单要有 owner 与解决时限",
            "升级机制：约定阻塞多久无人处理就升级到哪一级，并规定决策时限，避免悬而不决",
            "书面留痕：会议纪要与决策记录同步给所有干系人，减少\"我以为\"式扯皮",
            "前置处理约束：合规、资源、采购这类长周期事项尽早并行启动，不要在最后阶段才暴露",
            "管理预期：主动向上同步风险与取舍，而不是等到延期才汇报"
        ],
        "hints": "「唯一 owner + 依赖显式化 + 升级机制」这三条最能体现项目把控力"
    },
    {
        "job_category": "产品经理", "question_type": "PROFESSIONAL", "skill_name": "数据分析",
        "aliases": "数据分析,指标,埋点,数据驱动", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "你会看哪些指标来判断一个功能是否健康？",
        "reference_points": [
            "核心指标：功能使用率（渗透率）、关键路径转化率、使用后的留存变化",
            "护栏指标：性能与错误率、客服投诉与卸载率，避免主指标好看但整体受损",
            "看趋势与分布：时间趋势、按人群/渠道/机型拆分，避免只看总量平均数掩盖问题",
            "区分虚荣指标与业务指标：PV/DAU 总量好看不等于功能有价值，要看是否推动了目标",
            "口径先行：指标定义与埋点可用性要提前确认，否则数据无法支撑判断",
            "相关不等于因果：结论性判断需配合实验或对照"
        ],
        "hints": "要提「护栏指标」和「拆分看分布」，体现数据素养"
    },
    {
        "job_category": "产品经理", "question_type": "PROFESSIONAL", "skill_name": "数据分析",
        "aliases": "数据分析,埋点方案,效果评估,AB测试,指标体系", "stage": "深度探究",
        "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "如何为一个新功能设计埋点方案与效果评估计划？",
        "reference_points": [
            "先定义成功再定埋点：明确假设、核心指标与判定标准，避免先埋一堆点再想怎么看",
            "事件与属性设计：统一命名规范，事件带唯一用户标识、时间、来源、页面与关键业务属性",
            "覆盖完整路径：入口曝光、点击、关键步骤、完成、失败与异常分支都要埋，否则无法定位流失环节",
            "口径文档化：每个指标的计算口径、过滤条件与负责人写清楚，保证不同人算出同一个数",
            "上线前验证：灰度环境校验埋点是否上报、字段是否缺失、是否有重复上报",
            "评估设计：确定观察周期与最小样本量，能分组对照就分组（灰度/实验组），减少外部波动干扰",
            "避免事后拼凑：上线后再补埋点会丢失早期数据，且无法回溯"
        ],
        "hints": "要强调「先定指标再定埋点」和「异常分支也要埋」"
    },

    # ================= === 用户运营 === =================
    {
        "job_category": "用户运营", "question_type": "PROFESSIONAL", "skill_name": "用户分层",
        "aliases": "用户分层,用户分群,生命周期,RFM", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "新用户和老用户的运营策略应该有什么区别？",
        "reference_points": [
            "目标不同：新用户核心是激活与尽快体验到价值（aha moment），老用户核心是留存、复购与推荐",
            "触点与频率不同：新用户需要引导与陪伴、触达可稍密；老用户更看重不被打扰与专属感",
            "内容不同：新用户讲「怎么用、能获得什么」，老用户讲「新功能、专属权益、进阶玩法」",
            "基础分层可用生命周期阶段（新手/成长/成熟/沉默/流失）或 RFM 快速切分",
            "常见错误：对所有用户群发同样内容，导致新用户看不懂、老用户嫌烦而流失",
            "分层结果要对应具体动作，否则分层没有意义"
        ],
        "hints": "落到「分层必须对应不同动作」，否则只是在做标签"
    },
    {
        "job_category": "用户运营", "question_type": "PROFESSIONAL", "skill_name": "用户分层",
        "aliases": "用户分层,RFM,人群包,自动化运营,生命周期运营", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何设计一套能真正落地运转的用户分层运营体系？",
        "reference_points": [
            "维度选择：按业务选 RFM、行为活跃度、生命周期阶段或价值贡献，避免堆砌过多维度导致无法行动",
            "阈值设定有依据：用分位数、业务经验值与损失/收益平衡来确定边界，并定期重算",
            "分层数量克制：每增加一层就多一套策略与成本，分层必须与运营动作一一对应，不能有\"无策略层\"",
            "为每层定义目标指标与触达策略（渠道、频次、内容、权益），形成 playbook",
            "自动化与更新频率：人群包按天/周刷新，规则引擎自动触发触达，减少人工拉表",
            "效果验证：对每层策略做分组对照，验证是否真的改善了该层指标，避免\"做了但没用\"",
            "组织保障：明确每层的运营责任人，纳入日常看板，否则体系上线即荒废"
        ],
        "hints": "关键在「分层必须有对应动作和责任人」，这是落地与纸上谈兵的分水岭"
    },
    {
        "job_category": "用户运营", "question_type": "PROFESSIONAL", "skill_name": "增长实验",
        "aliases": "AB测试,增长实验,实验设计,灰度", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是 A/B 测试？运营中你会怎么用它？",
        "reference_points": [
            "基本原理：把用户随机分到对照组与实验组，只改变一个变量，比较指标差异以判断因果",
            "单一变量原则：同时改多个变量无法归因，多变量需用正交实验设计",
            "避免过早下结论：需满足最小样本量与完整周期（覆盖工作日与周末），防止偶然波动误判",
            "看核心指标也看护栏指标：转化提升但投诉或卸载上升，就不是好实验",
            "显著性不是唯一标准：效应大小是否有业务意义同样重要",
            "避免多个互相干扰的实验同时跑在同一人群上"
        ],
        "hints": "要提「样本量与周期」和「护栏指标」，这是最常见的踩坑点"
    },
    {
        "job_category": "用户运营", "question_type": "PROFESSIONAL", "skill_name": "增长实验",
        "aliases": "增长实验,增长体系,假设驱动,实验平台,指标树", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何搭建一套可持续运转的增长实验体系，而不是靠灵感撞爆款？",
        "reference_points": [
            "假设驱动：每个实验都从洞察出发写成「因为…所以改…预期…指标会提升」，拒绝无假设的瞎试",
            "指标体系：北极星指标 + 驱动指标树（拆解到可干预的环节）+ 护栏指标，三者缺一不可",
            "实验能力建设：分流与埋点平台、样本量与功效计算工具、结果看板，降低单次实验的成本",
            "优先级排序：用 ICE/PIE 等模型排序实验队列，把资源投到预期收益/成本比最高的实验上",
            "统计严谨：预注册指标与周期、控制多重比较与 p-hacking，避免把随机波动当成果",
            "失败也有价值：失败实验的结论要归档，避免团队重复踩同一个坑",
            "结果沉淀：把验证有效的策略固化为产品能力或 SOP，而不是停留在某次活动里",
            "伦理与体验底线：不做欺骗性设计、不损害用户长期利益换取短期指标"
        ],
        "hints": "「假设驱动 + 指标树 + 结果沉淀」是体系化的三根柱子"
    },
    {
        "job_category": "用户运营", "question_type": "PROFESSIONAL", "skill_name": "活动复盘",
        "aliases": "活动复盘,复盘,ROI分析,效果评估", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "一次线上活动结束后，你会复盘哪些内容？",
        "reference_points": [
            "目标达成度：对照事前设定的目标看实际结果，包括核心指标与次要指标",
            "漏斗数据：曝光 → 参与 → 完成 → 转化各环节的流失率，定位卡点在哪一步",
            "拆分维度：分渠道、分人群、分时段看差异，而不是只看整体平均",
            "成本与 ROI：投入的人力、预算、资源与产出对比，算清真实收益",
            "过程动作：哪些具体做法有效、哪些无效，对应到可执行的改进项",
            "用户反馈与舆情：评论区、客服工单、社群讨论中暴露的问题",
            "结论要落到「下一场怎么改」并指定负责人与时间"
        ],
        "hints": "按「目标-漏斗-拆分-成本-改进」清单式回答，最后必须有行动项"
    },
    {
        "job_category": "用户运营", "question_type": "PROFESSIONAL", "skill_name": "活动复盘",
        "aliases": "活动复盘,复盘方法论,SOP沉淀,经验复用", "stage": "深度探究", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何让复盘真正产出可复用的方法论，而不是开一次走过场的会？",
        "reference_points": [
            "先对齐目的：明确复盘是「为了学习改进」而不是「找人担责」，否则大家只会自我保护而隐瞒真实信息",
            "用事实还原：按时间线呈现事前假设、当时决策、实际结果与外部环境变化，用数据而非印象说话",
            "区分能力与运气：把结果拆成「可复制的方法」与「不可控的外部波动」，只把前者沉淀为经验",
            "归因要具体：不写\"曝光不够\"，而写\"因为投放素材与人群不匹配，点击率低于同类活动 40%\"",
            "沉淀为资产：输出可复用的 SOP、检查清单、话术模板或素材库，而不是一份只读过一次的 PPT",
            "建立实验与复盘记录库，让后人能查、能对比、能避免重复踩坑",
            "设定验证点：把改进项写进下一场活动并对比验证，形成闭环",
            "机制层面也要复盘：如果同一个问题反复出现，说明是流程或权限问题，而不是执行不力"
        ],
        "hints": "「区分能力与运气」和「归因要具体到可执行」是这题的核心得分点"
    },
    {
        "job_category": "用户运营", "question_type": "PROFESSIONAL", "skill_name": "私域运营",
        "aliases": "私域,社群运营,企业微信,流量池", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是私域？它和公域流量有什么区别？",
        "reference_points": [
            "私域是可以反复、免费、直接触达的自有用户阵地，如企业微信、社群、公众号、自有 APP",
            "公域依赖平台分发，获客成本随竞价上涨，用户归属平台，触达受算法与规则限制",
            "私域的核心价值：降低长期获客成本、提升复购与转介绍、沉淀用户关系与数据",
            "代价与前提：需要持续的内容与服务投入，否则群会沉寂、好友会被拉黑",
            "并非所有业务都适合：低频低客单价品类做私域投入产出比往往不佳",
            "正确认知：私域不是把人拉进群就结束，而是长期经营关系"
        ],
        "hints": "要说清价值也承认代价，避免把私域讲成万能药"
    },
    {
        "job_category": "用户运营", "question_type": "PROFESSIONAL", "skill_name": "私域运营",
        "aliases": "私域,私域闭环,社群分层,复购,会员", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何设计从引流到变现的完整私域运营闭环？",
        "reference_points": [
            "引流路径：设计公域内容、包裹卡、门店、活动等钩子，并明确引流人群与筛选标准（避免为凑数引入无效用户）",
            "承接与分层：按来源、兴趣、价值分层建群或打标签，不同人群不同欢迎语与内容节奏",
            "内容与服务节奏：价值输出为主（干货、答疑、专属服务），促销为辅，控制频次避免打扰",
            "标准化动作：欢迎语、标签体系、SOP 触达、沉默用户唤醒，尽量用工具自动化减少人工",
            "变现设计：爆品引流、会员权益、复购券、社群专属价，与业务毛利结构匹配",
            "流失与沉睡识别：设定不活跃阈值与挽回动作，同时接受合理流失率",
            "度量体系：好友净增、活跃率、留存、复购率、客单价、LTV 与获客成本对比，用数据判断是否健康",
            "风险控制：合规（不得违规群发/骚扰）、账号安全、负面舆情在群内的扩散处置"
        ],
        "hints": "要有「引流-承接-内容-变现-度量」全链路，并主动提合规与打扰控制"
    },

    # ================= === 销售商务 === =================
    {
        "job_category": "销售商务", "question_type": "PROFESSIONAL", "skill_name": "销售漏斗",
        "aliases": "销售漏斗,管道管理,CRM,跟进", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "你如何管理自己的销售管道与跟进节奏？",
        "reference_points": [
            "阶段定义清晰：线索 → 商机 → 需求确认 → 方案报价 → 谈判 → 成交，每阶段有明确的准入标准",
            "每个商机都必须有下一步动作与时间：没有下一步的商机等于已经死了",
            "用量化倒推：按各阶段历史转化率计算需要多少线索才能完成目标，据此安排开拓时间",
            "定期清理僵尸商机：长期无进展的移出管道，避免虚高的管道掩盖真实缺口",
            "记录在 CRM 而非靠记忆，方便复盘与交接",
            "固定节奏复盘管道健康度：阶段分布是否合理（只堆在最前段说明推进能力不足）"
        ],
        "hints": "「每个商机必须有下一步」是这题的灵魂"
    },
    {
        "job_category": "销售商务", "question_type": "PROFESSIONAL", "skill_name": "销售漏斗",
        "aliases": "销售漏斗,转化率,销售预测,团队管理,coaching", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何用数据提升整个团队而不只是个人的销售效率？",
        "reference_points": [
            "建立基线：统计各阶段历史转化率与销售周期，作为诊断与预测的基准",
            "定位卡点环节：逐阶段对比实际与基线，判断是线索质量、需求挖掘、方案能力还是谈判环节的问题",
            "针对性干预：卡在线索质量就调整渠道与筛选标准；卡在谈判就做陪访与话术演练",
            "打法沉淀：把 Top Sales 的有效动作提炼成可复制的提问清单与话术库，而不是停留在个人经验",
            "线索分配规则：按能力与行业经验分配并保持公平，避免优质线索集中导致其他人躺平或流失",
            "预测准确性：区分 commit / best case / pipeline，避免为好看而虚报，逐步校准预测偏差",
            "激励与反作弊：指标设计要防止压单、拆单、抢单等短期博弈行为",
            "教练机制：定期一对一复盘具体商机，关注过程动作而非只问结果"
        ],
        "hints": "「先建基线再定位卡点」比直接谈激励更有说服力"
    },
    {
        "job_category": "销售商务", "question_type": "PROFESSIONAL", "skill_name": "异议处理",
        "aliases": "异议处理,客户顾虑,推进成交,再考虑", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "客户说「我再考虑考虑」，你会怎么做？",
        "reference_points": [
            "先不逼单也不立刻打折，礼貌探询真实顾虑：是价格、决策权、时机还是对方案有疑问",
            "确认决策流程：谁参与决策、大致什么时间能定，判断这是真商机还是礼貌性拒绝",
            "约定下次沟通时间，并给一个下次联系的理由（新案例、新方案、行业数据），避免\"回头再说\"变失联",
            "保持温和的联系节奏，提供价值而非催促，避免给客户压力",
            "内部同步：把该商机标记为风险商机，调整预测",
            "接受结果：若确为婉拒，保持关系留待未来机会，不纠缠"
        ],
        "hints": "核心是「探询真实顾虑 + 约定下次明确时间点」"
    },
    {
        "job_category": "销售商务", "question_type": "PROFESSIONAL", "skill_name": "异议处理",
        "aliases": "异议处理,话术库,丢单分析,价值销售", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何系统化地提炼并复用异议处理话术？",
        "reference_points": [
            "源头汇总：把丢单原因与成交过程中的常见异议分类归集（价格、功能缺失、信任、时机、竞争、决策链）",
            "结构化应对：为每类异议准备「探询澄清 → 重构价值 → 提供证据 → 推进下一步」的四段式，而不是一句怼回去的话术",
            "证据支撑：准备同行业案例、量化 ROI、第三方评测或资质证明，让价值主张可验证",
            "校准靠实战：通过陪访、录音复盘、角色扮演持续校准话术的有效性，而不是写完就发下去",
            "避免僵化：话术是脚手架不是台词，要训练销售理解原理后灵活表达",
            "回流闭环：把高频异议同步给产品与市场，产品能解决的改产品，认知不足的改内容与传播",
            "度量效果：跟踪使用新话术后该类异议的转化率变化，用数据决定是否保留"
        ],
        "hints": "「四段式结构 + 实战校准 + 回流到产品」体现的是体系而非话术集"
    },
    {
        "job_category": "销售商务", "question_type": "PROFESSIONAL", "skill_name": "业绩抗压",
        "aliases": "业绩压力,时间管理,过程指标,自我管理", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "业绩压力很大的时候，你怎么安排一天的工作？",
        "reference_points": [
            "优先做高杠杆动作：拜访、演示、报价这类直接推进成交的事，排在精力最好的时段",
            "把结果目标拆成当日可完成的过程指标（有效拜访 3 家、新触达 10 个），用可控动作替代不可控结果",
            "最难的事先做：开拓类工作容易拖延，放在上午固定时段执行",
            "保护节奏：减少无效会议与整理性工作对黄金时间的侵占",
            "及时同步：主动向主管汇报进展与卡点，而不是独自硬扛到月底",
            "保持基本作息与情绪稳定，高压期更容易因状态崩掉而崩盘"
        ],
        "hints": "「过程指标替代结果指标」是抗压的核心方法"
    },
    {
        "job_category": "销售商务", "question_type": "PROFESSIONAL", "skill_name": "业绩抗压",
        "aliases": "业绩管理,团队业绩,业绩下滑,复盘,辅导", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如果团队连续两个季度业绩下滑，你作为负责人会怎么处理？",
        "reference_points": [
            "先归因再行动：区分外部因素（市场、政策、竞品、产品竞争力）与内部因素（线索量、转化率、人员能力、心态）",
            "用漏斗数据说话：判断是量的问题还是效率的问题，避免\"全员加压\"这种无差别动作",
            "人员盘点：识别能力差距、心态问题与流失风险，对高潜与低效采取不同策略",
            "资源再分配：聚焦高潜客户与高转化渠道，缩短销售周期；必要时调整目标客户的行业与规模定位",
            "短期止血与中长期建设并行：短期抓高价值商机与存量客户增量，中长期补话术、产品与渠道能力",
            "坦诚沟通：向团队说明现状与应对计划，重设阶段性目标，避免制造恐慌或反向激励造假",
            "守住诚信底线：明确禁止压单、虚报、抢单，短期数字不能以毁掉客户信任为代价",
            "向上管理：带着归因与方案汇报，而不是只汇报坏消息"
        ],
        "hints": "「先归因、再分流动作」+「守住诚信底线」是管理者视角的关键"
    },

    # ================= === 人力资源 === =================
    {
        "job_category": "人力资源", "question_type": "PROFESSIONAL", "skill_name": "招聘效能",
        "aliases": "招聘,简历筛选,人才画像,面试安排", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "筛选简历时你会重点看什么？",
        "reference_points": [
            "硬性条件匹配：经验年限、关键技能、行业与岗位相关性，先做基本筛选再谈潜力",
            "看成果而非职责：有量化结果（提升了多少、负责多大规模）比罗列工作内容更有信息量",
            "职业连贯性：看跳槽频率与每段经历的逻辑，短期频繁变动需要面试时重点确认",
            "留疑点给面试：空窗期、职级跳跃、项目描述夸大等先记录不预判，面试中验证",
            "按岗位差异化：销售看业绩数字，研发看技术深度与项目复杂度，不能用一个模板筛所有岗",
            "避免主观偏见：学历、性别、年龄、地域不应成为筛选依据，防止违法与错失人才"
        ],
        "hints": "要有合规意识（避免歧视性筛选），这是 HR 岗位的基本底线"
    },
    {
        "job_category": "人力资源", "question_type": "PROFESSIONAL", "skill_name": "招聘效能",
        "aliases": "招聘漏斗,招聘数据分析,渠道ROI,到面率", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何用数据诊断并改善招聘漏斗的整体效率？",
        "reference_points": [
            "建立漏斗指标：简历量 → 简历通过率 → 到面率 → 面试通过率 → offer 接受率 → 试用期留存率",
            "按渠道拆解：计算各渠道的投产比（成本/到面/入职），砍掉低效渠道，把预算集中到高质渠道",
            "定位卡点：量不足就扩渠道与做雇主品牌；转化低就校准用人标准、优化 JD 与面试体验",
            "校准用人标准：要求过高会导致 offer 拒绝率高与到岗后落差，需要与用人部门对优先级达成一致",
            "缩短流程周期：反馈慢是候选人流失的主因之一，明确各环节时限并监控",
            "统一评估标准：面试官培训与结构化评分表，降低主观偏差带来的误判",
            "闭环验证：用试用期留存与用人部门满意度回看招聘质量，而不只看入职人数"
        ],
        "hints": "要按「漏斗拆解 + 渠道 ROI + 闭环验证」讲，别只讲\"多发 JD\""
    },
    {
        "job_category": "人力资源", "question_type": "PROFESSIONAL", "skill_name": "员工关系",
        "aliases": "员工关系,冲突处理,员工投诉,沟通调解", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "员工之间发生冲突，其中一方找你投诉，你会怎么处理？",
        "reference_points": [
            "分别听取双方陈述，不预设结论也不当着 A 的面评价 B",
            "核实事实：区分可验证的行为与主观感受，必要时向相关第三方了解情况",
            "判断性质：是工作方式冲突、资源争夺还是人际关系/价值观矛盾，处理方式不同",
            "引导双方直接沟通并给出可执行的约定（沟通方式、协作边界），HR 做桥梁而非裁判",
            "关注是否暴露制度或管理问题（职责不清、考核不公），那需要从机制上解决",
            "注意保密与记录；涉及骚扰、歧视、安全等红线问题必须按制度上报处理"
        ],
        "hints": "「不预设结论 + 区分性质 + 红线上报」三条要说清"
    },
    {
        "job_category": "人力资源", "question_type": "PROFESSIONAL", "skill_name": "员工关系",
        "aliases": "员工关系,组织变革,沟通方案,人员安置", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何设计一次部门合并中的沟通方案与人员安置，减少动荡？",
        "reference_points": [
            "先定业务目的与不可变边界：明确合并的原因、必须达成的协同目标，以及人事安排的底线，避免边谈边改",
            "沟通顺序：管理者先对齐 → 关键人员一对一 → 团队集体说明，避免小道消息先于正式信息",
            "坦诚范围：明确告知已知与未知（哪些已定、哪些还在评估），不承诺做不到的事，保护信任",
            "人员盘点与保留：识别关键人才与流失风险，提前一对一沟通发展路径与保留方案",
            "合规安置：岗位变更需协商一致并留痕；涉及解除要符合法定情形与补偿标准，评估特殊群体保护",
            "过渡支持：转岗技能辅导、导师安排、心理疏导，以及明确的过渡期考核方式",
            "情绪管理：允许并消化负面情绪，提供正式的发声渠道，避免公开对抗升级",
            "变革后跟踪：持续监测士气、留存与协作效率，及时修正执行中的问题"
        ],
        "hints": "「沟通顺序 + 坦诚边界 + 合规留痕」是难点，最后要有跟踪闭环"
    },
    {
        "job_category": "人力资源", "question_type": "PROFESSIONAL", "skill_name": "人才发展",
        "aliases": "新人培养,入职带教,onboarding,buddy", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "你会怎么安排一个新人入职第一周的工作？",
        "reference_points": [
            "第一天解决\"能不能开始工作\"：账号权限、设备、基础工具与必要文档",
            "明确岗位职责与近期目标，让新人知道前三个月被期待产出什么",
            "安排导师或伙伴（buddy）：负责日常答疑，比直属主管更适合承接琐碎问题",
            "给一个可在一周内完成的小任务，建立成就感与真实参与感，而不是只看资料",
            "介绍团队协作方式：沟通渠道、会议节奏、汇报关系、跨部门对接人",
            "建立反馈节奏：第一周末一次短沟通，主动问困难而不是等新人开口",
            "关注融入与心理状态，第一周是离职高发期"
        ],
        "hints": "要提到「小任务建立成就感」和「第一周是离职高发期」"
    },
    {
        "job_category": "人力资源", "question_type": "PROFESSIONAL", "skill_name": "人才发展",
        "aliases": "人才盘点,九宫格,继任计划,高潜培养", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何做人才盘点并落地继任计划？",
        "reference_points": [
            "统一评价标准：用业绩 × 潜力等维度建立统一框架（如九宫格），先定义清楚每个维度的行为锚点",
            "校准会议：由跨部门管理者共同校准评级，避免宽严不一与个人偏好，这一步是盘点公信力的关键",
            "结果要对话：与本人沟通发展期望与路径，而不是只在 HR 系统里打个标签",
            "发展手段要具体：轮岗、挑战性项目、导师制、外部课程，按个人差距量身配置",
            "关键岗位继任梯队：区分\"现在可接任\"与\"1-2 年内可接任\"，并明确准备动作与时间表",
            "与业务规划挂钩：盘点结果要能回答\"明年的新业务由谁来扛\"，否则只是人力资源的自我循环",
            "保留与激励联动：高潜识别后如果没有实际机会或激励，反而加速流失",
            "保密与风险：盘点结果严格分级可见，避免被贴上固定标签造成伤害"
        ],
        "hints": "「校准会议」和「继任梯队要区分就绪度」是这题的硬核细节"
    },

    # ================= === 财务审计 === =================
    {
        "job_category": "财务审计", "question_type": "PROFESSIONAL", "skill_name": "财务报表",
        "aliases": "财务报表,毛利率,净利率,盈利能力", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "毛利率和净利率有什么区别？两者差距大说明了什么？",
        "reference_points": [
            "毛利率 =（营业收入 − 营业成本）/ 营业收入，反映产品本身的直接盈利能力",
            "净利率 = 净利润 / 营业收入，扣除了期间费用（销售、管理、研发）、财务费用与税金",
            "差距主要来自期间费用与税负：差距大通常意味着销售/研发投入高、财务费用重，或管理费用失控",
            "两者的趋势比绝对值更重要：毛利率下滑可能是成本上升或降价竞争，净利率下滑还可能叠加费用扩张",
            "不同行业不可直接比较：软件与零售的毛利率天然不同，需在同业内对比",
            "延伸：仅看利润不够，还要看经营性现金流是否匹配"
        ],
        "hints": "要落到「差距来自哪些费用」并提醒行业不可比"
    },
    {
        "job_category": "财务审计", "question_type": "PROFESSIONAL", "skill_name": "财务报表",
        "aliases": "财务报表,财务风险,应收账款,现金流,偿债能力", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何通过财务报表识别一家公司的经营风险？",
        "reference_points": [
            "收入质量：应收账款增速显著快于收入、关联交易占比高、收入确认政策激进，都可能是虚增或回款困难的信号",
            "现金流匹配：经营性现金流长期低于净利润，说明利润没有变成现金，需查应收账款与存货",
            "偿债能力：流动比率/速动比率、有息负债规模与利息保障倍数、短期债务占比，警惕短债长投与集中到期",
            "资产质量：存货周转放缓、存货跌价准备计提不足、商誉占净资产比例过高存在减值风险",
            "盈利异常：毛利率显著高于同业且无合理解释，可能是财务造假信号；非经常性损益占比高说明主业弱",
            "关联方与担保：对外担保、资金占用、大股东质押比例，都是潜在爆雷点",
            "交叉验证：结合审计意见类型、附注披露、董监高变动与经营数据（用电量、纳税）相互印证",
            "趋势与结构并重：单期数字意义有限，连续多期的结构变化更能暴露问题"
        ],
        "hints": "要按「收入-现金流-负债-资产-异常」分块，并提一句交叉验证与审计意见"
    },
    {
        "job_category": "财务审计", "question_type": "PROFESSIONAL", "skill_name": "成本分析",
        "aliases": "成本分析,固定成本,变动成本,贡献毛利,盈亏平衡", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "固定成本与变动成本有什么区别？为什么这个区分很重要？",
        "reference_points": [
            "固定成本：在相关业务量范围内总额不随产量/销量变化（房租、固定薪资、折旧）",
            "变动成本：随业务量同比例变化（原材料、按件计酬、交易手续费）",
            "用于计算贡献毛利（收入 − 变动成本）与盈亏平衡点（固定成本 / 单位贡献毛利），回答\"卖多少才不亏\"",
            "影响定价决策：短期只要售价高于变动成本就有边际贡献，可以接受低价订单以摊薄固定成本",
            "影响经营风险：固定成本占比高的业务（如重资产、软件研发）杠杆效应强，收入波动会被放大",
            "易错点：区分是「相关范围内」的假设，产能大幅扩张后固定成本也会跳变"
        ],
        "hints": "一定要落到「盈亏平衡点」和「边际贡献」这两个用途上"
    },
    {
        "job_category": "财务审计", "question_type": "PROFESSIONAL", "skill_name": "成本分析",
        "aliases": "成本分析,产品盈利性,贡献毛利,资源配置,分摊", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何做产品线的盈利性分析并据此做资源配置决策？",
        "reference_points": [
            "分摊逻辑要合理：间接费用应按因果关系选择分摊动因（面积、工时、订单量），错误的分摊会扭曲结论",
            "多维度看贡献：按产品、客户、渠道、区域分别算贡献毛利，识别\"收入高但利润薄\"的伪明星产品",
            "识别真亏损：区分亏损是因为定价低、成本高还是分摊不合理；剔除不可分摊的沉没成本后重新判断",
            "考虑战略与协同：某些产品是引流入口或生态拼图，短期亏损但带来其他产品的收益，不能一刀切砍掉",
            "资源配置决策：砍、维持、加码要给出明确判据（增速、毛利率、战略契合度、资源占用），并说明退出成本",
            "敏感性分析：对价格、销量、成本做情景模拟，判断结论在什么区间内才成立",
            "落地联动：结论要进入预算与考核体系，否则分析报告不会改变任何实际行为",
            "避免唯短期利润论：过度砍产品会损伤长期竞争力与客户完整解决方案能力"
        ],
        "hints": "要主动提「分摊动因是否合理」和「引流产品的战略价值」，这两点最容易出错"
    },
    {
        "job_category": "财务审计", "question_type": "PROFESSIONAL", "skill_name": "内控审计",
        "aliases": "内控,内部控制,COSO,风险控制", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是内部控制？为什么企业需要它？",
        "reference_points": [
            "定义：为合理保证经营合规、资产安全、财务报告可靠与运营效率而设计的一系列流程与制度",
            "COSO 五要素：控制环境、风险评估、控制活动、信息与沟通、监督",
            "常见控制手段：不相容职务分离、授权审批、复核、实物盘点、轮岗与强制休假、系统校验",
            "解决的核心问题是\"防错防弊\"：避免无意的操作错误与有意的舞弊，同时提升流程效率",
            "成本收益平衡：控制不是越严越好，过度控制会拖慢业务，需要按风险高低分级设计",
            "认知纠偏：内控不只是财务部门的事，业务部门是控制的实际执行者"
        ],
        "hints": "提一句「控制不是越严越好」，能体现成熟度"
    },
    {
        "job_category": "财务审计", "question_type": "PROFESSIONAL", "skill_name": "内控审计",
        "aliases": "内控审计,关键控制点,穿行测试,不相容职务", "stage": "深度探究",
        "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "如何识别一个业务流程中的关键控制点？",
        "reference_points": [
            "先画流程与风险地图：把流程拆成步骤，逐步识别可能出错的环节（资金、资产、数据、合规四类风险）",
            "判断控制性质：区分预防性控制（审批、权限分离）与检查性控制（复核、对账、盘点），两者要搭配",
            "关注不相容职务分离：发起与审批、执行与记录、保管与盘点不能由同一人兼任，这是最基础也最容易缺失的一环",
            "关键控制必须可留痕：能否在系统或单据上看到\"谁在什么时候做了什么判断\"，否则无法验证执行",
            "识别控制缺失与冗余：有没有高风险环节完全没有控制，以及有没有层层审批只为免责而无实际作用的冗余控制",
            "验证执行有效性：用穿行测试从一笔真实业务走完全流程，看制度写的和实际做的是否一致",
            "输出可执行结论：给出整改优先级、责任人与期限，而不是一份问题清单"
        ],
        "hints": "「不相容职务分离」和「能否留痕」是识别关键控制点的两个抓手"
    },
    {
        "job_category": "财务审计", "question_type": "PROFESSIONAL", "skill_name": "预算管理",
        "aliases": "预算管理,预算超支,预算调整,费用控制", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "预算超支了你会怎么处理？",
        "reference_points": [
            "先查原因：区分一次性支出与趋势性超支、可控与不可控因素（市场变化、政策、突发事故）",
            "评估影响：测算对全年目标与现金流的影响，判断是否需要重新排优先级",
            "分类处理：区分必须追加（关系到核心目标）与可压缩可延后的项目，不要在总额上简单摊派",
            "走正式流程：按制度启动预算调整审批，而不是私下挪用其他科目，避免失控与合规风险",
            "与业务方沟通取舍：让业务方参与决定\"砍什么保什么\"，而不是财务单方面下指标",
            "沉淀经验：把超支原因与判断写入下一年度的预算假设，避免重复踩坑"
        ],
        "hints": "「不私下挪用、走正式调整流程」是财务岗位的专业底线"
    },
    {
        "job_category": "财务审计", "question_type": "PROFESSIONAL", "skill_name": "预算管理",
        "aliases": "预算管理,滚动预测,差异分析,业财融合,驱动因子", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何建立预算与业务联动、能快速响应变化的滚动预测机制？",
        "reference_points": [
            "从静态年度预算转向滚动预测：按季度或月度滚动更新，把预算变成动态工具而不是年初一次性博弈",
            "驱动因子显性化：把预算拆成可观测的驱动因子（用户量、客单价、人效、单位成本），便于做敏感性分析",
            "业财融合机制：业务与财务联合预测，业务负责人对数字负责，财务提供口径与方法，避免财务闭门造数",
            "差异分析要定位到因子：不是只汇报\"费用超了 10%\"，而要说明是量增、价升还是效率下降导致",
            "设置调整触发规则：明确什么情况下重排预算（如收入偏离超阈值、重大策略变化），避免频繁调整失去严肃性",
            "保持弹性的同时留缓冲：预留机动额度应对不确定，但缓冲也要在制度内管理，不能成为暗箱",
            "系统支撑：数据及时性与颗粒度决定预测速度，依赖手工收集表格永远快不起来",
            "考核联动：预测与考核的关系要设计好，否则会诱导业务方故意压低预测"
        ],
        "hints": "「驱动因子 + 业财联合 + 触发规则」是滚动预测能跑起来的三要素"
    },

    # ================= === 市场品牌 === =================
    {
        "job_category": "市场品牌", "question_type": "PROFESSIONAL", "skill_name": "品牌定位",
        "aliases": "品牌定位,差异化,心智,品牌认知", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是品牌差异化？为什么它如此重要？",
        "reference_points": [
            "差异化的本质：给用户一个在同品类中优先想起并选择你的理由，占据一个清晰的心智位置",
            "为什么重要：缺乏差异就只能比价格，陷入同质化与毛利下滑；购买决策时用户的心智是稀缺资源",
            "差异点必须用户在意：技术上独特但用户无感的价值不算差异化",
            "差异点必须真实可支撑（RTB）：能被产品、服务、供应链或历史证据验证，否则是空话",
            "切入维度：品类创新、特定人群、使用场景、功能特性、情感与服务体验",
            "差异化的代价：越窄越清晰，同时意味着放弃部分人群；传播需长期一致才能建立认知"
        ],
        "hints": "「用户在意 + 真实可支撑」这两条缺一不可"
    },
    {
        "job_category": "市场品牌", "question_type": "PROFESSIONAL", "skill_name": "品牌定位",
        "aliases": "品牌定位,品牌升级,品牌重塑,品牌资产", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "品牌进入成熟期后增长放缓，如何判断该做品牌焕新还是品牌重塑？",
        "reference_points": [
            "先诊断再动刀：通过认知调研、搜索与社交舆情、销量结构变化，判断问题是\"表达老化\"还是\"价值主张失效\"",
            "区分两种路径：焕新（保留核心定位，更新视觉、语言与媒介方式，风险低）vs 重塑（改变核心定位与目标人群，风险高、周期长）",
            "判断依据：如果用户仍认可价值只是觉得品牌\"老气\"，做焕新；如果价值主张已不被目标人群认同或市场已转移，才考虑重塑",
            "保护品牌资产：识别用户仍有记忆与情感联结的元素（符号、颜色、口号），不要为求新而全盘推翻",
            "分阶段落地：从产品、视觉、传播到渠道有序推进，避免一次性切换造成认知断层",
            "内部与渠道共识先行：员工、经销商、合作伙伴的理解与配合决定成败",
            "效果度量：认知度、第一提及率、搜索指数、好感度、溢价能力、转化与新客结构，设定验证周期而不是发完发布会就结束",
            "反面教材警示：只换 logo 和 Slogan 而没有业务与体验支撑，会被用户视为\"换汤不换药\""
        ],
        "hints": "一定要区分「焕新 vs 重塑」的判据，并强调保护品牌资产"
    },
    {
        "job_category": "市场品牌", "question_type": "PROFESSIONAL", "skill_name": "内容营销",
        "aliases": "内容营销,文案,标题,创意", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "如何写一条能吸引目标用户的标题或文案？",
        "reference_points": [
            "先明确受众与场景：对谁、在什么处境下、想解决什么问题，文案才有针对性",
            "给具体利益点而非空泛形容词：\"3 天上线一个数据看板\" 优于 \"高效便捷\"",
            "用数字、结果与对比增强可信度与可读性",
            "调动情绪或好奇可以有，但不能标题党：承诺与内容落差会伤害品牌并提高跳出率",
            "适配渠道特性：搜索场景看关键词与意图匹配，信息流看前 3 秒抓取注意力，公众号看信息密度",
            "多版本小流量测试，用点击与转化数据决定投放版本",
            "合规底线：避免绝对化用语与广告法禁用词"
        ],
        "hints": "提「标题党会伤害品牌」和「合规禁用词」会显得专业"
    },
    {
        "job_category": "市场品牌", "question_type": "PROFESSIONAL", "skill_name": "内容营销",
        "aliases": "内容营销,内容体系,内容矩阵,SEO,内容资产", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何搭建可持续的内容营销体系，而不是依赖单次爆款？",
        "reference_points": [
            "内容矩阵设计：按用户旅程阶段（认知/考虑/决策/使用）与业务目标规划主题，保证内容服务于转化而不只是刷存在感",
            "内容资产化：把一次性内容沉淀为可复用的模板、专题页、素材库与长尾 SEO 内容，持续带来自然流量",
            "生产机制：明确选题来源（用户提问、客服工单、销售异议、搜索词）、产能规划（内部团队/专家共创/外部合作）与审核流程",
            "分发与再利用：一次生产多渠道改编（图文/短视频/直播/邮件），并按渠道特性调整而非机械搬运",
            "度量体系：不能只看阅读量——要看线索量、MQL/SQL 转化、自然搜索流量与内容带来的商机，建立内容归因",
            "与产品联动：内容暴露的高频问题要回流给产品，形成内容与产品的双向改进",
            "长期主义与节奏：内容效果有累积效应，需要稳定输出与季度复盘，而不是追一次爆款",
            "防止失焦：避免为了流量做与定位无关的内容，稀释品牌认知"
        ],
        "hints": "「内容资产化 + 用线索而非阅读量度量」是区别于做流量的关键"
    },
    {
        "job_category": "市场品牌", "question_type": "PROFESSIONAL", "skill_name": "危机公关",
        "aliases": "危机公关,舆情,负面评论,投诉处理", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "社交平台上出现了针对品牌的负面评论，你的第一步做什么？",
        "reference_points": [
            "不删帖不对线：第一时间核查事实与影响范围，判断是个体投诉、真实产品质量问题还是有组织的攻击",
            "建立沟通渠道：通过官方账号或私信尽快与当事人接通，把讨论从公开广场引导到可对话的场合",
            "同步内部：告知客服、公关、业务与法务，统一口径，避免不同账号给出矛盾回应",
            "准备回应框架：先表达关注与正在核实，给出下一步时间点，不要急于辩解或推责",
            "评估升级：若涉及安全、合规、群体性投诉，立即升级到危机处理流程",
            "记录时间线：截图、链接、传播范围，为后续判断与复盘留下依据"
        ],
        "hints": "「先核查再回应」和「统一口径」是头 30 分钟的关键动作"
    },
    {
        "job_category": "市场品牌", "question_type": "PROFESSIONAL", "skill_name": "危机公关",
        "aliases": "危机公关,舆情监测,应急预案,发言人机制", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何建立危机公关的预防与响应机制？",
        "reference_points": [
            "监测与预警：覆盖主流平台与关键社区，建立舆情监测与分级标准（蓝/黄/橙/红），明确各级的响应时限与决策层级",
            "预案与演练：为主要风险场景（产品事故、数据安全、人事纠纷、合规处罚、创始人言论）预置应对框架，并定期演练与更新",
            "响应组织：成立跨部门响应小组（公关、法务、客服、业务、技术），指定唯一发言人与对外统一出口，避免多人表态",
            "响应原则：速度优先于完美，真诚优先于辩驳，事实优先于立场；先解决用户实际问题再谈形象",
            "关系资产建设：与媒体、行业 KOL、监管部门保持长期正当沟通，危机时才有可信的沟通渠道",
            "把握尺度：不删帖控评硬压，也不过度道歉自我定罪；法务判断与公关表达需协同",
            "事后修复与闭环：跟踪问题解决、修复口碑，并把危机暴露的产品与流程缺陷闭环改进",
            "复盘入库：每次危机后更新预案与风险清单，让机制随经验进化"
        ],
        "hints": "「分级预警 + 唯一发言人 + 预案演练」是机制化的三要素"
    },
    {
        "job_category": "市场品牌", "question_type": "PROFESSIONAL", "skill_name": "投放增长",
        "aliases": "投放,渠道评估,CAC,LTV,获客成本", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "如何判断一个投放渠道值不值得继续投？",
        "reference_points": [
            "看 CAC 与 LTV 的关系：获客成本要显著低于用户生命周期价值，否则规模越大亏得越多",
            "看获客质量而非只看量：后续留存、复购与客单价才是渠道优劣的真实体现",
            "看能否规模化：小预算效果好的渠道放量后成本可能急剧上升，需测试边际成本曲线",
            "归因要谨慎：末次点击归因会高估收割型渠道、低估种草型渠道，最好用增量实验验证",
            "先用小预算测试再决定加码或止损，并设定明确的止损线",
            "关注作弊与无效流量：异常高的点击率、极低停留时间、集中设备号都是信号"
        ],
        "hints": "「CAC vs LTV」和「归因会失真」是这题的两个关键点"
    },
    {
        "job_category": "市场品牌", "question_type": "PROFESSIONAL", "skill_name": "投放增长",
        "aliases": "投放,落地页优化,转化率,AB测试,表单", "stage": "深度探究", "difficulty": "MEDIUM",
        "time_limit_sec": 180,
        "text": "投放有量但转化差，你会如何优化落地页与转化环节？",
        "reference_points": [
            "先逐环节定位：曝光 → 点击 → 落地页停留 → 表单/下单 → 留资后的触达，算出各环节流失率，找最大漏点",
            "广告与落地页一致性：主图、标题与落地页首屏的信息必须咬合，错配是点击高但跳出高的主因",
            "首屏价值主张：3 秒内让人看懂\"你是谁、能解决什么问题、凭什么信你\"，信任要素（资质、案例、数据）要前置",
            "降低操作成本：表单字段最小化、减少跳转步骤、提供多种联系方式，移动端优先适配并压缩加载时间",
            "用 A/B 测试迭代：标题、主图、CTA 文案、表单长度、社会证明，每次只改一个变量并跑足样本量",
            "缩短响应时间：留资后 5 分钟内触达的接通率显著更高，需与销售流程打通",
            "警惕假象：转化提升但要关注线索质量（无效线索增加会让销售侧浪费更多时间）"
        ],
        "hints": "「先算逐环节流失率再动手」+「落地页与广告一致性」是核心"
    },

    # ================= === 交互视觉设计 === =================
    {
        "job_category": "交互视觉设计", "question_type": "PROFESSIONAL", "skill_name": "设计流程",
        "aliases": "设计流程,需求理解,设计目标,设计方法", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "接到一个设计需求后，你的第一步做什么？",
        "reference_points": [
            "先搞清楚问题而不是急着画图：与产品经理对齐目标、用户、业务约束与判定成功的指标",
            "确认范围与交付预期：是概念探索、高保真稿还是只改局部，时间与颗粒度直接影响做法",
            "收集输入：现有页面数据、用户反馈、竞品做法与相关规范，避免凭个人偏好设计",
            "列出关键假设与待验证问题，明确哪些结论需要靠数据或用户测试确认",
            "识别约束：技术可行性、品牌规范、合规与无障碍要求",
            "避免的常见错误：跳过理解阶段直接出方案，后期返工成本更高"
        ],
        "hints": "「先理解问题再出方案」是这题最想听到的态度"
    },
    {
        "job_category": "交互视觉设计", "question_type": "PROFESSIONAL", "skill_name": "设计流程",
        "aliases": "设计流程,设计规范,落地推动,多产品线,指标复用", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何推动设计规范在跨团队、多产品线中真正落地？",
        "reference_points": [
            "先统一原则与术语：在讨论组件细节前，先就设计原则与命名规范达成一致，否则各团队各说各话",
            "从高频场景切入：挑使用率最高的页面与组件做规范化，产出可直接复用的组件而不是文档",
            "设计与前端共建：设计 token 与代码同源，组件由设计与研发共同维护，避免\"设计改了代码没改\"",
            "建立贡献与评审流程：外部团队如何提交新组件、谁评审、多久响应，没有流程就没有生态",
            "版本与变更管理：破坏性变更需公告、给迁移期与兼容方案，否则会被绕开",
            "用度量证明价值：一致性走查问题数下降、设计与研发提效、需求交付周期缩短，用数据争取资源",
            "处理边界与例外：为业务特例保留申请与评估机制，避免规范僵化被整体抛弃",
            "避免大而全的重构：一次性改造所有页面往往失败，渐进式迁移更容易被接受"
        ],
        "hints": "「与前端共建 + 贡献评审流程 + 用度量证明价值」是落地的关键"
    },
    {
        "job_category": "交互视觉设计", "question_type": "PROFESSIONAL", "skill_name": "设计系统",
        "aliases": "设计系统,组件化,变体,组件库", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是组件化？为什么比在每张设计稿里重复画元素更好？",
        "reference_points": [
            "组件化的本质：把可复用的界面元素抽象为带属性的组件，通过变体覆盖不同尺寸与状态",
            "效率提升：一次修改全局生效，避免逐个页面手动调整导致的遗漏与不一致",
            "一致性：所有页面共用同一份样式来源，减少\"同一个按钮有五种圆角\"的问题",
            "协作效率：组件命名与结构清晰便于团队检索与复用，新成员上手更快",
            "交付对接：设计组件与前端组件一一对应，降低还原偏差与沟通成本",
            "代价：需要前期投入与维护，命名与结构设计不当会变成新的混乱来源"
        ],
        "hints": "既要讲效率也要讲维护成本，避免把组件化讲成纯好处"
    },
    {
        "job_category": "交互视觉设计", "question_type": "PROFESSIONAL", "skill_name": "设计系统",
        "aliases": "设计系统,design token,主题,暗色模式,变量", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何设计并维护一套可扩展的设计 token 体系？",
        "reference_points": [
            "分层设计：基础层（原始色板、间距刻度）→ 语义层（背景、文字、边框、状态色）→ 组件层（按钮主色），组件只引用语义层",
            "命名语义化：用 color-text-danger 而不是 red-500，换肤或调整色值时无需改组件",
            "主题与暗色模式：语义层是主题切换的抓手，避免业务代码里散落具体色值",
            "与代码同源：token 导出为 JSON/CSS 变量/平台配置文件，设计工具与代码共享同一份来源，杜绝手抄",
            "变更与弃用流程：新增、修改、弃用都要有版本记录与迁移期，破坏性变更必须公告",
            "克制扩展：token 数量要按实际需要增长，过多会导致选择困难与滥用；定期清理未使用的 token",
            "无障碍与对比度：语义 token 要内置对比度要求，避免开发者随意组合出不达标的配色"
        ],
        "hints": "「分三层 + 语义化命名 + 与代码同源」是 token 体系的标准答案"
    },
    {
        "job_category": "交互视觉设计", "question_type": "PROFESSIONAL", "skill_name": "交互优化",
        "aliases": "交互优化,可用性,体验问题,用户反馈", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "用户反馈「这个页面不好用」，你会怎么定位问题？",
        "reference_points": [
            "先问清具体场景：在什么操作路径上、想完成什么、卡在哪一步，把模糊抱怨转成可复现的问题",
            "看数据：漏斗各步流失率、点击热力/滚动深度、会话录屏，找到用户真实行为与预期路径的偏差",
            "自己走查：按新人视角完整走一遍流程，记录每一步的犹豫点与信息缺口",
            "归类原因：信息不清晰、操作步骤过多、反馈缺失（点完没反应）、性能慢、错误提示不友好",
            "小范围可用性测试：找 5 个目标用户做任务式测试，观察卡点比听评价更有效",
            "避免直接按个人审美改：先定位根因再设计方案，并定义验证指标"
        ],
        "hints": "「把模糊抱怨转成可复现的问题」是专业度的体现"
    },
    {
        "job_category": "交互视觉设计", "question_type": "PROFESSIONAL", "skill_name": "交互优化",
        "aliases": "交互优化,数据驱动,转化率,AB测试,漏斗", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何用数据驱动的方式持续优化核心流程的转化率？",
        "reference_points": [
            "建立漏斗基线：把核心流程拆成步骤，量化每一步的流失率，找到影响最大的环节优先优化",
            "定量与定性结合：数据告诉你\"在哪流失\"，访谈与录屏告诉你\"为什么流失\"，缺一不可",
            "形成假设：把洞察写成可验证的假设（如果简化这一步，预计完成率提升 X%），而非\"我觉得应该这样改\"",
            "实验验证：A/B 测试单一变量、样本量充足、覆盖完整周期，避免过早下结论",
            "关注护栏指标：转化提升但投诉、退款或后续留存恶化，就不是真正的优化",
            "多轮迭代累积：小幅改动的收益需要持续叠加，同时警惕局部最优与长期伤害",
            "沉淀为规范：验证有效的模式固化到设计系统或组件默认行为中，避免后续设计再犯",
            "长期视角：某些优化会消耗用户信任换取短期指标，需要明确底线"
        ],
        "hints": "「数据定位 + 定性解释 + 实验验证」三段式比只讲 A/B 更有深度"
    },

    # ================= === 客户成功 === =================
    {
        "job_category": "客户成功", "question_type": "PROFESSIONAL", "skill_name": "客户健康度",
        "aliases": "客户健康度,流失预警,客户活跃,风险信号", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "你会关注客户的哪些信号来判断他最近用得不好？",
        "reference_points": [
            "登录频次与活跃用户数下降：尤其是核心使用者的活跃度变化",
            "核心功能渗透率低：只用了边缘功能，说明价值未被真正兑现",
            "工单与投诉增多，或问题长期未解决导致情绪升级",
            "关键联系人变动或失联：对接人离职是常见的流失前兆",
            "合同与商务信号：续约期临近但无续约动作、付款延迟、采购流程停滞",
            "业务侧变化：客户自身业务收缩、被并购、预算削减",
            "主动性：这些信号要靠定期巡检发现，不能等客户主动来找"
        ],
        "hints": "要提「关键联系人离职」这个常被忽略但极准的先行信号"
    },
    {
        "job_category": "客户成功", "question_type": "PROFESSIONAL", "skill_name": "客户健康度",
        "aliases": "客户健康度,收入预测,续约预测,干预机制,playbook", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何把客户健康度体系与公司收入预测、资源投入真正打通？",
        "reference_points": [
            "模型要校准：用历史续约/流失结果回归验证健康度权重是否有效，而不是拍脑袋定分值",
            "分层配置资源：高价值高风险客户优先人工介入，中小客户靠自动化触达，避免资源平均分配",
            "输出经营视角：把健康度转换为可预测的收入风险清单（本季度可能流失的 ARR），供管理层决策",
            "统一口径：与销售、产品、财务共享同一套客户与收入定义，避免各部门数字打架",
            "自动触发 playbook：不同风险等级对应标准干预动作（触达、技术攻关、高层拜访），并规定时限与责任人",
            "度量干预效果：对比干预组与未干预组的续约率，验证机制是否真的有效并迭代模型",
            "避免两个极端：只算分不行动，或只看分数不看客户真实业务处境",
            "与续约流程打通：健康度信号要在续约前足够早地触发动作，而不是到期前一个月才报警"
        ],
        "hints": "「模型要用结果校准 + 输出收入风险清单」是这题的高度所在"
    },
    {
        "job_category": "客户成功", "question_type": "PROFESSIONAL", "skill_name": "客户导入",
        "aliases": "客户导入,onboarding,启动会,对接", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "客户刚签约，你第一天会做什么？",
        "reference_points": [
            "建立对接渠道：拉群或建立正式沟通机制，明确双方接口人与职责分工",
            "推进账号开通与权限配置，确保客户能尽快登录并使用",
            "对齐业务目标与成功标准：客户为什么买、希望达成什么业务结果，这决定后续所有动作",
            "约定启动会时间与议程，把 onboarding 计划与里程碑先摆出来",
            "发送简明上手材料：不要一上来就丢一堆文档，给最小必要路径",
            "明确后续沟通节奏（周会/双周会）与升级联系人的联系方式"
        ],
        "hints": "「对齐业务目标」是第一天最重要但最容易被跳过的事"
    },
    {
        "job_category": "客户成功", "question_type": "PROFESSIONAL", "skill_name": "客户导入",
        "aliases": "客户导入,分层交付,标准化,SOP,自助化,TTV", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何设计分层的客户导入方案，既保证体验又能规模化交付？",
        "reference_points": [
            "按价值与复杂度分层：大客户高接触（专属方案、现场实施、高层对接），中小客户标准化自助，避免一套流程打天下",
            "标准化资产：成功计划模板、里程碑检查清单、实施 SOP、常见问题库，把个人经验变成组织能力",
            "自助化建设：产品内置引导、视频教程、帮助中心与社区，让低接触客户能自行完成大部分步骤",
            "自动化跟踪：系统按进度与健康度自动触达，人工只在关键节点（启动会、首次价值达成、风险预警）介入",
            "定义完成标准：每一阶段有明确交付物与达标门槛（如核心功能已配置、关键用户已完成培训）",
            "度量并按层对比：激活率、首值达成时间（TTV）、阶段性流失，找出哪一层效率最低并优化",
            "应对复杂项目：多产品线、多部门、涉及数据迁移的客户需要独立项目管理与风险清单",
            "反馈闭环：把 onboarding 中反复出现的问题回流到产品与销售承诺环节，从源头减少实施难度"
        ],
        "hints": "「分层 + 标准化资产 + 自动化跟踪」是规模化交付的三件套"
    },
    {
        "job_category": "客户成功", "question_type": "PROFESSIONAL", "skill_name": "客户挽留",
        "aliases": "客户挽留,退订,流失原因,价值重现", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "客户说要退订，你会先做什么？",
        "reference_points": [
            "先探询真实原因，不急于打折也不立刻争辩：是产品能力不足、价值没被感知、预算削减还是人事变动",
            "收集事实：了解使用情况、最近发生的具体问题、不满积累的起点",
            "判断可挽回性：如果是价值未兑现且可修复，值得投入；如果是业务关闭或战略转移，强留无意义",
            "给出具体方案与时间承诺，而不是模糊表态\"我们再优化\"",
            "内部同步升级：涉及产品缺陷或重大商务条件，需要拉通产品、研发与销售一起决策",
            "保持尊重：即使最终流失，也要维护关系，客户可能因业务变化再回来或推荐他人"
        ],
        "hints": "「先探询不急于打折」是这题的关键判断"
    },
    {
        "job_category": "客户成功", "question_type": "PROFESSIONAL", "skill_name": "客户挽留",
        "aliases": "客户挽留,流失预警,挽留机制,流失归因,退出机制", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何建立体系化的流失预警与挽留机制？",
        "reference_points": [
            "流失归因分类：把历史流失按原因归类（产品能力、服务质量、价格、关键人变动、被竞品替换、客户业务变化），不同原因对应完全不同的对策",
            "预警前置：以续约或到期为锚点提前 3~6 个月识别风险信号，留足干预窗口",
            "分级与 playbook：按风险等级与客户价值制定标准干预动作——价值重现、技术攻关、高层对话、商务方案",
            "授权与决策效率：挽留常涉及让利或资源投入，需明确一线可自主决定的范围，避免层层审批错过时机",
            "跨部门协同：产品缺陷类流失必须拉通产品与研发给出修复时间表，CS 单方面承诺没有意义",
            "规范退出：挽留失败也要有序退出，做好数据导出、权限回收与知识回收，保留未来合作可能",
            "闭环改进：把流失原因回流到产品、销售承诺与交付环节，否则同类流失会持续发生",
            "度量：跟踪挽留成功率、挽回的 ARR 与投入成本，判断机制是否经济有效"
        ],
        "hints": "「归因分类 + 提前 3-6 个月预警 + 授权让一线能快速决策」是机制的三根柱子"
    },
    {
        "job_category": "客户成功", "question_type": "PROFESSIONAL", "skill_name": "续约增购",
        "aliases": "续约,增购,价值回顾,QBR,续费率", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "续约应该提前多久开始准备？需要准备什么？",
        "reference_points": [
            "提前 3~6 个月启动：给风险处置与决策链沟通留出足够时间，避免到期前临时抱佛脚",
            "准备价值证明材料：使用数据、业务成果与 ROI 回顾，用客户自己的成果说话而不是功能清单",
            "理清客户内部决策链与预算周期：谁提出、谁审批、预算什么时候到位",
            "识别风险信号：健康度、关键联系人状态、历史问题是否已解决",
            "准备续约方案：续约期限、价格策略与可能的升级选项，明确可让渡的边界",
            "避免的错误：到期才联系、只谈价格不谈价值、把续约当成行政流程"
        ],
        "hints": "「用客户自己的成果说话」比介绍功能更有说服力"
    },
    {
        "job_category": "客户成功", "question_type": "PROFESSIONAL", "skill_name": "续约增购",
        "aliases": "续约增购,land and expand,价值证明,多干系人,打包定价", "stage": "系统设计",
        "difficulty": "HARD", "time_limit_sec": 240,
        "text": "如何设计一套从价值证明到增购的系统化打法？",
        "reference_points": [
            "价值证明常态化：把 QBR（季度业务回顾）与成功报告制度化，量化业务结果（效率提升、成本下降、收入增长），而不是汇报功能使用率",
            "识别增购信号：用量接近套餐上限、新部门或新场景出现、客户主动询问进阶能力、已有成功案例可复制到其他团队",
            "价值驱动而非促销驱动：增购的前提是客户已在使用中获得价值，靠折扣催出的增量往往带来后续流失",
            "多干系人经营：识别使用者、技术把关者、经济买家与 Champion，避免只依赖单一联系人",
            "与销售的协同分工：CS 负责价值交付与需求识别，销售负责商务谈判，需要明确移交标准与激励分配避免内耗",
            "产品打包与定价策略：设计合理的阶梯与模块组合，避免不同产品线自相残杀或让客户觉得被套路",
            "风险控制：警惕过度销售超出客户实际承受能力，短期收入增长可能换来长期信任损失与流失",
            "度量：跟踪净收入留存率（NRR）、扩容转化率与增购客户的后续续约率"
        ],
        "hints": "「价值证明常态化 + 与销售明确分工」是体系化的关键，最后提 NRR"
    },

    # === 补齐 P0-3b 遗漏：4 个「原题即为 HARD」的技能需补 EASY + MEDIUM ===
    {
        "job_category": "用户运营", "question_type": "PROFESSIONAL", "skill_name": "增长实验",
        "aliases": "增长实验,实验复盘,实验设计,指标", "stage": "深度探究", "difficulty": "MEDIUM",
        "time_limit_sec": 180,
        "text": "请完整讲一次你做过的增长实验：从假设到结论是怎么走完的？",
        "reference_points": [
            "起点是假设：写清「因为观察到什么，所以改什么，预期哪个指标会变化」，而不是先想改法再倒推理由",
            "实验设计：明确核心指标与护栏指标、分流方式、所需样本量与观察周期（覆盖工作日与周末）",
            "执行与数据质量：中途监控分流是否均匀、埋点是否正常，出现异常时的处理原则（如污染要作废重跑）",
            "结果解读：区分统计显著与业务显著，效应小到没有业务意义就不值得上线",
            "负结果同样要归因：是假设错了、执行不到位还是样本不足，这决定下次怎么改",
            "可复制性判断：结论在什么人群、什么场景下成立，是否可以直接推广",
            "归档沉淀：把假设、设计与结论写入实验记录库，避免团队重复做同一个实验"
        ],
        "hints": "重点是「负结果也要归因」和「结论的适用边界」"
    },
    {
        "job_category": "销售商务", "question_type": "PROFESSIONAL", "skill_name": "大客户攻坚",
        "aliases": "大客户,客户开发,商机挖掘,拜访准备", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "初次接触一个潜在大客户，你会做哪些准备？",
        "reference_points": [
            "研究客户背景：业务模式、行业地位、近期动态（融资、扩张、组织调整）、公开财报与新闻",
            "推测痛点与切入点：结合我们的能力找出可能的契合场景，准备好对应的价值主张",
            "准备同行业案例与数据，证明我们解决过类似问题",
            "寻找接触路径：是否有引荐人、共同人脉、行业活动或公开渠道可以建立联系",
            "设定首次沟通目标：不是当场成交，而是获取信息、建立信任并推进到下一步",
            "准备提问清单：现状与挑战、决策流程与参与人、预算与时间表、过往方案的不满点"
        ],
        "hints": "首次拜访的目标是「获取信息 + 推进下一步」，不是当场成交"
    },
    {
        "job_category": "销售商务", "question_type": "PROFESSIONAL", "skill_name": "大客户攻坚",
        "aliases": "大客户,商机推进,停滞商机,Champion,决策链", "stage": "深度探究", "difficulty": "MEDIUM",
        "time_limit_sec": 180,
        "text": "一个已经建立联系的大客户商机长期停滞，你会怎么推进或止损？",
        "reference_points": [
            "先复盘停滞原因：缺 Champion、预算未到位、需求不紧急、竞品已卡位、决策链未打通",
            "重新评估商机真实性：是否有明确痛点、时间表与预算；不成立就降级或退出管道，避免虚高占用资源",
            "多线接触：建立第二、第三联系人，降低对单一对接人的依赖，同时识别真正的经济买家",
            "创造推进理由：新方案、新案例、行业活动、高层互访或阶段性试点，给对方一个重新启动的契机",
            "匹配客户节奏：对齐预算周期与年度规划节点，在客户内部立项窗口前完成铺垫",
            "设定退出标准：明确多久无实质进展就归档，把精力投到胜率更高的商机上"
        ],
        "hints": "「重新评估真实性 + 设定退出标准」体现的是资源效率意识"
    },
    {
        "job_category": "人力资源", "question_type": "PROFESSIONAL", "skill_name": "绩效体系",
        "aliases": "绩效面谈,绩效反馈,沟通,员工发展", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "绩效面谈应该怎么谈？",
        "reference_points": [
            "提前准备：把事实、数据与具体事件整理清楚，避免现场凭印象回忆",
            "先让员工自评：了解对方对自己表现的判断，找出认知差距再给反馈",
            "对事不对人：用具体行为与结果说话，避免\"你不够积极\"这类人格评价",
            "双向沟通：留出时间听取员工视角、困难与诉求，而不是单向宣贯结果",
            "明确改进方向：哪些要延续、哪些要调整，以及公司能提供什么支持",
            "形成记录与约定：写下面谈结论与下一步，约定下次检查时间",
            "避免的误区：只谈缺点打击信心、只做形式走过场、或者只在裁员前才认真谈"
        ],
        "hints": "「先让员工自评」和「对事不对人」是面谈质量的两个关键"
    },
    {
        "job_category": "人力资源", "question_type": "PROFESSIONAL", "skill_name": "绩效体系",
        "aliases": "绩效方案,绩效设计,考核指标,指标拆解", "stage": "系统设计", "difficulty": "MEDIUM",
        "time_limit_sec": 180,
        "text": "如何设计一套业务认可、员工也信服的绩效方案？",
        "reference_points": [
            "从战略逐层拆解：公司目标 → 部门目标 → 个人目标，保证每个人知道自己的工作如何支撑大局",
            "指标可控可衡量：尽量用员工能影响的过程与结果指标，避免把不可控因素计入考核",
            "结果与过程搭配：只看结果会诱导短期行为，加入必要的过程指标与质量约束",
            "权重与阈值设计：避免极端权重造成博弈（如一味压库龄、砍研发投入），设置封顶与地板",
            "谨慎使用强制分布：团队规模小或协作紧密时，强制排名会破坏合作，需评估适用性",
            "沟通与申诉机制：让员工理解规则并有权申诉，减少\"暗箱操作\"的感知",
            "周期性回看：用数据检验方案是否产生了预期行为，而不是设完就不再动",
            "防止层层加码：目标拆解过程中容易被逐级放大，最终失真到无法完成"
        ],
        "hints": "「指标可控」和「防层层加码」是最容易被忽略但最致命的两点"
    },
    {
        "job_category": "交互视觉设计", "question_type": "PROFESSIONAL", "skill_name": "设计决策",
        "aliases": "设计决策,方案讲解,设计沟通,设计依据", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "你会如何向非设计同事解释自己的设计方案？",
        "reference_points": [
            "先说目标与约束，再讲方案：让对方知道问题是什么，才容易接受解法",
            "用依据支撑而非个人审美：设计原则、用户研究结论、数据或行业惯例都可以作为论据",
            "针对听众调整表达：产品经理关心业务价值、研发关心可行性与成本、老板关心风险与收益",
            "给出备选与取舍：说明为什么没选另一个方案，比只给一个答案更容易获得信任",
            "主动说明局限：清楚方案在哪些条件下可能不成立，以及打算如何验证",
            "避免术语堆砌与\"我觉得好看\"，那会让讨论陷入审美争论"
        ],
        "hints": "「针对听众调整表达」是设计沟通的关键，别用一套语言对所有人"
    },
    {
        "job_category": "交互视觉设计", "question_type": "PROFESSIONAL", "skill_name": "设计决策",
        "aliases": "设计决策,用户研究,数据冲突,A/B测试,论证", "stage": "深度探究", "difficulty": "MEDIUM",
        "time_limit_sec": 180,
        "text": "当用户研究的结论与数据表现冲突时，你如何做设计决策？",
        "reference_points": [
            "先核对口径与样本：确认研究人群与数据统计人群是否一致，避免\"不同人群得出不同结论\"的伪冲突",
            "理解两者各回答什么问题：定性解释\"为什么\"，定量说明\"有多少、影响多大\"，通常互补而非对立",
            "检查可能的偏差：研究设计是否存在引导性提问、样本是否存在幸存者偏差，埋点是否存在缺陷或漏埋",
            "用小成本实验做裁判：把两种判断转成可验证的方案做 A/B 测试，用结果而不是争论来决策",
            "若无法实验：按风险与影响面权衡，选择可回滚、可监控的方案，并设定复盘时点",
            "记录决策依据：写清当时的判断与前提，便于事后验证是判断错了还是环境变了",
            "避免的陷阱：只挑支持自己既定方案的证据（确认偏误），或直接以\"数据不会说谎\"否定用户真实体验"
        ],
        "hints": "核心是先确认「是不是同一人群、同一口径」，再谈谁对"
    },

    # =====================================================================
    # v2 扩充批次 P0-3c：长尾 6 类补齐每技能三档难度（38 题）+ 通用池扩充（16 题）
    # =====================================================================

    # ================= === 系统运维 · 补齐 === =================
    {
        "job_category": "系统运维", "question_type": "PROFESSIONAL", "skill_name": "CI/CD",
        "aliases": "CI/CD,持续集成,持续交付,流水线,DevOps", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是 CI/CD？它到底解决了什么问题？",
        "reference_points": [
            "CI（持续集成）：频繁把代码合回主干，每次合并自动构建与跑测试，尽早暴露集成问题",
            "CD 的两种含义要区分：持续交付（随时可发布，发布动作人工触发）与持续部署（自动发布到生产）",
            "解决的痛点：\"集成地狱\"（长期分支后合并冲突）、手工发布易错、反馈周期长、环境不一致导致\"我本地是好的\"",
            "关键要素不是工具而是纪律：自动化测试门禁、制品唯一化、环境一致性、可快速回滚",
            "判断标准：反馈速度、失败能否自动阻断、发布是否可重复与可回滚——只画了流水线不等于做到了 CI/CD"
        ],
        "hints": "要区分「持续交付 vs 持续部署」，并强调回滚能力"
    },
    {
        "job_category": "系统运维", "question_type": "PROFESSIONAL", "skill_name": "CI/CD",
        "aliases": "CI/CD,流水线设计,灰度发布,制品管理,回滚", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何设计一套支持多环境、可灰度、能快速回滚的流水线体系？",
        "reference_points": [
            "制品唯一化：一次构建、多环境晋升（promote），禁止每个环境重新构建，否则无法证明测过的就是发布的",
            "流水线分层：提交级跑快速检查（lint/单测）；合并级跑全量与集成测试；发布级跑端到端、性能与安全扫描，据此控制反馈时长",
            "环境与配置分离：配置按环境注入，密钥走专用管理（不落仓库、不落制品），环境差异必须显式可见",
            "灰度策略：按用户/地域/百分比切流，配套灰度期间的指标看板与异常自动回滚阈值",
            "回滚优先于修复：保留历史制品，回滚只需切流量或换版本标签，秒级生效；数据库变更要考虑向后兼容（先加后删）",
            "审批与留痕：生产发布的关键节点留审批记录，满足审计要求但不拖慢日常发布",
            "流水线自身的可观测：失败要能快速归因（是代码、环境还是依赖问题），并统计失败率与时长趋势"
        ],
        "hints": "「一次构建多环境晋升」和「数据库变更向后兼容」是这题的关键细节"
    },
    {
        "job_category": "系统运维", "question_type": "PROFESSIONAL", "skill_name": "Docker",
        "aliases": "Docker,容器,虚拟机,namespace,cgroups,镜像分层", "stage": "专业基础", "difficulty": "MEDIUM",
        "time_limit_sec": 180,
        "text": "容器与虚拟机有什么区别？容器为什么更轻量？",
        "reference_points": [
            "虚拟机：由 Hypervisor 虚拟化硬件，每台 VM 含完整 Guest OS，隔离性强但资源开销与启动时间大",
            "容器：共享宿主机内核，靠 namespace 隔离视图（PID/NET/MNT/UTS/USER）、cgroups 限制 CPU 与内存",
            "因此容器启动秒级、体积小、密度高，适合微服务与快速扩缩容",
            "镜像分层：基于 UnionFS 的只读层叠加，容器运行时加一个可写层，因此层可复用、拉取快",
            "代价与边界：隔离性弱于虚拟机（内核共享，内核漏洞可逃逸），不适合强隔离或异构内核场景",
            "选择依据：需要强隔离或多 OS 内核用 VM；需要快速交付与高密度部署用容器，二者常组合（VM 上跑容器）"
        ],
        "hints": "要落到「namespace 隔离 + cgroups 限制」这两个内核机制，而不是只说\"更轻量\""
    },
    {
        "job_category": "系统运维", "question_type": "PROFESSIONAL", "skill_name": "Docker",
        "aliases": "Docker,容器安全,容器生产实践,资源限制,存储驱动", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "容器在生产环境有哪些常见坑与安全加固点？",
        "reference_points": [
            "不以 root 运行：指定非 root 用户、只读根文件系统、drop 掉多余 capabilities，必要时加 seccomp/AppArmor 策略",
            "镜像可信与漏洞治理：只用可信基础镜像、固定 digest 而非浮动 tag、接入镜像扫描并在流水线卡口",
            "资源限制：必须设置 CPU/内存 limit 与 request，避免单个容器拖垮宿主机；限制 pid 数防 fork 炸弹",
            "存储与日志：容器可写层不要写业务数据（易爆盘且重启丢失），日志走 stdout 由采集组件收；日志驱动与轮转要配置",
            "状态与数据卷：有状态服务要明确卷方案与备份，避免\"容器一重建数据就没了\"",
            "生命周期：配置健康检查、正确处理 SIGTERM 做优雅停止，避免发布时中断请求",
            "网络暴露最小化：只暴露必要端口，管理端口不对公网开放",
            "宿主机与运行时：及时打内核与运行时补丁，避免共享内核带来的逃逸风险"
        ],
        "hints": "「非 root + 资源限制 + 不写可写层」是三个最常被忽略的生产坑"
    },
    {
        "job_category": "系统运维", "question_type": "PROFESSIONAL", "skill_name": "Kubernetes",
        "aliases": "Kubernetes,K8s,Pod,Deployment,Service,声明式", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "K8s 里 Pod、Deployment、Service 分别解决什么问题？",
        "reference_points": [
            "Pod 是最小调度单元：一组共享网络命名空间与存储卷的容器，通常一个主容器加若干 sidecar",
            "Deployment 管理无状态工作负载：声明期望副本数，负责滚动更新、回滚与副本自愈（由 ReplicaSet 承载）",
            "Service 为一组 Pod 提供稳定访问入口：虚拟 IP + 负载均衡 + 服务发现，屏蔽 Pod 频繁重建带来的 IP 变化",
            "配套对象：ConfigMap/Secret 管配置、Ingress 管七层入口、StatefulSet 管有状态、Job/CronJob 管批处理",
            "核心范式是声明式与控制器循环：声明期望状态，控制器持续把实际状态收敛到期望状态",
            "理解这点就能类推：多数问题都是\"期望与实际不一致\"，排查从控制器的状态与事件看起"
        ],
        "hints": "最后点出「声明式 + 控制器循环」这个统一心智模型"
    },
    {
        "job_category": "系统运维", "question_type": "PROFESSIONAL", "skill_name": "Kubernetes",
        "aliases": "Kubernetes,K8s,容量规划,探针,HPA,QoS,PDB", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何为一个生产 K8s 集群做容量规划与稳定性治理？",
        "reference_points": [
            "资源与 QoS：合理设置 requests/limits 决定 QoS 等级，避免无限制的 BestEffort 在节点压力时被优先驱逐；requests 过小会导致超卖与争抢",
            "弹性能力：HPA 按指标扩副本、VPA 调资源、集群自动扩缩容加节点，三者要配合并防止互相打架",
            "高可用分布：用亲和/反亲和与拓扑分布约束把副本打散到不同节点与可用区；关键组件多副本",
            "发布安全：滚动更新的 maxSurge/maxUnavailable 与 PodDisruptionBudget 保证驱逐与发布期间可用性不塌",
            "探针设计：readiness 决定是否接流量、liveness 决定是否重启，配置不当会造成流量打到未就绪实例或频繁误杀；启动慢的服务用 startupProbe",
            "控制面与基础设施瓶颈：etcd 与 API Server 的压力、镜像拉取带宽、节点磁盘与网络，常是被忽略的容量瓶颈",
            "可观测与水位：节点资源水位、Pending Pod、OOMKilled、驱逐事件都要进监控并设告警阈值",
            "变更管理：K8s 版本与节点镜像升级要走灰度与回滚预案"
        ],
        "hints": "「探针配置不当的后果」和「QoS 决定驱逐顺序」是实战派才会讲的点"
    },

    # ================= === 运维架构 · 补齐 === =================
    {
        "job_category": "运维架构", "question_type": "PROFESSIONAL", "skill_name": "Go",
        "aliases": "Go,Golang,slice,map,并发安全", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "Go 的 slice 与 map 有哪些容易踩的使用要点？",
        "reference_points": [
            "slice 是底层数组的视图（指针 + 长度 + 容量），append 超出容量会分配新数组，此后与原切片不再共享数据",
            "共享底层数组的陷阱：切片切片后互相修改会\"意外联动\"，需要隔离时用 copy 或三索引切片限制容量",
            "map 非并发安全：并发读写会直接 panic（fatal error: concurrent map writes），需要加锁或使用 sync.Map",
            "map 的遍历顺序是随机的，不要依赖顺序；删除后再遍历也不保证顺序",
            "nil map 可以读、不能写；按容量预估初始化 make(map, n) 可减少扩容",
            "slice 的 len 与 cap 要分清：len 决定可见元素，cap 决定 append 是否触发扩容"
        ],
        "hints": "「append 后不再共享底层数组」是最高频的隐性 bug"
    },
    {
        "job_category": "运维架构", "question_type": "PROFESSIONAL", "skill_name": "Go",
        "aliases": "Go,Golang,pprof,内存泄漏,GC,goroutine泄漏", "stage": "深度探究", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何系统排查与优化 Go 服务的内存与 GC 问题？",
        "reference_points": [
            "先取证：用 net/http/pprof 采集 heap（inuse_space 与 alloc_objects），对比多个时间点看是哪类对象在持续增长",
            "区分两类问题：真泄漏（goroutine 未退出、全局缓存无上限、time.Ticker 未 Stop、channel 阻塞导致 goroutine 堆积）与高分配率（正常但放大了 GC 压力）",
            "goroutine 泄漏排查：看 goroutine profile 的堆栈聚集，常见于无缓冲 channel 发送阻塞、context 未取消",
            "降低分配：对象复用（sync.Pool）、预分配 slice 容量、避免小对象频繁转 interface、字符串拼接用 Builder",
            "GC 调优：理解 GOGC 与 GOMEMLIMIT 的作用，容器内要设置 GOMEMLIMIT 防 OOM Kill；不要盲目调 GOGC 掩盖泄漏",
            "看调度与停顿：用 trace 观察 GC 停顿与调度延迟，确认是否影响 P99 延迟",
            "验证闭环：压测复现 → 修复 → 上线观察内存曲线与 GC 频率是否平稳"
        ],
        "hints": "「先区分真泄漏与高分配」是能否快速定位的分水岭"
    },
    {
        "job_category": "运维架构", "question_type": "PROFESSIONAL", "skill_name": "Linux",
        "aliases": "Linux,系统监控,top,free,iostat", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "Linux 上如何快速查看系统的负载、CPU、内存、磁盘与网络状态？",
        "reference_points": [
            "负载：uptime/top 看 1/5/15 分钟负载，关键是结合 CPU 核数判断（负载 8 在 4 核机器上已过载）",
            "CPU：top 看 us（用户态）/sy（内核态）/wa（IO 等待）/si（软中断）分布，不同占比指向完全不同的原因",
            "内存：free -h 关注 available 而不是 free（buff/cache 可回收）；同时看 swap 使用，大量 swap 说明内存吃紧",
            "磁盘：df -h 看空间，iostat -x 看 %util、await 判断 IO 压力",
            "网络：ss -s / ss -lnt 看连接数与监听端口，iftop/nload/sar -n DEV 看流量",
            "进程：ps/top 排序定位资源占用高的进程，pidstat 按进程看 CPU/IO/内存趋势"
        ],
        "hints": "强调「负载要结合核数看」「内存看 available」，这是新手最常见的误读"
    },
    {
        "job_category": "运维架构", "question_type": "PROFESSIONAL", "skill_name": "Linux",
        "aliases": "Linux,磁盘IO,性能诊断,iotop,火焰图", "stage": "深度探究", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "一台服务器磁盘 IO 打满、负载飙高，你会如何定位根因并处置？",
        "reference_points": [
            "先确认现象与范围：iostat -x 看 %util、await、aqu-sz，判断是读还是写压力、是设备饱和还是队列堆积",
            "定位到进程：iotop 或 pidstat -d 找出 IO 大户；再追到具体文件（lsof、/proc/<pid>/io、strace 观察调用）",
            "区分应用与系统原因：应用侧常见日志狂打、同步刷盘、批量导入、缺少索引导致大范围扫表；系统侧可能是 RAID 降级、磁盘故障、内存不足触发 swap 抖动",
            "看是否伴随 CPU iowait 与内存压力：wa 高且 swap 活跃，说明瓶颈可能在内存而非磁盘本身",
            "深度定位：必要时用 perf/火焰图看线程是否长期阻塞在 IO 等待，或抓取慢请求对应的时间段",
            "处置顺序：先止损（限流、降级、暂停批任务、临时扩容/换节点），再优化（异步写、批量合并、日志级别与轮转、索引与查询优化）",
            "验证与预防：处理后复测指标，并把 IO 水位纳入监控告警，避免复发时才发现"
        ],
        "hints": "要有「先止损再优化」的顺序感，并主动提到「内存不足会表现为 IO 高」这个伪装"
    },
    {
        "job_category": "运维架构", "question_type": "PROFESSIONAL", "skill_name": "Prometheus",
        "aliases": "Prometheus,指标类型,Counter,Gauge,Histogram,监控", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "Prometheus 的指标类型有哪些？分别适合描述什么？",
        "reference_points": [
            "Counter：只增不减（请求总数、错误总数），不能直接看原值，要用 rate/increase 转成速率才有意义",
            "Gauge：可增可减的瞬时值（内存占用、并发连接数、队列长度），可直接看绝对值",
            "Histogram：按桶统计分布（延迟、请求体大小），可用 histogram_quantile 算分位数，且分位数可跨实例聚合",
            "Summary：客户端直接算好分位数，精度高但分位数无法跨实例聚合，且不可回算",
            "标签（labels）用于区分维度（接口、状态码、实例），但基数过高会拖垮存储与查询，避免把用户 ID 之类高基数放进标签",
            "选型：次数用 Counter、瞬时状态用 Gauge、延迟分布优先用 Histogram"
        ],
        "hints": "「Counter 必须用 rate 看」和「总结分位数不可聚合」是核心考点"
    },
    {
        "job_category": "运维架构", "question_type": "PROFESSIONAL", "skill_name": "Prometheus",
        "aliases": "Prometheus,PromQL,告警规则,告警风暴,分位数", "stage": "深度探究", "difficulty": "MEDIUM",
        "time_limit_sec": 180,
        "text": "如何写出一条实用且不易误报的告警规则？需要注意什么？",
        "reference_points": [
            "用速率而非原值：rate(http_requests_total[5m]) 才有业务含义，Counter 原值没有可比性",
            "用 for 持续一段时间才触发（如 for: 5m），过滤瞬时抖动造成的误报；同时设置合理的评估间隔",
            "分位数用 histogram_quantile 并确认分桶设置是否覆盖目标区间，桶不合适会导致分位数失真",
            "关注长尾：P99 比平均值更能反映用户体感，平均延迟好看不代表用户没被拖慢",
            "采集断链要单独告警：用 up == 0 或 absent() 检测目标消失，否则\"指标不报\"会被误认为\"一切正常\"",
            "告警要有可行动性：写清业务含义、阈值依据与处理指引，并配置分组（group_by）、抑制（inhibit）与静默（silence）防告警风暴",
            "控制查询开销与标签基数，避免大范围聚合导致 Prometheus 自身过载"
        ],
        "hints": "「for 抑制抖动」与「采集断链要单独告警」是两个最实用的细节"
    },

    # ================= === 质量保障 · 补齐 === =================
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "测试设计",
        "aliases": "测试设计,等价类,边界值,用例设计", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是等价类划分与边界值分析？为什么它们能减少用例数却不降低覆盖率？",
        "reference_points": [
            "等价类划分：把输入域划成有效类与无效类，认为同一类中任取一个值的处理逻辑相同，因此每类只要代表值即可",
            "边界值分析：缺陷最易出现在边界，因此取边界值本身与边界两侧（min-1、min、max、max+1）作为用例",
            "两者配合使用效果最好，常先划分等价类再对每类取边界",
            "补充方法：判定表适合多条件组合、场景法适合流程型功能、错误推测法补充经验盲点",
            "前提假设要说明：等价类方法隐含\"同类行为一致\"的假设，若实现中有特殊分支则假设不成立，需要针对分支补充用例"
        ],
        "hints": "最后点出「等价类是假设同类行为一致」，体现对方法前提的理解"
    },
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "测试设计",
        "aliases": "测试设计,测试策略,风险评估,大促测试", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何为一个大型促销活动设计覆盖完整、可在有限时间内执行的测试策略？",
        "reference_points": [
            "先做风险分析与范围裁剪：按变更影响面、业务重要度、故障代价决定测试深度，时间不够时要明确放弃什么并记录风险",
            "分层策略：单元/接口/端到端分工，越底层越自动越高频，端到端只覆盖核心链路",
            "关键场景清单：活动开始与结束的时间边界、库存与限购的并发一致性、支付与退款链路、优惠叠加与资损风险、异常与降级（第三方不可用、超时）",
            "容量与性能：按预估峰值设计压测，验证限流与降级策略真的生效",
            "数据准备与隔离：活动数据、账户与库存的构造方式，避免污染生产；压测数据要能回滚",
            "上线与回滚验证：上线检查清单、灰度观察指标、回滚方案要演练过",
            "线上验证：活动开始后的人工巡查与监控看板，出问题时的预案与决策人",
            "资损是最高优先级：涉及金额的路径必须做对账与幂等验证"
        ],
        "hints": "「明确放弃什么并记录风险」比声称全覆盖更专业，最后务必提资损与对账"
    },
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "Pytest",
        "aliases": "Pytest,fixture,单元测试,自动化测试", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "pytest 里的 fixture 是做什么的？它带来哪些好处？",
        "reference_points": [
            "作用：集中准备与清理测试所需的依赖（数据、连接、临时文件、服务），通过参数注入到用例，替代 setUp/tearDown",
            "scope 控制（function/class/module/package/session）：session 级可复用昂贵资源，function 级保证隔离，需按代价与污染风险权衡",
            "conftest.py 支持跨文件共享 fixture，形成分层的作用域",
            "yield 形式实现 teardown：yield 之前是准备，之后是清理，即使用例失败也会执行",
            "可参数化：一个 fixture 提供多组数据，配合 @pytest.mark.parametrize 大幅减少重复代码",
            "可覆盖：测试文件内定义同名 fixture 即可覆盖上层实现，便于针对特殊场景定制"
        ],
        "hints": "「scope 决定隔离与性能的权衡」是理解 fixture 的关键"
    },
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "Pytest",
        "aliases": "Pytest,自动化框架,并行测试,xdist,flake", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何设计一套可并行、稳定复跑、失败可定位的自动化测试框架？",
        "reference_points": [
            "并行前提：用例之间无共享可变状态与顺序依赖，否则并行会随机失败；用 xdist 前先做隔离审计",
            "数据隔离：每个用例独立造数与清理，或事务回滚；共享数据只读且版本固定",
            "确定性：固定随机种子、mock 外部服务与时间、容器化依赖版本，消除\"在我机器上是好的\"",
            "重试要谨慎：可以作为稳定性兜底，但必须重试前清理状态，且要统计重试率——持续靠重试通过的用例应视为缺陷而非安慰",
            "失败可定位：保留日志、请求与响应、截图/工件并上传，失败信息要能直接指向原因而不是\"断言失败\"",
            "分层与执行策略：按 smoke/regression 打标记，CI 上只跑与本次变更相关的子集，全量在夜间跑",
            "度量与治理：跟踪用例总数、执行时长、flake 率与失效用例，定期清理僵尸用例，否则维护成本会失控"
        ],
        "hints": "「重试率要度量而不是靠重试掩盖」是这题最能体现成熟度的一句"
    },
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "Selenium",
        "aliases": "Selenium,UI自动化,端到端测试,回归", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "UI 自动化测试适合做什么、不适合做什么？",
        "reference_points": [
            "适合：核心主干流程的回归验证（如登录→下单→支付）、跨系统端到端链路、发布前的 smoke 检查",
            "不适合：大量细节校验、频繁变更的页面、视觉细节与文案断言——这类更适合接口层或人工验收",
            "成本对比：UI 测试执行慢、定位脆弱、维护成本显著高于接口测试，因此应优先把校验下沉到接口层",
            "价值定位：覆盖率不是目标，用最少用例拦住最高价值的回归风险才是目标",
            "补充：像素级视觉一致性可交给专门的视觉回归工具，不要用 Selenium 硬做"
        ],
        "hints": "「优先把校验下沉到接口层」是这题的核心判断"
    },
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "Selenium",
        "aliases": "Selenium,UI自动化,flake,显式等待,PageObject", "stage": "深度探究", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何降低 UI 自动化的不稳定率与长期维护成本？",
        "reference_points": [
            "定位器策略：优先语义化属性与专用测试属性（data-testid），避免绝对路径 XPath 与依赖文案；定位器集中在页面对象中管理",
            "等待策略：用显式等待等待具体条件，禁用固定 sleep；封装常用等待（元素可见、可点击、网络空闲）",
            "结构设计：页面对象模式分离定位与业务逻辑，用例只表达业务意图，页面改动只改一处",
            "用例独立性：不依赖执行顺序与残留状态，前置数据自行准备并可清理",
            "异步与动画：处理骨架屏、懒加载、动效未结束导致的可点击性判断失误",
            "失败诊断：自动截图、保留 DOM 快照、记录浏览器日志与网络请求，便于快速判断是环境抖动还是真实缺陷",
            "治理机制：统计 flake 率并设阈值，长期不稳定且价值低的用例果断删除，避免用例集越堆越慢越假"
        ],
        "hints": "「flake 率要量化治理，该删就删」比泛泛谈稳定性更有说服力"
    },
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "性能测试",
        "aliases": "性能测试,QPS,响应时间,并发数,压测", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "QPS、响应时间与并发数分别是什么？它们之间有什么关系？",
        "reference_points": [
            "QPS：系统每秒成功处理的请求数，反映吞吐能力",
            "响应时间：单个请求从发出到返回的耗时，关注 P95/P99 而非平均值——平均值会掩盖长尾体验问题",
            "并发数：同一时刻系统正在处理的请求数量（更准确说是\"在途请求数\"）",
            "三者近似关系：并发数 ≈ QPS × 平均响应时间（Little's Law），可用于估算压测的目标并发",
            "压测要同时看吞吐、延迟与错误率，以及资源水位（CPU、内存、连接池），否则\"QPS 上去了\"可能是靠超时与错误换来的",
            "区分负载与容量：容量是满足延迟目标前提下能承受的最大负载，不是系统崩溃前的极限"
        ],
        "hints": "「平均值掩盖长尾」和 Little's Law 是这题的两个加分点"
    },
    {
        "job_category": "质量保障", "question_type": "PROFESSIONAL", "skill_name": "性能测试",
        "aliases": "性能测试,压测方案,容量评估,瓶颈定位", "stage": "系统设计", "difficulty": "MEDIUM",
        "time_limit_sec": 180,
        "text": "如何设计和执行一次有效的性能测试？",
        "reference_points": [
            "先明确目标：是容量评估、瓶颈定位还是验证扩容效果？目标不同，场景与结论完全不同；并定好可量化的通过标准",
            "场景设计贴近真实：业务配比、思考时间、参数与数据分布要模拟真实用户，避免单一接口空跑得出虚高结论",
            "分阶段加压：基准测试（单接口打底）→ 阶梯加压找拐点 → 稳定性长跑（验证内存泄漏与资源耗尽）",
            "数据与初始状态接近生产：数据量级、索引与缓存状态都会显著影响结果",
            "全链路监控：应用、中间件、数据库、主机、网络都要采集，否则定位不到瓶颈在哪一层",
            "瓶颈定位与调优后必须回归验证，确认优化真的生效且没有把瓶颈转移到别处",
            "产出可行动的结论：容量上限、扩容建议、已知短板与风险，而不是一份曲线图"
        ],
        "hints": "「先问目标」和「数据量级要接近生产」是压测最容易做假的两处"
    },

    # ================= === 客户端 · 补齐 === =================
    {
        "job_category": "客户端", "question_type": "PROFESSIONAL", "skill_name": "Android",
        "aliases": "Android,Activity,生命周期,配置变更", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "Android 中 Activity 的生命周期是怎样的？旋转屏幕时发生了什么？",
        "reference_points": [
            "完整流程：onCreate → onStart → onResume → onPause → onStop → onDestroy；onRestart 用于从停止恢复",
            "onResume 为可见且可交互；onPause 后不完全可见，因此不要在其中做耗时操作，否则阻塞切换",
            "前后台切换：进入后台走 onPause → onStop；返回时 onRestart → onStart → onResume",
            "配置变更（如旋转）默认会销毁并重建 Activity，走 onPause → onStop → onDestroy → onCreate → ...",
            "保存状态：用 onSaveInstanceState 保存瞬时 UI 状态，用 ViewModel 保存跨重建的数据（更可靠）",
            "也可以声明 configChanges 自行处理，但需自行适配布局，滥用会导致资源切换异常"
        ],
        "hints": "「onPause 不能做耗时」和「ViewModel 比 onSaveInstanceState 更适合存数据」是实用点"
    },
    {
        "job_category": "客户端", "question_type": "PROFESSIONAL", "skill_name": "Android",
        "aliases": "Android,性能优化,启动优化,ANR,包体积,稳定性", "stage": "系统设计", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何系统性地做 Android 应用的性能优化与稳定性治理？",
        "reference_points": [
            "启动优化：区分冷/温/热启动，用启动 trace 找出耗时任务，把非必要初始化延后或异步化，首屏优先渲染",
            "流畅度：主线程耗时（IO、JSON 解析、重计算）下沉；布局层级与过度绘制治理；关注掉帧率与卡顿分布而非平均 FPS",
            "内存：定位泄漏（Activity/Context 被静态或长生命周期对象持有、未注销的监听、Handler 延迟消息）、图片按需采样与缓存、Bitmap 复用",
            "稳定性：崩溃与 ANR 监控上报、按堆栈聚合与版本对比、重点关注新版本引入的崩溃；ANR 要结合主线程堆栈判断是 IO 阻塞还是锁竞争",
            "包体积：资源与代码裁剪、无用依赖清理、图片与 so 库优化、按需动态下发",
            "网络与耗电：合并请求、弱网重试与缓存、后台任务收敛，避免频繁唤醒",
            "度量与门禁：建立性能基线与指标（启动耗时、掉帧率、崩溃率、包体积），纳入发布前检查，做灰度发布与快速回滚"
        ],
        "hints": "要有「基线 + 门禁 + 灰度」的治理闭环，而不是只列优化手段"
    },
    {
        "job_category": "客户端", "question_type": "PROFESSIONAL", "skill_name": "Flutter",
        "aliases": "Flutter,StatefulWidget,StatelessWidget,setState,状态管理", "stage": "专业基础",
        "difficulty": "EASY", "time_limit_sec": 150,
        "text": "Flutter 中 StatelessWidget 与 StatefulWidget 有什么区别？setState 做了什么？",
        "reference_points": [
            "StatelessWidget 无内部可变状态，界面完全由构造参数决定，父级重建时跟着重建",
            "StatefulWidget 通过关联的 State 对象保存可变状态；State 有独立生命周期（initState/didChangeDependencies/dispose）",
            "setState 把回调里的修改应用到 State 并标记该 Element 为脏，随后在下一帧重建该子树",
            "性能提醒：setState 会重建该 widget 的整棵子树，过大范围重建会造成卡顿，应把状态下沉到最小粒度或使用局部刷新机制",
            "跨组件共享状态时不要层层传参，使用 Provider/Riverpod 等方案，并注意 dispose 释放资源",
            "原则：能用 Stateless 就用 Stateless，可变状态尽量下沉到叶子节点"
        ],
        "hints": "「setState 重建整棵子树，所以要下沉状态」是进阶理解"
    },
    {
        "job_category": "客户端", "question_type": "PROFESSIONAL", "skill_name": "Flutter",
        "aliases": "Flutter,卡顿,掉帧,DevTools,内存泄漏,重建", "stage": "深度探究", "difficulty": "HARD",
        "time_limit_sec": 240,
        "text": "如何定位并优化 Flutter 应用的卡顿与内存问题？",
        "reference_points": [
            "先定位在哪条线程：DevTools Performance 看 UI 线程（构建与布局）与 Raster 线程（绘制）的帧耗时，区分是\"算得慢\"还是\"画得慢\"",
            "减少重建：用 const 构造、把不随状态变化的子树提取为独立 widget、按需监听而非整页 setState；长列表用 builder 懒加载并设置 itemExtent",
            "布局与绘制：避免深层嵌套与重复布局，减少 clip/opacity/shadow 等高开销效果，大图按显示尺寸解码（cacheWidth/cacheHeight）",
            "重计算下沉：图像处理、加解密等放到 Isolate，避免阻塞 UI 线程",
            "内存排查：DevTools Memory 看堆增长与 GC，抓 heap snapshot 找未释放对象；常见泄漏是未取消的 Stream 订阅、未 dispose 的 Controller/Animation、闭包长期持有上下文",
            "长稳验证：用 DevTools Memory 的分配追踪观察长时间使用后是否持续增长，模拟真实场景而非只跑几秒",
            "结果验证：优化前后对比帧时间与内存曲线，并在真机多机型上验证（模拟器性能不代表真机）"
        ],
        "hints": "「先分清 UI 线程还是 Raster 线程」是 Flutter 卡顿定位的关键分叉"
    },
    {
        "job_category": "客户端", "question_type": "PROFESSIONAL", "skill_name": "Kotlin",
        "aliases": "Kotlin,val,var,data class,不可变", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "Kotlin 中 val 与 var、data class 分别有什么作用和注意事项？",
        "reference_points": [
            "val 是只读引用，不等于对象不可变：它指向的对象内部属性仍可能被修改",
            "var 可重新赋值；编码规范上优先用 val，减少意外状态变更",
            "data class 自动生成 equals/hashCode/toString/copy 与 componentN，适合做数据载体（DTO、UI 状态、事件）",
            "陷阱一：data class 的属性若包含可变字段并被当作 HashMap/Set 的键，修改字段会导致哈希变化而查不到",
            "陷阱二：data class 的 copy 是浅拷贝，嵌套可变对象仍共享引用",
            "对比：普通 class 不生成这些方法；需要深度值语义或大量字段时可考虑用普通类或专门库（如不可变集合）"
        ],
        "hints": "「val 不等于对象不可变」+「data class 作 map key 的哈希陷阱」是加分点"
    },
    {
        "job_category": "客户端", "question_type": "PROFESSIONAL", "skill_name": "Kotlin",
        "aliases": "Kotlin,协程,异常处理,取消,结构化并发,supervisorScope", "stage": "深度探究",
        "difficulty": "HARD", "time_limit_sec": 240,
        "text": "Kotlin 协程如何做异常处理与取消？有哪些容易踩的坑？",
        "reference_points": [
            "结构化并发：子协程的异常默认沿 Job 层级向上传播到父协程，父协程失败会取消所有子协程——这既是保护也是坑（一个失败全盘取消）",
            "launch 的异常直接抛出，CoroutineExceptionHandler 只对根协程生效；async 的异常不会立即抛出，而是在 await 时抛出",
            "需要兄弟协程互不影响时用 supervisorScope 或 SupervisorJob 隔离失败",
            "取消是协作式的：协程不会被打断，必须在挂起点或在计算循环中检查 isActive 才能及时响应",
            "清理逻辑放 finally，但 finally 中不能再调用挂起函数（协程已取消会直接抛）；确需挂起操作时用 withContext(NonCancellable)",
            "超时控制用 withTimeout/withTimeoutOrNull，避免请求悬挂",
            "常见坑：用 GlobalScope 启动导致无法取消与泄漏；吞掉 CancellationException 破坏取消传播；在 catch 里捕获了所有异常却不上报"
        ],
        "hints": "「取消是协作式的，finally 里不能再挂起」是实战中真正会踩的坑"
    },

    # ================= === 系统底层 · 补齐 === =================
    {
        "job_category": "系统底层", "question_type": "PROFESSIONAL", "skill_name": "C++",
        "aliases": "C++,指针,引用,const,生命周期", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "C++ 中指针与引用有什么区别？什么时候该用哪个？",
        "reference_points": [
            "引用必须初始化且不能再绑定到其他对象；指针可为空、可重新指向、可做算术运算",
            "引用没有独立地址语义（不占用可见的存储值语义），使用上更安全，函数参数与返回值优先用引用",
            "需要表达\"可能为空\"或\"需要遍历/偏移\"时用指针，例如容器遍历、可选的出参",
            "const 引用（const T&）避免拷贝同时禁止修改，是传递大对象的标准做法；返回局部变量引用是典型错误",
            "生命周期是核心风险：无论引用还是指针，指向已销毁对象都会产生未定义行为，悬垂比空指针更难发现",
            "现代 C++ 倾向用智能指针表达所有权与可空语义，裸指针只用于非拥有型观察"
        ],
        "hints": "要点出「生命周期/悬垂才是真正的风险」而不是只比语法差异"
    },
    {
        "job_category": "系统底层", "question_type": "PROFESSIONAL", "skill_name": "C++",
        "aliases": "C++,内存泄漏,ASan,Valgrind,RAII,未定义行为", "stage": "深度探究",
        "difficulty": "HARD", "time_limit_sec": 240,
        "text": "如何排查与治理 C++ 程序的内存泄漏与未定义行为？",
        "reference_points": [
            "工具按问题类型选：Valgrind 查泄漏与非法访问（慢）；AddressSanitizer 查越界与释放后使用；UndefinedBehaviorSanitizer 查未定义行为；ThreadSanitizer 查数据竞争",
            "泄漏定位：看分配栈追踪，结合多次采样做增量对比，确认是哪类对象在持续增长",
            "治理靠所有权设计而非事后补 delete：优先 RAII 与智能指针；unique_ptr 表达独占，shared_ptr 共享但要用 weak_ptr 打破循环引用",
            "常见未定义行为来源：数组越界、释放后使用、悬垂引用、未初始化变量、有符号整数溢出、对象的生命周期与虚函数调用时机错误",
            "并发问题单独看：数据竞争用 TSan，或从设计上减少共享可变状态",
            "工程手段：静态分析（clang-tidy/编译器警告全开）、代码评审关注所有权、长稳与压力测试暴露低频问题",
            "修复后必须用同一工具复测，确认问题真正消失而不是被掩盖"
        ],
        "hints": "「用所有权设计根治，而不是补 delete」是这题最关键的立场"
    },
    {
        "job_category": "系统底层", "question_type": "PROFESSIONAL", "skill_name": "Raft",
        "aliases": "Raft,共识算法,选举,任期,心跳", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "Raft 中有哪些角色？Leader 选举大致是怎么进行的？",
        "reference_points": [
            "三种角色：Follower、Candidate、Leader；正常状态下只有一个 Leader，其余为 Follower",
            "触发条件：Follower 在选举超时内没收到 Leader 心跳，就自增任期转为 Candidate 并发起投票",
            "投票规则：每个节点在同一任期内只投一票，得多数票者成为 Leader 并立即发送心跳维持权威",
            "日志约束：候选人的日志必须不落后于投票者，投票者才投票，这保证了新 Leader 一定包含所有已提交日志",
            "随机化选举超时（通常在 150~300ms 区间随机）避免所有节点同时竞选造成选票分裂",
            "任期（term）是逻辑时钟，用于识别过期信息；收到更大任期的消息要退位为 Follower"
        ],
        "hints": "「随机化超时避免选票分裂」和「日志不落后才给票」是两个关键机制"
    },
    {
        "job_category": "系统底层", "question_type": "PROFESSIONAL", "skill_name": "Raft",
        "aliases": "Raft,网络分区,日志复制,多数派,脑裂", "stage": "深度探究",
        "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "Raft 如何处理网络分区？为什么不会脑裂？日志复制如何保证一致性？",
        "reference_points": [
            "多数派原则是防脑裂的根本：只有获得多数票才能当 Leader，少数分区里的旧 Leader 无法提交任何日志",
            "日志复制流程：客户端请求写入 Leader → Leader 追加到本地日志 → 并行发给所有 Follower → 多数确认后提交并应用到状态机 → 通知客户端",
            "提交索引只能推进到多数派已复制的最大位置；未提交的日志在领导权变更后可能被覆盖",
            "旧任期日志的处理：新 Leader 只能通过提交自己任期内的日志来\"间接提交\"前任日志（因此上任后常先提交一条空日志）",
            "安全性约束：Leader 只向日志不比自己新的节点复制，且不回滚自己的日志，而是强制覆盖 Follower 的冲突部分",
            "分区恢复后，少数派节点在收到更高任期的消息后回退未提交日志并接受新 Leader 的日志，最终收敛一致",
            "读一致性：默认读可能读到旧数据，需要 ReadIndex 或租约读（lease read）来保证线性一致读"
        ],
        "hints": "「为何要提交一条空日志」和「读也要专门处理」是区分理解深度的两个点"
    },

    # ================= === 信息安全 · 补齐 === =================
    {
        "job_category": "信息安全", "question_type": "PROFESSIONAL", "skill_name": "Web安全",
        "aliases": "Web安全,注入,SQL注入,参数化查询", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是注入攻击？为什么参数化查询能有效防护？",
        "reference_points": [
            "本质：把用户可控输入当作代码或指令的一部分执行，从而改变程序原本的意图（SQL、系统命令、LDAP、模板等）",
            "SQL 注入的成因是字符串拼接：输入 ' OR 1=1 -- 会改变语句结构",
            "参数化查询（预编译）把 SQL 结构与数据分离，语句结构在传参前已确定，数据只能作为值参与，无法改变结构",
            "对比转义：手写转义容易漏掉边界情况（不同字符集、二次解码），因此不可靠；白名单校验适用于有限取值场景",
            "命令注入需要另外的思路：避免拼接 shell 字符串，改用参数数组调用，并做参数白名单",
            "纵深防御：数据库账号最小权限，即使被注入也限制其破坏范围；同时做好错误信息不外泄"
        ],
        "hints": "要讲清「结构先定、数据后传」的本质，而不是只说\"参数化安全\""
    },
    {
        "job_category": "信息安全", "question_type": "PROFESSIONAL", "skill_name": "Web安全",
        "aliases": "Web安全,SDL,安全体系,SAST,DAST,供应链安全", "stage": "系统设计",
        "difficulty": "HARD", "time_limit_sec": 240,
        "text": "如何设计一套覆盖研发生命周期的应用安全防护体系？",
        "reference_points": [
            "需求与设计阶段：安全需求梳理与威胁建模，明确数据分类与合规要求，避免安全只在测试阶段介入",
            "编码阶段：安全编码规范（参数化查询、输出编码、避免反序列化不可信数据）、密钥不入库不入仓、依赖与镜像来源可信",
            "依赖与供应链：第三方组件漏洞扫描、及时升级、固定版本与校验来源，防止被投毒",
            "测试阶段：SAST 查代码、DAST 查运行时、IAST 辅助定位，配合渗透测试；业务逻辑漏洞（越权、支付篡改、并发薅羊毛）要专门设计用例",
            "上线阶段：WAF 与限流、最小权限与网络隔离、密钥管理与定期轮换、日志脱敏",
            "运行阶段：漏洞响应流程与时限、应急响应与取证、修复后复测、定期红蓝对抗",
            "组织与流程：把安全卡点嵌入研发节奏（评审、CI 门禁、发布检查），并配套培训与责任到人，否则体系会退化为一次性检查",
            "度量：漏洞发现与修复时长、逃逸到生产的漏洞数、覆盖的资产比例"
        ],
        "hints": "要体现「安全左移 + 供应链 + 业务逻辑漏洞」三点，避免只谈工具"
    },
    {
        "job_category": "信息安全", "question_type": "PROFESSIONAL", "skill_name": "数据合规",
        "aliases": "数据合规,个人信息,最小必要,告知同意", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是个人信息？处理个人信息要遵循哪些基本原则？",
        "reference_points": [
            "个人信息的界定：以电子或其他方式记录的、能够单独或与其他信息结合识别特定自然人的各种信息",
            "基本原则：合法正当必要、目的明确与限定、最小必要（只收集与目的直接相关的最少信息）、公开透明、告知同意、保障安全、责任可追溯",
            "敏感个人信息（生物识别、医疗健康、金融账户、行踪轨迹、不满十四周岁未成年人信息）需单独同意，并说明必要性与影响",
            "处理者与受托处理者的责任划分：委托处理需签订协议并监督，责任仍在委托方",
            "个人享有的权利：知情、决定、查阅复制、更正补充、删除、可携带、解释说明，产品上要有可操作的入口",
            "常见误区：\"用户点了同意协议\"不等于已满足所有合规要求，仍需满足最小必要与目的限定"
        ],
        "hints": "要提「最小必要」与「敏感信息单独同意」，别只讲告知同意"
    },
    {
        "job_category": "信息安全", "question_type": "PROFESSIONAL", "skill_name": "数据合规",
        "aliases": "数据合规,数据出境,分类分级,数据地图,留存期限", "stage": "系统设计",
        "difficulty": "HARD", "time_limit_sec": 240,
        "text": "如何为跨区域业务设计数据合规架构？",
        "reference_points": [
            "先做数据资产盘点与分类分级：识别个人信息、敏感个人信息、重要数据与商业机密，分级决定保护强度",
            "画数据地图与流向：从采集、存储、使用、共享到销毁的完整链路，明确每个环节的责任方与存储位置",
            "跨境传输的合法路径：按适用法规选择安全评估、标准合同、认证等机制，并评估数据出境的必要性与替代方案（如本地化处理）",
            "技术落地：属地化存储与分区部署、访问最小权限与审批留痕、脱敏与假名化、（敏感字段）加密与密钥分域管理",
            "留存与删除：定义各类数据的最短必要留存期，建立到期删除与用户行使删除权的流程（含备份中的副本处理）",
            "第三方与合作方管理：数据处理协议、安全能力评估、审计权与退出时的数据处置",
            "安全事件响应：泄露发现后的通知义务与时限、对内对外的沟通口径、取证与整改闭环",
            "持续合规：法规跟踪、定期审计与演练、员工培训与考核，避免架构建好之后无人维护"
        ],
        "hints": "「数据地图」和「跨境合法路径」是这题的两个硬核考点"
    },
    {
        "job_category": "信息安全", "question_type": "PROFESSIONAL", "skill_name": "权限治理",
        "aliases": "权限治理,越权,水平越权,垂直越权,鉴权", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "什么是水平越权与垂直越权？它们的共同根因是什么？",
        "reference_points": [
            "水平越权：同权限级别的用户访问了本不属于自己的数据，例如把订单 ID 改成别人的就能查看或删除",
            "垂直越权：低权限用户获得了高权限能力，例如普通用户直接调用管理端接口",
            "共同根因：服务端过度信任客户端——只校验了\"是否登录\"，没有校验\"这个资源是否属于你\"或\"你的角色是否有权限执行\"",
            "常见表现：越权靠前端隐藏按钮、靠不可枚举的 ID 来\"保护\"，接口层毫无校验",
            "正确做法：所有鉴权必须在服务端统一入口完成，资源操作要校验归属关系",
            "补充：还有\"未授权访问\"（完全无鉴权）与\"越权修改\"（读被拦了但写没拦），测试时读写要分别验证"
        ],
        "hints": "点出「只校验登录不校验归属/角色」是共同根因，比背定义更有价值"
    },
    {
        "job_category": "信息安全", "question_type": "PROFESSIONAL", "skill_name": "权限治理",
        "aliases": "权限治理,RBAC,ABAC,数据权限,鉴权设计", "stage": "系统设计",
        "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "如何设计一个可维护、可扩展的权限模型？",
        "reference_points": [
            "模型选型：常规场景用 RBAC（用户-角色-权限）；需要按属性动态判断时用 ABAC，关系复杂（如共享文档）时用 ReBAC",
            "权限点粒度分层：菜单/页面级、操作级（按钮与接口）、数据级（行与列），三者要成套设计而非只做菜单",
            "鉴权入口统一：在中间件或拦截器集中校验，避免权限判断散落在业务代码里导致遗漏",
            "数据权限要下沉：行级过滤在查询层统一注入（数据权限上下文），而不是每个接口手写 where 条件",
            "角色的配置化：角色与权限关系可配置并留变更审计，新增角色不改代码",
            "缓存与失效：权限校验高频，需缓存并保证角色变更后及时失效，避免\"已回收权限仍然生效\"",
            "测试与治理：越权用例必须进自动化回归；定期做权限膨胀审计（谁有不该有的权限）",
            "避免：把角色硬编码在代码判断里、只做前端隐藏、超级管理员可绕过所有审计"
        ],
        "hints": "「鉴权入口统一 + 数据权限下沉到查询层」是设计可维护性的关键"
    },

    # ================= === 通用池扩充（GENERAL +8 / STRESS +8）=== =================
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "EASY", "time_limit_sec": 150,
        "text": "你平时如何保证交付质量？有没有自己的检查清单或工作习惯？",
        "reference_points": [
            "有具体机制而非\"我很细心\"：自测清单、单元测试、双人复核、上线前检查表",
            "把易错点固化成清单：历史踩过的坑都进清单，避免重复犯错",
            "交付前主动验证而非等别人发现：关键路径自己走一遍，边界条件单独验证",
            "对不确定性主动求证：需求不清先对齐，不靠猜测往下做",
            "事后复盘：出错后更新清单与流程，而不是只道歉",
            "能说出一次\"因为检查清单避免的事故\"最有说服力"
        ],
        "hints": "关键是把\"细心\"这种形容词换成可复述的具体机制"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "EASY", "time_limit_sec": 150,
        "text": "当你需要向不熟悉业务的同事解释一件复杂的事，你会怎么做？",
        "reference_points": [
            "先判断对方的知识背景，选择共同的认知锚点（类比、熟悉的业务场景）",
            "结论先行：先说清楚\"是什么、为什么重要、需要你做什么\"，细节按需展开",
            "少用术语或术语即时解释；用图、示例或具体数字代替抽象描述",
            "控制信息量：一次只讲一层，确认对方跟上再往下，避免信息倾泻",
            "给出可带走的材料（文档或要点），方便对方后续查阅与转述",
            "主动确认理解：让对方复述或提出问题，而不是问\"听懂了吗\""
        ],
        "hints": "「结论先行 + 确认理解」是沟通能力的直接体现"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "你如何看待加班与工作强度？有没有经历过难以承受的阶段，你是怎么处理的？",
        "reference_points": [
            "态度要真实不极端：既不宣扬无意义加班，也不回避阶段性高强度是常态",
            "区分类型：偶发冲刺（上线、故障、大促）可以接受；长期常态化加班说明排期或资源有问题，应该被提出来",
            "描述具体经历时要讲方法：如何排优先级、如何与主管沟通资源、如何避免自己成为瓶颈",
            "有自我保护的意识：睡眠、身体与情绪是长期产出的前提，透支不可持续",
            "展示解决问题的主动性：不只抱怨，而是提出可执行的改善（拆需求、加人手、延排期、砍范围）",
            "诚实底线：不要为了迎合而声称\"我随时可以通宵\""
        ],
        "hints": "要区分「阶段性冲刺」与「常态加班」，并给出可执行的改善动作"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "如果团队里有人长期交付不达标但态度很好，你会怎么处理？",
        "reference_points": [
            "先弄清原因：能力不足、方向不清、资源不足还是任务分配不合理，四种原因对策完全不同",
            "直接反馈：一对一沟通，用具体事实说明差距，避免模糊的\"再努力一点\"",
            "提供支持：明确期望与衡量标准、安排导师或结对、拆分更小的任务帮助建立信心",
            "设定改进期限与检查点：给机会但要有可验证的时间与标准，避免无限期容忍",
            "考虑调整岗位：有时是\"人不合适\"而非\"人不行\"，换到匹配的位置对双方都好",
            "团队视角：长期容忍会打击其他成员积极性，公平性也是管理责任",
            "态度要好但判断要清晰：温和沟通不等于不做决策"
        ],
        "hints": "要点出「长期容忍会伤害团队公平性」，这是从管理者视角的思考"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "你做过的最不被理解的一个决定是什么？后来证明对了吗？",
        "reference_points": [
            "选真实且具体的例子：当时的分歧点是什么、反对意见是什么、你依据什么坚持",
            "说明决策依据：是数据、用户反馈、技术判断还是风险预判，而不是固执",
            "讲清如何推进：不是硬扛，而是降低试错成本、设验证节点、允许他人保留意见",
            "诚实说明结果：要么被证明正确，要么承认判断有偏差并说明修正过程——后者往往更可信",
            "反思：从这件事学到什么关于沟通或决策的东西",
            "避免两种极端：不能说\"我从来没被质疑过\"，也不能把明显错误包装成坚持"
        ],
        "hints": "敢于承认判断有偏差反而更可信，别把答案准备成\"我都是对的\""
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "项目深挖", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "介绍一个你从 0 到 1 主导的项目，你怎么验证它真的解决了问题？",
        "reference_points": [
            "背景与目标：为什么做、要解决谁的什么问题、成功标准是什么（最好可量化）",
            "你是主导者：说清你的决策范围与关键判断，而不只是执行了分配的任务",
            "怎么做的：方案与关键取舍、为什么选这条路、放弃了什么",
            "验证方式：上线前后的指标对比、用户反馈、灰度或 A/B 验证、埋点数据",
            "结果要量化：效率提升、成本下降、错误率降低等，并说明数据来源与口径",
            "诚实处理不达预期的部分：哪些目标没达成、原因是什么、后来怎么调整",
            "沉淀：这次留下的可复用经验或资产"
        ],
        "hints": "「怎么验证」比「做了什么」更关键，必须有可量化的对照"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "HARD", "time_limit_sec": 240,
        "text": "你如何判断一件事该做到 80 分还是 100 分？请举一个你权衡取舍的例子。",
        "reference_points": [
            "判断依据是「边际收益与机会成本」：做到 100 分的额外投入换来的收益是否值得，以及这些时间本可以用在什么更重要的事上",
            "考虑可逆性：可逆的、影响面小的事先做到 80 分快速验证；不可逆或影响资金安全、数据正确性、对外承诺的事必须做到接近 100 分",
            "考虑受众与代价：面向外部客户的交付、涉及合规与资损的部分不能打折",
            "要能说清\'80 分\'边界：明确哪些必须保证、哪些可以后续迭代，而不是笼统地说\"先上线再说\"",
            "例子要具体：说明当时的时间约束、你砍掉了什么、保留了什么、事后结果与反思",
            "反面也要提：过度追求 100 分导致错过窗口，或长期停留在 80 分积累技术债，都是失衡",
            "补充机制：把\"暂时不做\"的部分显式记录为待办与技术债，避免被遗忘"
        ],
        "hints": "「可逆性」与「影响是否涉及资损/合规」是判断的两把尺子"
    },
    {
        "job_category": "通用", "question_type": "GENERAL", "skill_name": "综合素养",
        "stage": "综合素养", "difficulty": "MEDIUM", "time_limit_sec": 180,
        "text": "你如何给自己设定目标并跟踪进展？最近一个目标完成得怎么样？",
        "reference_points": [
            "目标要具体可衡量、有时间边界，并区分结果目标与可控的过程目标",
            "拆解到可执行动作：把大目标拆成每周/每天能完成的最小行动，避免只有愿望没有路径",
            "跟踪机制：固定节奏回顾（周复盘/月度总结）、记录数据而不是凭感觉、必要时调整策略而非直接放弃",
            "应对偏差：遇到进度落后时的处理方式——是加投入、缩范围还是延时间，要主动决策",
            "最近一个例子要真实：说清目标、进展、是否达成、以及没达成时的调整，不要含糊带过",
            "自我驱动证据：这个目标是你自己设的还是被要求的，能体现主动性"
        ],
        "hints": "「区分结果目标与过程目标」是目标管理的核心，能体现方法而不是口号"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "你提的方案已经上线一周，现在有同事当着全组说这个方案是他最早提出的，你会怎么回应？",
        "reference_points": [
            "不陷入争抢功劳的当场对峙：先把讨论拉回工作本身（方案后续怎么优化），避免把会议变成争执",
            "陈述事实要克制：如有共享过的记录（文档、群消息、评审记录）可平和提及，但不做人身评价",
            "关注真实动机：对方可能是随口一说、也可能是想争贡献，不必上纲上线；判断是否需要私下沟通",
            "会后处理：必要时与对方一对一聊清楚，或请主管在团队机制上明确贡献记录方式",
            "机制视角：推动团队以文档与评审记录留痕贡献，减少这类争议再次发生",
            "底线：不接受被公开否定到影响他人对我专业能力的判断，此时要澄清而不是默认"
        ],
        "hints": "考察情绪控制与政治敏感度：会上克制、会后解决、机制兜底"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "MEDIUM", "time_limit_sec": 120,
        "text": "如果我把你期望的薪资砍掉 30%，你还会来吗？",
        "reference_points": [
            "不慌张也不立刻妥协：先了解这个数字的构成与是否有其他补偿空间（期权、奖金、成长机会、弹性）",
            "表达自己的判断依据：基于自身能力与市场行情说明期望值的来源，而不是情绪化或直接拒绝",
            "给出可协商的空间与条件：例如试用期后调整、承担更大职责时上调，保持对话开放",
            "诚实底线：如果差距超出可接受范围，平静说明\"这个数字我确实难以接受\"，比虚假答应更专业",
            "关注整体价值：明确岗位成长、团队与技术挑战对自己的权重，并说明取舍逻辑",
            "礼貌收尾：即使谈不拢也保持尊重，为未来保留可能"
        ],
        "hints": "考察谈判心态与自我价值认知，坦诚且不卑不亢最加分"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 150,
        "text": "业务方今天下午就要一个结论，但你的数据还没跑完，你会怎么处理？",
        "reference_points": [
            "先说清约束与不确定性：明确告诉业务方现在能给出什么、不能给出什么，而不是硬编一个结论",
            "给出可用的\"部分答案\"：基于已有数据给出方向性判断，并标注置信度与前提条件",
            "说明数据缺失会带来什么风险，让业务方在知情下决策；把决策责任交还给业务方",
            "争取时间的具体方案：能否缩小范围先跑关键切片、能否用近似口径先用、能给出结论的准确时间点",
            "保留书面记录：把\"这是基于不完整数据的初步判断\"写清楚，避免后续被当成确定结论引用",
            "底线：不伪造数据、不隐瞒不确定性——短期应付会带来更大的信任与决策损失"
        ],
        "hints": "关键动作是「给部分答案 + 标注不确定 + 明确时间」，而不是硬凑结论"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "你负责的模块被要求下线，你投入了三个月的成果作废，你现在什么感受？",
        "reference_points": [
            "先接受事实再表达感受：承认会有失落，但把情绪与后续动作分开说清楚",
            "主动追问原因：是业务方向调整、效果不达预期还是资源问题？理解原因才能判断是否有可挽回的部分",
            "争取有价值的处置：可复用的能力与资产如何沉淀（组件、文档、经验），人员如何调整",
            "反思自己可改进的部分：是否有更早的验证手段、是否应该更早暴露风险（这不是自我否定，而是专业态度）",
            "不把情绪转向团队或合作方：避免抱怨式回答，展现职业成熟度",
            "向前看：明确接下来会把精力投入哪里，展示自我调节与目标感"
        ],
        "hints": "考察情绪成熟度：承认失落、追问原因、争取沉淀，且不迁怒他人"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 150,
        "text": "你带的两个人同时提离职，项目还有两周就要上线，你怎么撑过去？",
        "reference_points": [
            "先冷静评估影响面：他们负责哪些关键路径、能否交接、还有什么工作可以砍",
            "立即与两人沟通：了解真实原因，判断是否有挽留空间（待遇、职责、压力），但不做无法兑现的承诺",
            "重排优先级与范围：与业务方明确\"两周内能交付什么\"，主动砍掉非核心功能换取上线可用",
            "资源求助：向主管申请临时支援、跨团队借人、外包或延后其他项目，而不是自己硬扛",
            "风险透明：把延期风险与取舍尽早向上与业务方同步，避免上线日才暴露",
            "保障团队剩余成员：明确分工、避免过载引发连锁离职，稳定士气",
            "复盘机制层面：关键人依赖是管理问题，后续要建立备份与知识沉淀"
        ],
        "hints": "「主动砍范围 + 向上要资源」比\"我加班顶上\"更体现管理能力"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "HARD", "time_limit_sec": 150,
        "text": "我怀疑你前面几个回答是提前准备好的，你能用一个从没讲过的例子证明吗？",
        "reference_points": [
            "不慌不怒：坦然接受质疑，说明准备面试是正常的，但用的都是真实经历",
            "当场给出一个新例子：选一个细节丰富的真实经历，包含具体时间、数字与当时的困难",
            "细节要可追问：真实经历经得起追问（当时的具体做法、失败的部分、他人反馈）",
            "坦诚边界：如果某段经历记不清细节，如实说明，而不是编造补全",
            "反向展示可信度：主动说明哪些部分可以佐证或提供材料",
            "保持平和：被质疑时不辩解过度也不自我贬低，用事实回应"
        ],
        "hints": "考察临场真实性与抗压：用可追问的细节而非情绪化辩解来回应"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "如果你的直属上级要求你做一件你认为不合规的事，你会怎么做？",
        "reference_points": [
            "先确认理解是否一致：可能对方的表述有歧义，先复述并确认具体要求",
            "明确边界并说明风险：指出可能违反的法规、流程或公司制度，以及会带来的后果（而不只是说\"我不想做\"）",
            "提供替代方案：给出既能达成业务目的又合规的做法，把问题从\"做不做\"转为\"怎么做\"",
            "拒绝要有技巧：不公开对抗、不越级告状，先私下沟通；若无效则按公司举报渠道或书面留痕",
            "保护自己：保留沟通记录，避免成为唯一的责任承担者",
            "底线清晰：涉及违法、数据造假、伪证、资损风险等绝不妥协，宁可承受职业代价"
        ],
        "hints": "重点在「先确认、再给替代方案、底线不退」，避免极端化回答"
    },
    {
        "job_category": "通用", "question_type": "STRESS", "skill_name": "抗压能力",
        "stage": "压力应对", "difficulty": "MEDIUM", "time_limit_sec": 150,
        "text": "客户临时把交付时间提前一半，你的团队明确说做不到，你会怎么回复客户？",
        "reference_points": [
            "先承接态度再谈事实：感谢客户的紧迫需求，明确表达会全力配合，而不是直接说\"不行\"",
            "用事实说明约束：说清当前排期、关键依赖与提前一半意味着什么代价（质量风险、返工、影响其他承诺）",
            "给出可行选项：分批交付（先上核心功能）、增加资源需客户配合的部分、或明确加速所需的额外成本",
            "让客户参与选择：把决策权交回客户，同时说明每个选项的风险与后果",
            "内部先对齐：回复客户前必须与团队和主管确认可承诺的范围，避免对外承诺了内部做不到的事",
            "书面留痕：把达成的调整写进邮件或纪要，避免后续反复变更与扯皮",
            "底线：不为安抚客户而承诺做不到的日期，那只会制造更大的信任危机"
        ],
        "hints": "考察跨方沟通与风险把控：不硬承诺、给选项、内部先对齐"
    },

    # === 补齐 P0-3c 遗漏：系统底层 · 网络 需补 EASY + HARD ===
    {
        "job_category": "系统底层", "question_type": "PROFESSIONAL", "skill_name": "网络",
        "aliases": "网络,TCP,UDP,传输层,协议选型", "stage": "专业基础", "difficulty": "EASY",
        "time_limit_sec": 150,
        "text": "TCP 与 UDP 有什么区别？分别适合什么场景？",
        "reference_points": [
            "TCP 面向连接、可靠有序：有三次握手与四次挥手，靠确认与重传、序号保证不丢不乱，并有流量控制与拥塞控制",
            "UDP 无连接、不可靠：不保证到达与顺序，没有重传与拥塞控制，因此头部开销小、延迟低",
            "TCP 适合：网页、文件传输、数据库连接、需要完整性与顺序的业务",
            "UDP 适合：实时音视频、直播、游戏、DNS——这些场景宁可丢帧也不要因重传造成卡顿",
            "折中方案：QUIC 基于 UDP 在应用层实现可靠性与多路复用，兼顾低延迟与可靠性",
            "选择依据是业务对「可靠有序」与「延迟/开销」的优先级，而不是哪个更先进"
        ],
        "hints": "要给出「选择依据是业务优先级」的判断，而不是背特性对比表"
    },
    {
        "job_category": "系统底层", "question_type": "PROFESSIONAL", "skill_name": "网络",
        "aliases": "网络,HTTP慢,抓包,DNS,TLS,TTFB,tcpdump", "stage": "深度探究",
        "difficulty": "HARD", "time_limit_sec": 240,
        "text": "一次 HTTP 请求很慢，你会如何从网络层面定位问题？",
        "reference_points": [
            "先分段：把一次请求拆成 DNS 解析 → TCP 建连 → TLS 握手 → 等待首字节（TTFB）→ 内容传输，用 curl -w 或浏览器瀑布图量化各段耗时",
            "DNS 段慢：检查解析耗时与本地缓存、递归解析器质量，考虑预解析或更换解析服务",
            "建连段慢：关注跨地域 RTT、丢包与 SYN 重传、是否缺少长连接复用；用 mtr/traceroute 看路径质量",
            "TLS 段慢：握手往返次数、证书链过大、未启用会话复用或 TLS 1.3；可用会话复用与 OCSP stapling 优化",
            "传输段慢：带宽限制、接收窗口与拥塞窗口、丢包导致重传、MTU 与分片问题；用 ss 看重传与队列、tcpdump 抓包确认",
            "TTFB 慢通常是服务端问题：此时网络已通畅，应转向应用与后端依赖排查，不要继续在网络层打转",
            "客户端侧排除：是否被代理/VPN 影响、是否命中缓存、是否为特定网络环境复现",
            "结论要能落到具体一段并给出优化项，而不是笼统说\"网络慢\""
        ],
        "hints": "「分段量化」是唯一正确起点；能指出 TTFB 慢其实与服务端有关，说明你没有把问题都归给网络"
    }
]
