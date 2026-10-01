<template>
  <div class="home-page">
    <!-- Hero Section per Spec Appendix A.1 -->
    <section class="hero-section">
      <div class="hero-container">
        <div class="hero-content">
          <div class="hero-badge">
            <span class="badge-dot"></span>
            AI 赋能 · 职业成长 · 更好你的自己
          </div>
          <h1 class="hero-main-title">
            让每一次面试<br />
            都成为<span class="text-brand-blue">更好的自己</span>
          </h1>
          <p class="hero-desc">
            AI 驱动的模拟面试与职业成长平台，真实双向互动、技术深度追问、能力雷达复盘，从校园到职场，陪你走好每一步。
          </p>
          <div class="hero-cta">
            <router-link to="/register">
              <el-button type="primary" size="large" class="cta-btn primary-cta">
                立即体验 AI 面试舱 →
              </el-button>
            </router-link>
            <router-link to="/jobs">
              <el-button size="large" class="cta-btn secondary-cta">
                浏览公开岗位广场
              </el-button>
            </router-link>
          </div>

          <!-- Real Platform Stats -->
          <div class="platform-stats">
            <div class="stat-box">
              <span class="stat-num">{{ stats.verified_companies || 5 }}+</span>
              <span class="stat-label">合作认证企业</span>
            </div>
            <div class="stat-box">
              <span class="stat-num">{{ stats.published_jobs || 16 }}+</span>
              <span class="stat-label">真实在招职位</span>
            </div>
            <div class="stat-box">
              <span class="stat-num">{{ stats.active_talents || 10 }}+</span>
              <span class="stat-label">注册求职人才</span>
            </div>
            <div class="stat-box">
              <span class="stat-num">{{ stats.simulated_interviews || 10 }}+</span>
              <span class="stat-label">模拟面试完成</span>
            </div>
          </div>
        </div>

        <!-- Hero Visual Mockup -->
        <div class="hero-visual">
          <div class="mockup-card">
            <div class="mockup-header">
              <div class="ai-avatar">
                <el-icon :size="20" color="#2563EB"><Cpu /></el-icon>
              </div>
              <div class="ai-meta">
                <span class="ai-name">经纬职引-智面仓 AI 首席面试官</span>
                <span class="ai-status">● 实时双向音视频交互中</span>
              </div>
            </div>
            <div class="mockup-chat">
              <div class="chat-bubble ai-bubble">
                “请详细聊聊在你的高并发项目中，如何利用 Redis 分布式锁保障库存防超卖？如何规避死锁与锁续期？”
              </div>
              <div class="chat-bubble user-bubble">
                “我们在项目中采用 Redisson 分布式锁，利用其看门狗 (Watchdog) 自动延期机制保障业务线程安全执行...”
              </div>
            </div>
            <div class="mockup-score-bar">
              <div class="score-pill">
                <span>实时表达流利度</span>
                <strong>92 分 (优)</strong>
              </div>
              <div class="score-pill">
                <span>技术核心关键词命中</span>
                <strong style="color: #10B981;">Watchdog, 原子性, Lua</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Four Core Capabilities -->
    <section class="features-section">
      <div class="zh-page-container">
        <div class="section-title-area">
          <h2 class="section-title">四大核心全链路能力</h2>
          <p class="section-subtitle">从岗位发现、简历解析、全真模拟到成长提升，打造个人与企业双向闭环</p>
        </div>

        <div class="feature-grid">
          <div class="feature-card">
            <div class="f-icon bg-blue">
              <el-icon :size="26"><VideoCamera /></el-icon>
            </div>
            <h3 class="f-title">AI 模拟面试仓</h3>
            <p class="f-desc">真实音视频与文本交互，Rubric 六维打分，动态多轮追问与降难补基，还原一线大厂面试体验。</p>
          </div>

          <div class="feature-card">
            <div class="f-icon bg-green">
              <el-icon :size="26"><DocumentChecked /></el-icon>
            </div>
            <h3 class="f-title">简历智能深度解析</h3>
            <p class="f-desc">秒级提炼教育、项目与工作经历，精准定位目标岗位差距并给出表达优化建议，绝不虚构经历。</p>
          </div>

          <div class="feature-card">
            <div class="f-icon bg-amber">
              <el-icon :size="26"><TrendCharts /></el-icon>
            </div>
            <h3 class="f-title">个性化成长路径</h3>
            <p class="f-desc">追踪技能历史变迁，自动将面试暴露的薄弱知识点转化为可执行的学习与定向专项训练任务。</p>
          </div>

          <div class="feature-card">
            <div class="f-icon bg-purple">
              <el-icon :size="26"><OfficeBuilding /></el-icon>
            </div>
            <h3 class="f-title">企业高效协作招聘</h3>
            <p class="f-desc">AI 胜任力模型智能人岗匹配、自动发送 AI 初筛面试邀请、结构化团队评价与敏捷招聘看板。</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 3-Step Process -->
    <section class="process-section">
      <div class="zh-page-container">
        <div class="section-title-area">
          <h2 class="section-title">三步开启你的求职跃升之旅</h2>
          <p class="section-subtitle">简单高效的使用流程，让每一次面试都有清晰前行方向</p>
        </div>

        <div class="process-steps">
          <div class="process-step">
            <div class="step-badge">01</div>
            <h4>注册与完善档案</h4>
            <p>上传或在线创建个人简历，AI 毫秒级提取技能树与经历结构。</p>
          </div>
          <div class="step-connector">→</div>
          <div class="process-step">
            <div class="step-badge">02</div>
            <h4>岗位探索与定向准备</h4>
            <p>基于目标岗位要求与匹配度差距，开展设备检测与专项准备。</p>
          </div>
          <div class="step-connector">→</div>
          <div class="process-step">
            <div class="step-badge">03</div>
            <h4>模拟面试与复盘成长</h4>
            <p>进入面试仓实战对答，获取五维能力雷达报告与可执行学习路线。</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Hot Jobs on Square -->
    <section class="hot-jobs-section">
      <div class="zh-page-container">
        <div class="jobs-header">
          <div>
            <h2 class="section-title">热门公开在招岗位</h2>
            <p class="section-subtitle">来自认证名企的精选职位，支持一键投递与 AI 匹配度分析</p>
          </div>
          <router-link to="/jobs">
            <el-button type="primary" plain>查看全部岗位 ({{ stats.published_jobs || 16 }}) →</el-button>
          </router-link>
        </div>

        <div class="jobs-grid">
          <div
            v-for="job in hotJobs"
            :key="job.id"
            class="job-card zh-card zh-card-hover"
            @click="$router.push(`/jobs/${job.id}`)"
          >
            <div class="job-card-top">
              <div class="job-title-row">
                <h3 class="job-title">{{ job.title }}</h3>
                <span class="job-salary">{{ job.salary_min }}-{{ job.salary_max }}K</span>
              </div>
              <div class="company-name">{{ job.company_name }}</div>
            </div>

            <div class="job-meta">
              <span>{{ job.city }}</span>
              <span class="dot">·</span>
              <span>{{ job.education }}</span>
              <span class="dot">·</span>
              <span>{{ job.experience }}</span>
            </div>

            <div class="job-skills">
              <el-tag
                v-for="(skill, idx) in job.skills"
                :key="idx"
                size="small"
                effect="plain"
                class="skill-tag"
              >
                {{ skill }}
              </el-tag>
            </div>

            <div class="job-card-bottom">
              <span class="match-badge">AI 匹配分析已就绪</span>
              <el-button link type="primary" class="detail-btn">查看详情 →</el-button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { publicApi } from '@/api'
import {
  Cpu, VideoCamera, DocumentChecked, TrendCharts, OfficeBuilding
} from '@element-plus/icons-vue'

const stats = ref<any>({})
const hotJobs = ref<any[]>([])

onMounted(async () => {
  try {
    const res: any = await publicApi.getHome()
    stats.value = res.stats || {}
    hotJobs.value = res.hot_jobs || []
  } catch (e) {
    // handled
  }
})
</script>

<style scoped>
.hero-section {
  background: linear-gradient(180deg, #EFF6FF 0%, #FFFFFF 100%);
  padding: 64px 24px 80px;
}

.hero-container {
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 56px;
  align-items: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #DBEAFE;
  color: #1E40AF;
  padding: 6px 14px;
  border-radius: 9999px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 20px;
}

.badge-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #2563EB;
}

.hero-main-title {
  font-size: 42px;
  font-weight: 800;
  line-height: 1.22;
  color: var(--zh-text-title);
  letter-spacing: -0.025em;
  margin-bottom: 20px;
}

.text-brand-blue {
  color: var(--zh-primary);
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-desc {
  font-size: 16px;
  color: var(--zh-text-body);
  line-height: 1.65;
  margin-bottom: 32px;
  max-width: 540px;
}

.hero-cta {
  display: flex;
  gap: 16px;
  margin-bottom: 48px;
}

.primary-cta {
  height: 48px;
  padding: 0 28px;
  font-size: 15px;
  font-weight: 600;
}

.secondary-cta {
  height: 48px;
  padding: 0 24px;
  font-size: 15px;
}

.platform-stats {
  display: flex;
  gap: 36px;
  border-top: 1px solid var(--zh-border);
  padding-top: 24px;
}

.stat-box {
  display: flex;
  flex-direction: column;
}

.stat-num {
  font-size: 26px;
  font-weight: 800;
  color: var(--zh-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--zh-text-muted);
  margin-top: 2px;
}

.hero-visual {
  display: flex;
  justify-content: center;
}

.mockup-card {
  width: 100%;
  max-width: 480px;
  background: #FFFFFF;
  border-radius: var(--zh-radius-xl);
  box-shadow: 0 20px 35px -10px rgba(37, 99, 235, 0.15), 0 0 1px 1px rgba(226, 232, 240, 0.9);
  padding: 24px;
}

.mockup-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--zh-border-light);
}

.ai-avatar {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  background: #EFF6FF;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-meta {
  display: flex;
  flex-direction: column;
}

.ai-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--zh-text-title);
}

.ai-status {
  font-size: 11px;
  color: #10B981;
}

.mockup-chat {
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.chat-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.55;
}

.ai-bubble {
  background: #EFF6FF;
  color: #1E3A8A;
  align-self: flex-start;
  border-bottom-left-radius: 2px;
}

.user-bubble {
  background: #F1F5F9;
  color: var(--zh-text-body);
  align-self: flex-end;
  border-bottom-right-radius: 2px;
}

.mockup-score-bar {
  display: flex;
  gap: 12px;
  padding-top: 14px;
  border-top: 1px dashed var(--zh-border);
}

.score-pill {
  flex: 1;
  background: #F8FAFC;
  padding: 8px 12px;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  font-size: 11px;
  color: var(--zh-text-muted);
}

.score-pill strong {
  font-size: 13px;
  color: var(--zh-text-title);
  margin-top: 2px;
}

.section-title-area {
  text-align: center;
  margin-bottom: 48px;
}

.section-title {
  font-size: 30px;
  font-weight: 800;
  color: var(--zh-text-title);
  margin-bottom: 8px;
}

.section-subtitle {
  font-size: 15px;
  color: var(--zh-text-muted);
}

.features-section {
  padding: 80px 0;
  background: #FFFFFF;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.feature-card {
  padding: 32px 24px;
  border-radius: var(--zh-radius-lg);
  border: 1px solid var(--zh-border-light);
  background: #FAFCFF;
  transition: all 0.2s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--zh-shadow-hover);
  border-color: #BFDBFE;
}

.f-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.bg-blue { background: #EFF6FF; color: #2563EB; }
.bg-green { background: #ECFDF5; color: #10B981; }
.bg-amber { background: #FFFBEB; color: #F59E0B; }
.bg-purple { background: #F5F3FF; color: #8B5CF6; }

.f-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin-bottom: 8px;
}

.f-desc {
  font-size: 13px;
  color: var(--zh-text-muted);
  line-height: 1.6;
}

.process-section {
  padding: 80px 0;
  background: #F8FAFC;
}

.process-steps {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 960px;
  margin: 0 auto;
}

.process-step {
  flex: 1;
  background: #FFFFFF;
  padding: 28px 24px;
  border-radius: var(--zh-radius-lg);
  box-shadow: var(--zh-shadow-sm);
  border: 1px solid var(--zh-border);
  text-align: center;
}

.step-badge {
  display: inline-block;
  font-size: 18px;
  font-weight: 800;
  color: var(--zh-primary);
  background: var(--zh-primary-light);
  padding: 4px 14px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.process-step h4 {
  font-size: 16px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin-bottom: 6px;
}

.process-step p {
  font-size: 13px;
  color: var(--zh-text-muted);
  line-height: 1.5;
}

.step-connector {
  font-size: 24px;
  color: #94A3B8;
  padding: 0 16px;
}

.hot-jobs-section {
  padding: 80px 0;
  background: #FFFFFF;
}

.jobs-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 36px;
}

.jobs-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.job-card {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.job-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
}

.job-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--zh-text-title);
}

.job-salary {
  font-size: 16px;
  font-weight: 800;
  color: #EF4444;
}

.company-name {
  font-size: 13px;
  color: var(--zh-text-muted);
  margin-bottom: 12px;
}

.job-meta {
  font-size: 12px;
  color: #64748B;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 14px;
}

.dot {
  color: #CBD5E1;
}

.job-skills {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}

.skill-tag {
  border-radius: 4px;
}

.job-card-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--zh-border-light);
  padding-top: 12px;
}

.match-badge {
  font-size: 11px;
  color: #2563EB;
  background: #EFF6FF;
  padding: 2px 8px;
  border-radius: 4px;
}

.detail-btn {
  font-size: 13px;
  font-weight: 600;
}

@media (max-width: 1024px) {
  .hero-container { grid-template-columns: 1fr; }
  .feature-grid { grid-template-columns: repeat(2, 1fr); }
  .jobs-grid { grid-template-columns: repeat(2, 1fr); }
  .process-steps { flex-direction: column; gap: 16px; }
  .step-connector { display: none; }
}
</style>
