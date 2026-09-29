<template>
  <div class="growth-center-page">
    <div class="header-box zh-card">
      <div class="header-content">
        <div>
          <h2 class="title">长期职业能力成长中心</h2>
          <p class="subtitle">记录从首次模拟面试到当前阶段的能力跃迁轨迹，量化见证技能积累</p>
        </div>
        <el-radio-group v-model="period" size="small" @change="loadGrowth">
          <el-radio-button label="30d">近 30 天</el-radio-button>
          <el-radio-button label="90d">近 90 天</el-radio-button>
          <el-radio-button label="ALL">全部历史</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <StateContainer :loading="loading" :error="error" @retry="loadGrowth">
      <div v-if="growthData" class="growth-grid">
        <!-- 3 Stats Top -->
        <div class="stats-cards">
          <div class="stat-card zh-card">
            <span class="lbl">累计模拟面试</span>
            <span class="val">{{ growthData.interview_count || 0 }} 场</span>
          </div>
          <div class="stat-card zh-card">
            <span class="lbl">当前平均面试分</span>
            <span class="val text-blue">{{ growthData.avg_score != null ? growthData.avg_score + ' 分' : '暂无' }}</span>
          </div>
          <div class="stat-card zh-card">
            <span class="lbl">学习计划任务完成率</span>
            <span class="val text-green">{{ growthData.completed_tasks_rate != null ? growthData.completed_tasks_rate + '%' : '暂无' }}</span>
          </div>
        </div>

        <!-- Score Trend Line Chart -->
        <div class="chart-card zh-card">
          <h3 class="sec-title">面试技术得分长期演进趋势</h3>
          <LineChart
            v-if="growthData.has_data"
            :x-axis-data="trendDates"
            :series-data="trendScores"
            height="260px"
          />
          <el-empty v-else description="暂无面试记录，完成模拟面试后将在此展示得分趋势" :image-size="90" />
        </div>

        <!-- Skill Progression Paths (e.g., Redis 43 -> 52 -> 61 -> 76 per Spec U12) -->
        <div class="progression-card zh-card">
          <h3 class="sec-title">核心技能分演进轨迹 (来自真实面试历史)</h3>
          <p class="sec-tip">系统根据历次对答表现实时累积能力点：</p>

          <div v-if="growthData.skill_progressions?.length" class="progression-list">
            <div
              v-for="sk in growthData.skill_progressions"
              :key="sk.skill"
              class="progression-item"
            >
              <div class="p-left">
                <span class="p-skill">{{ sk.skill }}</span>
                <span class="p-path">{{ sk.history_path }}</span>
              </div>
              <div class="p-right">
                <span class="p-curr">当前 {{ sk.current }} 分</span>
                <el-progress :percentage="sk.current" :stroke-width="6" :show-text="false" color="#2563EB" style="width: 140px;" />
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无技能累积记录" :image-size="90" />
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

const loading = ref(true)
const error = ref(false)
const period = ref('30d')
const growthData = ref<any>(null)

const trendDates = computed(() => growthData.value?.score_trend?.map((i: any) => i.date) ?? [])
const trendScores = computed(() => growthData.value?.score_trend?.map((i: any) => i.score) ?? [])

const loadGrowth = async () => {
  loading.value = true
  error.value = false
  try {
    const res: any = await personalApi.getGrowth(period.value)
    growthData.value = res
  } catch (e) {
    error.value = true
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadGrowth()
})
</script>

<style scoped>
.growth-center-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

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

.growth-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.stat-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.stat-card .lbl {
  font-size: 13px;
  color: var(--zh-text-muted);
  margin-bottom: 8px;
}

.stat-card .val {
  font-size: 28px;
  font-weight: 900;
  color: var(--zh-text-title);
}

.text-blue { color: #2563EB !important; }
.text-green { color: #10B981 !important; }

.chart-card, .progression-card {
  padding: 28px;
}

.sec-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin-bottom: 12px;
}

.sec-tip {
  font-size: 12px;
  color: var(--zh-text-muted);
  margin-bottom: 20px;
}

.progression-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.progression-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: #F8FAFC;
  border-radius: 8px;
  border: 1px solid var(--zh-border-light);
}

.p-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.p-skill {
  font-size: 15px;
  font-weight: 700;
  color: var(--zh-text-title);
  width: 100px;
}

.p-path {
  font-size: 13px;
  color: #2563EB;
  background: #EFF6FF;
  padding: 4px 12px;
  border-radius: 6px;
  font-family: monospace;
  font-weight: 600;
}

.p-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.p-curr {
  font-size: 14px;
  font-weight: 700;
  color: var(--zh-text-title);
}

@media (max-width: 768px) {
  .stats-cards { grid-template-columns: 1fr; }
  .progression-item { flex-direction: column; align-items: flex-start; gap: 10px; }
}
</style>
