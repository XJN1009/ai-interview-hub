<template>
  <div class="dashboard-view">
    <StateContainer :loading="loading" :error="error" @retry="loadDashboard">
      <div v-if="dashboardData" class="dashboard-content">
        <!-- Welcome & Target & Today Tasks Unified Hero (Mockup 06) -->
        <div class="welcome-header zh-card">
          <div class="welcome-left">
            <h2 class="welcome-title">你好，{{ dashboardData.welcome?.name || '同学' }}</h2>
            <div class="target-badge-row">
              <span class="target-title-pill">
                <template v-if="dashboardData.welcome?.target_job_title">
                  {{ dashboardData.welcome.target_job_title }}<template v-if="dashboardData.welcome?.target_cities"> · 目标城市：{{ dashboardData.welcome.target_cities }}</template>
                </template>
                <template v-else>
                  尚未设置目标岗位，<router-link to="/personal/profile" class="target-set-link">前往个人档案设置 →</router-link>
                </template>
              </span>
            </div>
            <div class="welcome-action-buttons">
              <router-link to="/personal/interviews/create">
                <el-button type="primary" size="large" class="hero-start-btn">开始模拟面试 →</el-button>
              </router-link>
              <router-link to="/personal/growth">
                <el-button size="large" class="hero-report-btn">查看成长报告</el-button>
              </router-link>
            </div>
          </div>

          <!-- Readiness Circle Center -->
          <div class="readiness-center-col">
            <div class="readiness-ring-wrap">
              <span class="ring-percent">{{ dashboardData.readiness_score != null ? dashboardData.readiness_score + '%' : '--' }}</span>
              <span class="ring-label">当前岗位准备度</span>
            </div>
          </div>

          <!-- Today Core Tasks Right Column -->
          <div class="welcome-right-tasks">
            <div class="tasks-mini-header">
              <span class="tasks-mini-title">今日核心训练任务</span>
              <router-link to="/personal/learning" class="tasks-all-link">全部路线 →</router-link>
            </div>
            <div class="tasks-mini-list">
              <div v-if="!(dashboardData.today_tasks || []).length" class="mini-task-empty">
                暂无训练任务，<router-link to="/personal/learning">生成学习路线 →</router-link>
              </div>
              <div
                v-for="(task, idx) in (dashboardData.today_tasks || []).slice(0, 2)"
                :key="task.id"
                class="mini-task-item"
              >
                <div class="mini-task-badge">{{ Number(idx) + 1 }}</div>
                <div class="mini-task-content">
                  <span class="mini-task-title">{{ task.title }}</span>
                  <div class="mini-task-tags">
                    <el-tag size="small" :type="task.priority === 'HIGH' ? 'danger' : 'warning'">
                      {{ task.priority === 'HIGH' ? '重点突破' : '进阶巩固' }}
                    </el-tag>
                    <span v-if="task.status === 'COMPLETED'" class="task-done-badge">已打卡</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 4 Lightweight Metric Cards -->
        <div class="metrics-row">
          <div class="metric-card zh-card">
            <div class="m-icon bg-blue"><el-icon><Trophy /></el-icon></div>
            <div class="m-content">
              <span class="m-lbl">最近面试分</span>
              <div class="m-val-row">
                <span class="m-val">{{ dashboardData.metrics?.recent_interview_score ?? '--' }}</span>
                <span v-if="dashboardData.metrics?.recent_interview_score != null" class="m-unit">分</span>
                <span v-if="dashboardData.metrics?.recent_interview_score != null" class="m-trend text-green">↑ 良好</span>
              </div>
            </div>
          </div>

          <div class="metric-card zh-card">
            <div class="m-icon bg-green"><el-icon><Document /></el-icon></div>
            <div class="m-content">
              <span class="m-lbl">已投递岗位</span>
              <div class="m-val-row">
                <span class="m-val">{{ dashboardData.metrics?.applied_count || 0 }}</span>
                <span class="m-unit">个</span>
                <span class="m-trend text-blue">同步企业中</span>
              </div>
            </div>
          </div>

          <div class="metric-card zh-card">
            <div class="m-icon bg-amber"><el-icon><Clock /></el-icon></div>
            <div class="m-content">
              <span class="m-lbl">本周训练时长</span>
              <div class="m-val-row">
                <span class="m-val">{{ dashboardData.metrics?.training_hours ?? 0 }}</span>
                <span class="m-unit">小时</span>
                <span class="m-trend text-amber">保持节奏</span>
              </div>
            </div>
          </div>

          <div class="metric-card zh-card">
            <div class="m-icon bg-purple"><el-icon><Star /></el-icon></div>
            <div class="m-content">
              <span class="m-lbl">收藏心仪岗位</span>
              <div class="m-val-row">
                <span class="m-val">{{ dashboardData.metrics?.favorite_count || 0 }}</span>
                <span class="m-unit">个</span>
                <span class="m-trend text-purple">待投递</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Middle Grid: Today Tasks & Growth Trend -->
        <div class="middle-grid">
          <!-- Today Tasks (Max 3) -->
          <div class="today-tasks-card zh-card">
            <div class="card-header">
              <div class="header-left">
                <h3 class="card-title">今日核心训练任务</h3>
                <span class="sub-tip">AI 智能规划 · 突破薄弱技能点</span>
              </div>
              <router-link to="/personal/learning">
                <el-button link type="primary">全部路线 →</el-button>
              </router-link>
            </div>

            <div class="tasks-list">
              <el-empty v-if="!dashboardData.today_tasks?.length" description="暂无训练任务，完成面试或生成学习路线后自动规划" :image-size="80" />
              <div
                v-for="task in dashboardData.today_tasks"
                :key="task.id"
                class="task-item"
              >
                <div class="task-info">
                  <div class="task-title-row">
                    <span class="task-name">{{ task.title }}</span>
                    <el-tag size="small" :type="task.priority === 'HIGH' ? 'danger' : 'warning'">
                      {{ task.priority === 'HIGH' ? '重点突破' : '进阶巩固' }}
                    </el-tag>
                  </div>
                  <span class="task-reason">{{ task.reason }}</span>
                </div>
                <div class="task-action">
                  <el-button
                    v-if="task.status === 'COMPLETED'"
                    type="success"
                    size="small"
                    disabled
                  >
                    已完成
                  </el-button>
                  <el-button
                    v-else
                    type="primary"
                    size="small"
                    @click="handleCompleteTask(task.id)"
                  >
                    去完成
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- Growth Trend Chart -->
          <div class="growth-trend-card zh-card">
            <div class="card-header">
              <h3 class="card-title">面试能力成长轨迹</h3>
              <router-link to="/personal/growth">
                <el-button link type="primary">成长中心 →</el-button>
              </router-link>
            </div>
            <LineChart
              v-if="growthX.length"
              :x-axis-data="growthX"
              :series-data="growthY"
              height="200px"
            />
            <el-empty v-else description="暂无面试历史，完成首场模拟面试后生成成长轨迹" :image-size="80" />
          </div>
        </div>

        <!-- Bottom Grid: Recent Applications & Recommended Jobs -->
        <div class="bottom-grid">
          <!-- Recent Applications -->
          <div class="zh-card">
            <div class="card-header">
              <h3 class="card-title">最近求职进度</h3>
              <router-link to="/personal/applications">
                <el-button link type="primary">查看全部 →</el-button>
              </router-link>
            </div>

            <div v-if="dashboardData.recent_applications?.length > 0" class="apps-list">
              <div
                v-for="app in dashboardData.recent_applications"
                :key="app.id"
                class="app-item"
              >
                <div class="app-left">
                  <h4 class="app-job">{{ app.job_title }}</h4>
                  <span class="app-comp">{{ app.company_name }}</span>
                </div>
                <div class="app-right">
                  <el-tag size="small" :type="getStatusTag(app.status)">
                    {{ getStatusText(app.status) }}
                  </el-tag>
                  <span class="app-date">{{ app.updated_at }}</span>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无求职申请，赶快前往岗位广场投递吧" />
          </div>

          <!-- Recommended Jobs -->
          <div class="zh-card">
            <div class="card-header">
              <h3 class="card-title">高匹配推荐职位</h3>
              <router-link to="/personal/jobs">
                <el-button link type="primary">岗位探索 →</el-button>
              </router-link>
            </div>

            <div class="rec-jobs-list">
              <div
                v-for="job in dashboardData.recommended_jobs"
                :key="job.id"
                class="rec-job-item"
                @click="$router.push(`/jobs/${job.id}`)"
              >
                <div class="rec-job-main">
                  <span class="rec-title">{{ job.title }}</span>
                  <span class="rec-comp">{{ job.company_name }} · {{ job.city }}</span>
                </div>
                <div class="rec-job-side">
                  <span class="rec-salary">{{ job.salary_min }}-{{ job.salary_max }}K</span>
                  <span class="match-pill">{{ job.match_score }}% 匹配</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </StateContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { personalApi } from '@/api'
import StateContainer from '@/components/StateContainer.vue'
import LineChart from '@/components/LineChart.vue'
import { ElMessage } from 'element-plus'
import { Location, Trophy, Document, Clock, Star } from '@element-plus/icons-vue'

const loading = ref(true)
const error = ref(false)
const dashboardData = ref<any>(null)

const growthX = computed(() => dashboardData.value?.growth_chart?.map((i: any) => i.date) ?? [])
const growthY = computed(() => dashboardData.value?.growth_chart?.map((i: any) => i.score) ?? [])

const loadDashboard = async () => {
  loading.value = true
  error.value = false
  try {
    const res: any = await personalApi.getDashboard()
    dashboardData.value = res
  } catch (e) {
    error.value = true
  } finally {
    loading.value = false
  }
}

const handleCompleteTask = async (taskId: number) => {
  try {
    await personalApi.completeTask(taskId)
    ElMessage.success('任务已标记为完成！准备度提升')
    loadDashboard()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '任务打卡失败')
  }
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    SUBMITTED: '已投递',
    VIEWED: '企业已查看',
    AI_SCREENING: 'AI评估中',
    AI_INTERVIEW_PENDING: '待AI面试',
    AI_INTERVIEW_DONE: 'AI面试完成',
    ENTERPRISE_INTERVIEW: '企业面试中',
    OFFER: '已发Offer',
    HIRED: '已录用',
    REJECTED: '未通过',
    WITHDRAWN: '已撤回'
  }
  return map[status] || status
}

const getStatusTag = (status: string): any => {
  if (['HIRED', 'OFFER'].includes(status)) return 'success'
  if (['REJECTED', 'WITHDRAWN'].includes(status)) return 'info'
  if (['AI_INTERVIEW_PENDING', 'ENTERPRISE_INTERVIEW'].includes(status)) return 'warning'
  return 'primary'
}

onMounted(() => {
  loadDashboard()
})
</script>

<style scoped>
.dashboard-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.welcome-header {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1.3fr;
  align-items: center;
  gap: 32px;
  padding: 32px;
  background: #FFFFFF;
  border: 1px solid var(--zh-border);
  border-radius: var(--zh-radius-card);
}

.welcome-left {
  display: flex;
  flex-direction: column;
}

.welcome-title {
  font-size: 26px;
  font-weight: 800;
  color: var(--zh-text-title);
  margin-bottom: 8px;
}

.target-badge-row {
  margin-bottom: 20px;
}

.target-title-pill {
  display: inline-block;
  background: var(--zh-sub-bg);
  border: 1px solid var(--zh-border);
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: var(--zh-text-body);
}

.welcome-action-buttons {
  display: flex;
  align-items: center;
  gap: 12px;
}

.hero-start-btn {
  font-weight: 600 !important;
  padding: 0 20px !important;
}

.hero-report-btn {
  font-weight: 500 !important;
}

.readiness-center-col {
  display: flex;
  justify-content: center;
  align-items: center;
  border-left: 1px dashed var(--zh-border);
  border-right: 1px dashed var(--zh-border);
  padding: 0 20px;
}

.readiness-ring-wrap {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 6px solid #2563EB;
  border-top-color: #BFDBFE;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #FFFFFF;
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.08);
}

.ring-percent {
  font-size: 26px;
  font-weight: 900;
  color: #2563EB;
  line-height: 1.1;
}

.ring-label {
  font-size: 11px;
  color: var(--zh-text-muted);
  margin-top: 2px;
}

.welcome-right-tasks {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tasks-mini-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tasks-mini-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--zh-text-title);
}

.tasks-all-link {
  font-size: 12px;
  color: var(--zh-primary);
}

.tasks-mini-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mini-task-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--zh-sub-bg);
  border-radius: 8px;
  border: 1px solid var(--zh-border-light);
}

.mini-task-badge {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563EB;
  color: #FFFFFF;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.mini-task-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;
}

.mini-task-title {
  font-size: 12.5px;
  color: var(--zh-text-body);
  max-width: 170px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mini-task-tags {
  display: flex;
  align-items: center;
  gap: 6px;
}

.task-done-badge {
  font-size: 11px;
  color: #10B981;
}

.circle-lbl {
  font-size: 11px;
  color: var(--zh-text-muted);
}

.readiness-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.readiness-tip {
  font-size: 11px;
  color: #64748B;
}

.metrics-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.metric-card {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.m-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.bg-blue { background: #EFF6FF; color: #2563EB; }
.bg-green { background: #ECFDF5; color: #10B981; }
.bg-amber { background: #FFFBEB; color: #F59E0B; }
.bg-purple { background: #F5F3FF; color: #8B5CF6; }

.m-content { display: flex; flex-direction: column; }
.m-lbl { font-size: 12px; color: var(--zh-text-muted); margin-bottom: 4px; }
.m-val-row { display: flex; align-items: baseline; gap: 4px; }
.m-val { font-size: 24px; font-weight: 800; color: var(--zh-text-title); line-height: 1; }
.m-unit { font-size: 12px; color: var(--zh-text-muted); }
.m-trend { font-size: 11px; margin-left: 6px; font-weight: 600; }
.text-green { color: #10B981; }
.text-blue { color: #2563EB; }
.text-amber { color: #F59E0B; }
.text-purple { color: #8B5CF6; }

.middle-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.card-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--zh-text-title);
}

.sub-tip {
  font-size: 12px;
  color: var(--zh-text-muted);
  margin-left: 10px;
  font-weight: normal;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #F8FAFC;
  border-radius: 8px;
  border: 1px solid var(--zh-border-light);
}

.task-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.task-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--zh-text-title);
}

.task-reason {
  font-size: 12px;
  color: var(--zh-text-muted);
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.apps-list, .rec-jobs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.app-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid var(--zh-border-light);
}

.app-job { font-size: 14px; font-weight: 600; color: var(--zh-text-title); }
.app-comp { font-size: 12px; color: var(--zh-text-muted); }
.app-right { display: flex; align-items: center; gap: 10px; }
.app-date { font-size: 11px; color: var(--zh-text-muted); }

.rec-job-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-radius: 8px;
  background: #F8FAFC;
  cursor: pointer;
  transition: all 0.15s ease;
}

.rec-job-item:hover {
  background: #EFF6FF;
}

.rec-title { font-size: 14px; font-weight: 600; color: var(--zh-text-title); display: block; }
.rec-comp { font-size: 12px; color: var(--zh-text-muted); }
.rec-job-side { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.rec-salary { font-size: 14px; font-weight: 700; color: #EF4444; }
.match-pill { font-size: 11px; color: #2563EB; }

@media (max-width: 1024px) {
  .metrics-row { grid-template-columns: repeat(2, 1fr); }
  .middle-grid { grid-template-columns: 1fr; }
  .bottom-grid { grid-template-columns: 1fr; }
}
</style>
