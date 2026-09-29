<template>
  <div class="assessment-page">
    <StateContainer :loading="loading" :error="error" @retry="loadAssessment">
      <div v-if="assessmentData" class="assessment-container">
        <!-- Top Summary Card -->
        <div class="top-card zh-card">
          <div class="card-left">
            <h2 class="title">个人综合能力深度诊断</h2>
            <p class="subtitle">可解释地比对个人多维能力画像与目标岗位【{{ assessmentData.target_job }}】的胜任力基准</p>
          </div>
          <div class="overall-badge">
            <span class="lbl">胜任力契合指数</span>
            <span class="num">{{ assessmentData.overall_score }}</span>
          </div>
        </div>

        <!-- Middle: Radar Chart & Priority Enhancements -->
        <div class="middle-grid">
          <!-- Radar Chart Card -->
          <div class="radar-card zh-card">
            <h3 class="sec-title">能力模型多维雷达对照</h3>
            <RadarChart
              v-if="radarIndicators.length"
              :indicators="radarIndicators"
              :values="radarValues"
              :compare-values="radarCompareValues"
              height="340px"
            />
            <el-empty v-else description="暂无能力数据" :image-size="90" />
          </div>

          <!-- Priority Gaps Card -->
          <div class="priority-card zh-card">
            <h3 class="sec-title">优先突破重点 (差距 × 岗位权重)</h3>
            <p class="priority-tip">系统自动为您计算高收益突破技能，优先练习可最快提升面试通过率：</p>

            <div class="priority-list">
              <div
                v-for="(item, idx) in assessmentData.priority_improvements"
                :key="idx"
                class="priority-item"
              >
                <div class="p-rank">{{ Number(idx) + 1 }}</div>
                <div class="p-info">
                  <div class="p-title-row">
                    <span class="p-name">{{ item.name }}</span>
                    <span class="p-gap text-red">差距: -{{ item.gap }}分</span>
                  </div>
                  <span class="p-evidence">证据来源: {{ item.evidence }}</span>
                </div>
                <router-link to="/personal/interviews/create">
                  <el-button size="small" type="primary" plain>专项强化</el-button>
                </router-link>
              </div>
            </div>
          </div>
        </div>

        <!-- Bottom: Comprehensive Breakdown Table -->
        <div class="table-card zh-card">
          <h3 class="sec-title">各项能力细项评分与证据溯源</h3>
          <el-table :data="assessmentData.competencies" stripe style="width: 100%;">
            <el-table-column prop="name" label="能力维度 / 考察点" min-width="150" />
            <el-table-column prop="current_score" label="当前掌握得分" width="130">
              <template #default="{ row }">
                <strong style="color: #2563EB;">{{ row.current_score }} 分</strong>
              </template>
            </el-table-column>
            <el-table-column prop="required_score" label="岗位基准要求" width="130">
              <template #default="{ row }">
                {{ row.required_score }} 分
              </template>
            </el-table-column>
            <el-table-column prop="weight" label="岗位权重" width="110">
              <template #default="{ row }">
                {{ row.weight }}%
              </template>
            </el-table-column>
            <el-table-column prop="gap" label="差距" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.gap > 0" type="danger" size="small">-{{ row.gap }}</el-tag>
                <el-tag v-else type="success" size="small">达标</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="evidence" label="证据与评分来源" min-width="220" />
          </el-table>
        </div>
      </div>
    </StateContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { personalApi } from '@/api'
import StateContainer from '@/components/StateContainer.vue'
import RadarChart from '@/components/RadarChart.vue'

const loading = ref(true)
const error = ref(false)
const assessmentData = ref<any>(null)

const radarIndicators = computed(() => assessmentData.value?.radar?.indicators ?? [])
const radarValues = computed(() => assessmentData.value?.radar?.current_values ?? [])
const radarCompareValues = computed(() => assessmentData.value?.radar?.required_values ?? [])

const loadAssessment = async () => {
  loading.value = true
  error.value = false
  try {
    const res: any = await personalApi.getAssessment()
    assessmentData.value = res
  } catch (e) {
    error.value = true
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAssessment()
})
</script>

<style scoped>
.assessment-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.top-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 32px;
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

.overall-badge {
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  border-radius: 12px;
  padding: 12px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.overall-badge .lbl {
  font-size: 11px;
  color: #2563EB;
  margin-bottom: 2px;
}

.overall-badge .num {
  font-size: 28px;
  font-weight: 900;
  color: #2563EB;
}

.middle-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 24px;
}

.radar-card, .priority-card, .table-card {
  padding: 28px;
}

.sec-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin-bottom: 16px;
}

.priority-tip {
  font-size: 12px;
  color: var(--zh-text-muted);
  margin-bottom: 16px;
  line-height: 1.5;
}

.priority-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.priority-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  background: #F8FAFC;
  border: 1px solid var(--zh-border-light);
  border-radius: 8px;
}

.p-rank {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #EF4444;
  color: #FFFFFF;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.p-info {
  flex: 1;
}

.p-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.p-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--zh-text-title);
}

.p-gap {
  font-size: 12px;
  font-weight: 600;
}

.text-red { color: #EF4444; }

.p-evidence {
  font-size: 11px;
  color: var(--zh-text-muted);
}

@media (max-width: 900px) {
  .middle-grid { grid-template-columns: 1fr; }
}
</style>
