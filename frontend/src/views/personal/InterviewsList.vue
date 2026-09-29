<template>
  <div class="interviews-list-page">
    <div class="header-box zh-card">
      <div class="header-content">
        <div>
          <h2 class="title">模拟面试记录与复盘中心</h2>
          <p class="subtitle">沉淀历史面试对答数据，点击报告可查看五维能力雷达与证据式复盘</p>
        </div>
        <router-link to="/personal/interviews/create">
          <el-button type="primary">发起新面试训练 +</el-button>
        </router-link>
      </div>
    </div>

    <!-- 成长对比 + 薄弱题重练 -->
    <div class="insight-row">
      <div class="insight-card zh-card">
        <div class="ic-head">
          <h3 class="ic-title">同岗位成长对比</h3>
          <el-button v-if="compare.ready" link type="primary" size="small" @click="includeRetrain = !includeRetrain">
            {{ includeRetrain ? '已含重练记录' : '默认排除重练' }}
          </el-button>
        </div>
        <div v-if="compare.ready" class="ic-body">
          <p class="ic-sub">{{ compare.job_title }}｜共 {{ compare.session_count }} 次完成面试</p>
          <div class="delta-line">
            <span class="delta-label">综合得分变化</span>
            <span :class="['delta-value', (compare.total_delta || 0) >= 0 ? 'up' : 'down']">
              {{ (compare.total_delta || 0) >= 0 ? '+' : '' }}{{ compare.total_delta }} 分
            </span>
          </div>
          <div class="dim-list">
            <div v-for="(t, name) in compare.dimension_trends" :key="name" class="dim-item">
              <span class="dim-name">{{ name }}</span>
              <span class="dim-series">{{ t.series.join(' → ') }}</span>
              <span :class="['dim-delta', t.improved ? 'up' : 'flat']">
                {{ t.improved ? '↑' : '·' }} {{ t.delta >= 0 ? '+' : '' }}{{ t.delta }}
              </span>
            </div>
          </div>
        </div>
        <el-empty v-else :image-size="52" :description="compare.message || '至少完成 2 次同岗位面试后生成对比'" />
      </div>

      <div class="insight-card zh-card">
        <div class="ic-head">
          <h3 class="ic-title">我的薄弱题（低于 {{ weak.threshold || 60 }} 分）</h3>
          <el-button
            v-if="weak.items?.length"
            type="warning" size="small" :loading="retraining"
            @click="handleRetrain"
          >
            一键重练 {{ weak.items.length }} 题
          </el-button>
        </div>
        <div v-if="weak.items?.length" class="weak-list">
          <div v-for="w in weak.items" :key="w.bank_id" class="weak-item">
            <div class="wi-top">
              <el-tag size="small" effect="plain">{{ w.skill_name }}</el-tag>
              <el-tag size="small" type="danger" effect="plain">{{ w.latest_score }} 分</el-tag>
              <span class="wi-attempts">已练 {{ w.attempts }} 次</span>
            </div>
            <p class="wi-text">{{ w.text }}</p>
          </div>
        </div>
        <el-empty v-else :image-size="52" description="暂无薄弱题记录，或题库题尚未作答" />
      </div>
    </div>

    <StateContainer :loading="loading" :empty="!loading && interviews.length === 0" empty-text="暂无面试记录" empty-action-text="立即开始模拟面试" @empty-action="$router.push('/personal/interviews/create')">
      <div class="interviews-table-card zh-card">
        <el-table :data="interviews" stripe style="width: 100%;">
          <el-table-column prop="job_title" label="面试目标岗位" min-width="180">
            <template #default="{ row }">
              <strong style="color: var(--zh-text-title);">{{ row.job_title }}</strong>
            </template>
          </el-table-column>

          <el-table-column prop="type" label="性质" width="130">
            <template #default="{ row }">
              <el-tag v-if="row.type === 'ENTERPRISE_RECRUITMENT'" type="warning" size="small">企业招聘面</el-tag>
              <el-tag v-else type="primary" size="small">个人训练面</el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="mode" label="考察模式" width="130">
            <template #default="{ row }">
              {{ getModeText(row.mode) }}
              <el-tag v-if="row.purpose === 'RETRAIN'" size="small" type="warning" effect="plain" class="retrain-tag">重练</el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="score" label="综合得分" width="120">
            <template #default="{ row }">
              <span v-if="row.score" style="font-size: 16px; font-weight: 800; color: #2563EB;">
                {{ row.score }} 分
              </span>
              <span v-else style="color: #94A3B8;">未生成</span>
            </template>
          </el-table-column>

          <el-table-column prop="status" label="面试状态" width="120">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'COMPLETED'" type="success" size="small">已完成</el-tag>
              <el-tag v-else-if="row.status === 'IN_PROGRESS'" type="primary" size="small">进行中</el-tag>
              <el-tag v-else type="info" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="created_at" label="面试时间" width="160" />

          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <router-link v-if="row.status === 'COMPLETED'" :to="`/personal/interviews/${row.id}/report`">
                <el-button link type="primary">查看复盘报告 →</el-button>
              </router-link>
              <router-link v-else :to="`/personal/interviews/${row.id}/room`">
                <el-button link type="warning">继续作答 →</el-button>
              </router-link>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </StateContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { interviewApi } from '@/api'
import StateContainer from '@/components/StateContainer.vue'
import { ElMessage } from 'element-plus'
import type { HistoryComparison, WeakQuestionsResult } from '@/types'

const router = useRouter()
const loading = ref(true)
const interviews = ref<any[]>([])

const compare = ref<Partial<HistoryComparison>>({ ready: false })
const weak = ref<Partial<WeakQuestionsResult>>({ threshold: 60, items: [] })
const includeRetrain = ref(false)
const retraining = ref(false)

const getModeText = (mode: string) => {
  const map: Record<string, string> = {
    TECHNICAL: '技术专项',
    COMPREHENSIVE: '综合模拟',
    PROJECT_DEEP_DIVE: '项目深挖',
    BEHAVIORAL: '行为面试',
    STRESS: '压力训练'
  }
  return map[mode] || mode
}

const loadInsights = async () => {
  try {
    const [cmp, wk] = await Promise.all([
      interviewApi.getHistoryComparison({ include_retrain: includeRetrain.value }),
      interviewApi.getWeakQuestions({ threshold: 60, limit: 8 })
    ])
    compare.value = cmp as any
    weak.value = wk as any
  } catch (e) {
    // handled
  }
}

// 重练：直接用薄弱题 bank_id 走"按指定考卷开考"，标记 purpose=RETRAIN
const handleRetrain = async () => {
  const ids = weak.value.retrain_bank_ids || []
  if (!ids.length) {
    ElMessage.info('暂无可重练的薄弱题')
    return
  }
  retraining.value = true
  try {
    const res: any = await interviewApi.createInterview({
      mode: 'COMPREHENSIVE',
      difficulty: 'MEDIUM',
      total_questions: Math.min(ids.length, 8),
      duration_minutes: Math.min(ids.length, 8) * 5,
      use_question_bank: true,
      selected_bank_ids: ids,
      purpose: 'RETRAIN'
    })
    ElMessage.success('薄弱题重练卷已生成（不计入成长曲线）')
    router.push(`/personal/interviews/${res.id}/room`)
  } catch (e) {
    // handled
  } finally {
    retraining.value = false
  }
}

watch(includeRetrain, loadInsights)

onMounted(async () => {
  loading.value = true
  try {
    const res: any = await interviewApi.listInterviews()
    interviews.value = res || []
  } catch (e) {
    // handled
  } finally {
    loading.value = false
  }
  loadInsights()
})
</script>

<style scoped>
.interviews-list-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 成长洞察双卡 */
.insight-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 1100px) {
  .insight-row { grid-template-columns: 1fr; }
}

.insight-card {
  padding: 18px 20px;
  min-height: 220px;
  display: flex;
  flex-direction: column;
}

.ic-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.ic-title { font-size: 15.5px; font-weight: 800; color: var(--zh-text-title); }
.ic-sub { font-size: 12.5px; color: var(--zh-text-muted); margin-bottom: 8px; }

.delta-line {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #F8FAFC;
  border-radius: 8px;
  padding: 8px 12px;
  margin-bottom: 10px;
}

.delta-label { font-size: 12.5px; color: var(--zh-text-muted); }
.delta-value { font-size: 18px; font-weight: 800; }
.delta-value.up { color: #16A34A; }
.delta-value.down { color: #DC2626; }

.dim-list { display: flex; flex-direction: column; gap: 6px; overflow-y: auto; max-height: 200px; }

.dim-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12.5px;
  padding: 5px 0;
  border-bottom: 1px dashed var(--zh-border);
}

.dim-item:last-child { border-bottom: none; }
.dim-name { width: 68px; font-weight: 600; color: #374151; flex-shrink: 0; }
.dim-series { flex: 1; color: var(--zh-text-muted); font-family: Consolas, monospace; font-size: 12px; }
.dim-delta { font-weight: 700; flex-shrink: 0; }
.dim-delta.up { color: #16A34A; }
.dim-delta.flat { color: #9CA3AF; }

.weak-list { display: flex; flex-direction: column; gap: 10px; overflow-y: auto; max-height: 220px; }

.weak-item {
  background: #FFF7ED;
  border: 1px solid #FED7AA;
  border-radius: 8px;
  padding: 8px 10px;
}

.wi-top { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.wi-attempts { font-size: 11.5px; color: var(--zh-text-muted); margin-left: auto; }
.wi-text {
  font-size: 12.5px;
  color: #7C2D12;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.retrain-tag { margin-left: 6px; }

.header-box {
  padding: 24px 32px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 22px;
  font-weight: 800;
  color: var(--zh-text-title);
  margin-bottom: 6px;
}

.subtitle {
  font-size: 13px;
  color: var(--zh-text-muted);
}

.interviews-table-card {
  padding: 24px;
}
</style>
