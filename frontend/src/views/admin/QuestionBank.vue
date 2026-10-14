<template>
  <div class="qb-page">
    <div class="page-head">
      <div>
        <h2 class="page-title">结构化题库管理</h2>
        <p class="page-sub">面试组卷引擎的数据源。<strong>只有「已放行」的题目参与组卷</strong>，新批次默认待审；编辑或停用题目仅影响之后的组卷，<strong>历史面试卷面已快照固化，不会变化</strong>；题目只支持停用、不支持物理删除（被历史卷面与错题清单引用）。</p>
      </div>
      <el-button type="primary" @click="openCreate">+ 新增题目</el-button>
    </div>

    <!-- 概览统计 -->
    <div class="stat-row" v-if="stats">
      <div class="stat-card"><span class="v">{{ stats.total }}</span><span class="k">题库总量</span></div>
      <div class="stat-card"><span class="v">{{ stats.enabled }}</span><span class="k">启用中</span></div>
      <div class="stat-card stat-clickable" :class="{ 'stat-warn': stats.pending > 0 }"
           @click="pickReview('PENDING')">
        <span class="v">{{ stats.pending }}</span><span class="k">待审核</span>
      </div>
      <div class="stat-card stat-clickable" @click="pickReview('REJECTED')">
        <span class="v">{{ stats.rejected }}</span><span class="k">已驳回</span>
      </div>
      <div class="stat-card"><span class="v">{{ stats.by_type.PROFESSIONAL || 0 }}</span><span class="k">专业题</span></div>
      <div class="stat-card"><span class="v">{{ stats.by_type.GENERAL || 0 }}</span><span class="k">通用题</span></div>
      <div class="stat-card"><span class="v">{{ stats.by_type.STRESS || 0 }}</span><span class="k">压力题</span></div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar zh-card">
      <el-input v-model="filters.keyword" placeholder="搜索题干 / 技能关键词" clearable style="width: 220px" @keyup.enter="reload(1)" />
      <el-select v-model="filters.job_category" placeholder="岗位大类" clearable style="width: 150px" @change="reload(1)">
        <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
      </el-select>
      <el-select v-model="filters.question_type" placeholder="题型" clearable style="width: 130px" @change="reload(1)">
        <el-option label="专业题" value="PROFESSIONAL" />
        <el-option label="通用题" value="GENERAL" />
        <el-option label="压力题" value="STRESS" />
      </el-select>
      <el-select v-model="filters.difficulty" placeholder="难度" clearable style="width: 120px" @change="reload(1)">
        <el-option label="入门 EASY" value="EASY" />
        <el-option label="标准 MEDIUM" value="MEDIUM" />
        <el-option label="高阶 HARD" value="HARD" />
      </el-select>
      <el-select v-model="filters.enabled" placeholder="状态" clearable style="width: 120px" @change="reload(1)">
        <el-option label="启用中" :value="true" />
        <el-option label="已停用" :value="false" />
      </el-select>
      <el-select v-model="filters.review_status" placeholder="审核状态" clearable style="width: 130px" @change="reload(1)">
        <el-option label="待审核" value="PENDING" />
        <el-option label="已放行" value="APPROVED" />
        <el-option label="已驳回" value="REJECTED" />
      </el-select>
      <el-select v-model="filters.batch" placeholder="灌库批次" clearable style="width: 140px" @change="reload(1)">
        <el-option v-for="b in batches" :key="b" :label="b" :value="b" />
      </el-select>
      <el-button @click="reload(1)">查询</el-button>
      <el-button link type="primary" @click="resetFilters">重置</el-button>
    </div>

    <!-- 按批次审核（D5：分批放行，把 179 题的审核窗口压短） -->
    <div class="batch-panel zh-card" v-if="batchList.length">
      <div class="batch-head">
        <strong>按批次审核</strong>
        <span class="batch-tip">组卷只取「已放行」的题目；新批次默认待审，逐批确认后再入卷。</span>
      </div>
      <div class="batch-rows">
        <div v-for="b in batchList" :key="b.name" class="batch-row">
          <span class="batch-name">{{ b.name }}</span>
          <span class="batch-meta">共 {{ b.total }} · 待审 {{ b.PENDING }} · 已放行 {{ b.APPROVED }} · 已驳回 {{ b.REJECTED }}</span>
          <span class="batch-ops">
            <el-button v-if="b.PENDING" size="small" type="primary" plain
                       :loading="batchBusy === b.name + 'approve'" @click="handleBatchReview(b.name, 'approve')">
              放行本批次
            </el-button>
            <el-button v-if="b.PENDING" size="small" plain
                       :loading="batchBusy === b.name + 'reject'" @click="handleBatchReview(b.name, 'reject')">
              驳回本批次
            </el-button>
            <el-button v-else-if="b.APPROVED" size="small" link type="warning"
                       :loading="batchBusy === b.name + 'pending'" @click="handleBatchReview(b.name, 'pending')">
              重新送审
            </el-button>
          </span>
        </div>
      </div>
    </div>

    <!-- 列表 -->
    <el-table :data="items" v-loading="loading" class="qb-table zh-card" stripe>
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="expand-box">
            <p class="expand-label">题干</p>
            <p class="expand-text">{{ row.text }}</p>
            <p class="expand-label">参考答案要点（{{ row.reference_points.length }} 条）</p>
            <ol class="expand-points">
              <li v-for="(p, i) in row.reference_points" :key="i">{{ p }}</li>
            </ol>
            <p v-if="row.hints" class="expand-hint">临场提示：{{ row.hints }}</p>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="id" label="ID" width="64" />
      <el-table-column label="题型" width="92">
        <template #default="{ row }">
          <el-tag :type="qtypeTag(row.question_type)" size="small" effect="light">{{ qtypeLabel(row.question_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="job_category" label="岗位大类" width="110" />
      <el-table-column prop="skill_name" label="技能" width="120" show-overflow-tooltip />
      <el-table-column prop="stage" label="阶段" width="100" show-overflow-tooltip />
      <el-table-column label="难度" width="90">
        <template #default="{ row }">
          <span :class="['diff', row.difficulty.toLowerCase()]">{{ row.difficulty }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="time_limit_sec" label="限时" width="80">
        <template #default="{ row }">{{ row.time_limit_sec }}s</template>
      </el-table-column>
      <el-table-column prop="usage_count" label="出题次数" width="90" />
      <el-table-column label="来源" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.source === 'SEED' ? 'info' : 'warning'" effect="plain">
            {{ row.source === 'SEED' ? '预置' : '人工' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="审核" width="92">
        <template #default="{ row }">
          <el-tag size="small" :type="reviewTag(row.review_status)" effect="light">
            {{ reviewLabel(row.review_status) }}
          </el-tag>
          <div v-if="row.batch" class="cell-sub">{{ row.batch }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="text" label="题干" min-width="220" show-overflow-tooltip />
      <el-table-column label="启用" width="80" fixed="right">
        <template #default="{ row }">
          <el-switch :model-value="row.enabled" size="small" @change="(v: any) => handleToggle(row, !!v)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="176" fixed="right">
        <template #default="{ row }">
          <template v-if="row.review_status === 'PENDING'">
            <el-button link type="success" size="small" @click="handleReview(row, 'approve')">通过</el-button>
            <el-button link type="danger" size="small" @click="handleReview(row, 'reject')">驳回</el-button>
          </template>
          <el-button v-else link type="warning" size="small" @click="handleReview(row, 'pending')">退回待审</el-button>
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager-row">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="reload()"
        @size-change="reload(1)"
      />
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? `编辑题目 #${editingId}` : '新增题库题目'" width="680px" top="5vh">
      <el-form :model="form" label-width="100px" label-position="left">
        <div class="form-grid">
          <el-form-item label="岗位大类" required>
            <el-select v-model="form.job_category" filterable allow-create default-first-option placeholder="选择或输入新大类" style="width: 100%">
              <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
            </el-select>
          </el-form-item>
          <el-form-item label="题型" required>
            <el-select v-model="form.question_type" style="width: 100%">
              <el-option label="专业题 PROFESSIONAL" value="PROFESSIONAL" />
              <el-option label="通用题 GENERAL" value="GENERAL" />
              <el-option label="压力题 STRESS" value="STRESS" />
            </el-select>
          </el-form-item>
          <el-form-item label="考察技能" required>
            <el-input v-model="form.skill_name" placeholder="如 Redis / Vue3 / 综合素养" />
          </el-form-item>
          <el-form-item label="面试阶段">
            <el-input v-model="form.stage" placeholder="如 专业基础 / 深度探究 / 压力应对" />
          </el-form-item>
          <el-form-item label="难度">
            <el-radio-group v-model="form.difficulty">
              <el-radio-button label="EASY" />
              <el-radio-button label="MEDIUM" />
              <el-radio-button label="HARD" />
            </el-radio-group>
          </el-form-item>
          <el-form-item label="逐题限时(秒)">
            <el-input-number v-model="form.time_limit_sec" :min="30" :max="1800" :step="30" />
          </el-form-item>
        </div>

        <el-form-item label="题干" required>
          <el-input v-model="form.text" type="textarea" :rows="3" placeholder="面试题目正文" />
        </el-form-item>

        <el-form-item label="参考答案要点">
          <div class="points-editor">
            <div v-for="(p, i) in form.reference_points" :key="i" class="point-row">
              <span class="point-idx">{{ i + 1 }}</span>
              <el-input v-model="form.reference_points[i]" placeholder="要点内容" />
              <el-button link type="danger" @click="form.reference_points.splice(i, 1)">删除</el-button>
            </div>
            <el-button link type="primary" @click="form.reference_points.push('')">+ 添加要点</el-button>
          </div>
        </el-form-item>

        <el-form-item label="临场提示">
          <el-input v-model="form.hints" placeholder="答题方向提示（可空）" maxlength="255" show-word-limit />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="form.enabled" active-text="启用" inactive-text="停用" />
        </el-form-item>
        <el-alert v-if="editingId" type="info" :closable="false" show-icon
          title="编辑仅影响之后的组卷；已生成的历史面试报告与卷面快照保持不变。" />
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">{{ editingId ? '保存修改' : '创建题目' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { adminApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { QuestionBankItem } from '@/types'

const loading = ref(false)
const saving = ref(false)
const items = ref<QuestionBankItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const categories = ref<string[]>([])
const batches = ref<string[]>([])
const stats = ref<any>(null)
const batchBusy = ref('')

const filters = reactive({
  keyword: '',
  job_category: '' as string,
  question_type: '' as string,
  difficulty: '' as string,
  enabled: undefined as boolean | undefined,
  review_status: '' as string,
  batch: '' as string
})

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({
  job_category: '',
  question_type: 'PROFESSIONAL',
  skill_name: '',
  stage: '专业基础',
  difficulty: 'MEDIUM',
  text: '',
  reference_points: [] as string[],
  hints: '',
  time_limit_sec: 180,
  enabled: true
})

const qtypeLabel = (t: string) =>
  ({ PROFESSIONAL: '专业题', GENERAL: '通用题', STRESS: '压力题' }[t] || t)
const qtypeTag = (t: string) =>
  (({ PROFESSIONAL: 'primary', GENERAL: 'success', STRESS: 'danger' } as Record<string, any>)[t] || 'info')

const reviewLabel = (t: string) =>
  ({ APPROVED: '已放行', PENDING: '待审核', REJECTED: '已驳回' }[t] || t || '未知')
const reviewTag = (t: string) =>
  (({ APPROVED: 'success', PENDING: 'warning', REJECTED: 'danger' } as Record<string, any>)[t] || 'info')

// 批次审核面板数据：按后端返回的 by_batch 排序，待审多的批次排前面，先处理积压
const batchList = computed(() =>
  Object.entries<any>(stats.value?.by_batch || {})
    .map(([name, v]) => ({ name, total: v.total || 0, PENDING: v.PENDING || 0,
                           APPROVED: v.APPROVED || 0, REJECTED: v.REJECTED || 0 }))
    .sort((a, b) => (b.PENDING - a.PENDING) || a.name.localeCompare(b.name))
)

const pickReview = (status: string) => {
  filters.review_status = filters.review_status === status ? '' : status
  reload(1)
}

const reload = async (p?: number) => {
  if (p) page.value = p
  loading.value = true
  try {
    const res: any = await adminApi.listQuestionBank({
      page: page.value,
      page_size: pageSize.value,
      keyword: filters.keyword || undefined,
      job_category: filters.job_category || undefined,
      question_type: filters.question_type || undefined,
      difficulty: filters.difficulty || undefined,
      enabled: filters.enabled,
      review_status: filters.review_status || undefined,
      batch: filters.batch || undefined
    })
    items.value = res.items || []
    total.value = res.total || 0
    categories.value = res.categories || []
    batches.value = res.batches || []
    stats.value = res.stats
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.keyword = ''
  filters.job_category = ''
  filters.question_type = ''
  filters.difficulty = ''
  filters.enabled = undefined
  filters.review_status = ''
  filters.batch = ''
  reload(1)
}

const openCreate = () => {
  editingId.value = null
  Object.assign(form, {
    job_category: '', question_type: 'PROFESSIONAL', skill_name: '', stage: '专业基础',
    difficulty: 'MEDIUM', text: '', reference_points: [''], hints: '',
    time_limit_sec: 180, enabled: true
  })
  dialogVisible.value = true
}

const openEdit = (row: QuestionBankItem) => {
  editingId.value = row.id
  Object.assign(form, {
    job_category: row.job_category,
    question_type: row.question_type,
    skill_name: row.skill_name,
    stage: row.stage,
    difficulty: row.difficulty,
    text: row.text,
    reference_points: [...(row.reference_points || [])],
    hints: row.hints || '',
    time_limit_sec: row.time_limit_sec,
    enabled: row.enabled
  })
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!form.job_category.trim() || !form.skill_name.trim() || form.text.trim().length < 5) {
    ElMessage.warning('请完整填写岗位大类、技能与题干（题干至少 5 字）')
    return
  }
  saving.value = true
  try {
    const payload = {
      ...form,
      text: form.text.trim(),
      reference_points: form.reference_points.map(p => p.trim()).filter(Boolean)
    }
    if (editingId.value) {
      await adminApi.updateQuestion(editingId.value, payload)
      ElMessage.success('题目已更新，将影响之后的组卷')
    } else {
      await adminApi.createQuestion(payload)
      ElMessage.success('题目已创建（来源标记为人工，重建种子库不会丢失）')
    }
    dialogVisible.value = false
    reload()
  } catch (e) {
    // handled
  } finally {
    saving.value = false
  }
}

const handleToggle = async (row: QuestionBankItem, val: boolean) => {
  try {
    await adminApi.toggleQuestion(row.id, val)
    row.enabled = val
    ElMessage.success(val ? '题目已启用' : '题目已停用（不再参与新组卷）')
  } catch (e) {
    // handled
  }
}

const REVIEW_TEXT: Record<string, string> = {
  approve: '已通过，该题可参与组卷',
  reject: '已驳回，该题不再参与组卷',
  pending: '已退回待审'
}

const handleReview = async (row: QuestionBankItem, action: 'approve' | 'reject' | 'pending') => {
  try {
    const res: any = await adminApi.reviewQuestion(row.id, action)
    row.review_status = res?.review_status || (action === 'approve' ? 'APPROVED' : action === 'reject' ? 'REJECTED' : 'PENDING')
    ElMessage.success(REVIEW_TEXT[action])
    reload()
  } catch (e) {
    // handled
  }
}

const BATCH_CONFIRM: Record<string, { title: string; danger: boolean }> = {
  approve: { title: '确认放行本批次？放行后这些题目会立即参与组卷。', danger: false },
  reject: { title: '确认驳回本批次？被驳回的题目不会参与组卷，可随时退回待审。', danger: true },
  pending: { title: '确认把本批次重新送审？重新送审后这些题目暂不参与组卷，需再次放行。', danger: true }
}

const handleBatchReview = async (batch: string, action: 'approve' | 'reject' | 'pending') => {
  const conf = BATCH_CONFIRM[action]
  try {
    await ElMessageBox.confirm(conf.title, `${batch} · 批量${action === 'approve' ? '放行' : action === 'reject' ? '驳回' : '送审'}`,
      { type: conf.danger ? 'warning' : 'info', confirmButtonText: '确认执行', cancelButtonText: '再看看' })
  } catch {
    return
  }
  batchBusy.value = batch + action
  try {
    const res: any = await adminApi.batchReviewQuestions({ batch, action })
    ElMessage.success(`已处理 ${res?.affected ?? 0} 题，全站剩余待审 ${res?.pending_total ?? 0} 题`)
    await reload()
  } catch (e) {
    // handled
  } finally {
    batchBusy.value = ''
  }
}

onMounted(() => reload(1))
</script>

<style scoped>
.qb-page { display: flex; flex-direction: column; gap: 16px; }

.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.page-title { font-size: 20px; font-weight: 800; color: var(--zh-text-title); }
.page-sub { font-size: 12.5px; color: var(--zh-text-muted); margin-top: 4px; max-width: 820px; line-height: 1.7; }
.page-sub strong { color: #B45309; }

.stat-row { display: flex; gap: 12px; flex-wrap: wrap; }
.stat-card {
  background: #fff; border: 1px solid var(--zh-border); border-radius: 10px;
  padding: 12px 22px; display: flex; flex-direction: column; align-items: center; min-width: 96px;
}
.stat-card .v { font-size: 22px; font-weight: 800; color: var(--zh-primary); }
.stat-card .k { font-size: 12px; color: var(--zh-text-muted); }
.stat-clickable { cursor: pointer; transition: border-color 0.15s, box-shadow 0.15s; }
.stat-clickable:hover { border-color: var(--zh-primary); box-shadow: 0 2px 8px rgba(37, 99, 235, 0.12); }
.stat-warn .v { color: #D97706; }

.batch-panel { padding: 14px 16px; border-radius: 10px; display: flex; flex-direction: column; gap: 10px; }
.batch-head { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
.batch-head strong { font-size: 14px; color: var(--zh-text-title); }
.batch-tip { font-size: 12px; color: var(--zh-text-muted); }
.batch-rows { display: flex; flex-direction: column; gap: 6px; }
.batch-row {
  display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
  padding: 8px 10px; border: 1px solid var(--zh-border); border-radius: 8px; background: #fff;
}
.batch-name { font-size: 13px; font-weight: 700; color: #1F2937; min-width: 96px; }
.batch-meta { font-size: 12.5px; color: var(--zh-text-muted); flex: 1; }
.batch-ops { display: flex; gap: 8px; align-items: center; }

.cell-sub { font-size: 11px; color: var(--zh-text-muted); margin-top: 2px; }

.filter-bar {
  display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
  padding: 14px 16px; border-radius: 10px;
}

.qb-table { border-radius: 10px; }

.diff { font-size: 12px; font-weight: 700; }
.diff.easy { color: #059669; }
.diff.medium { color: #D97706; }
.diff.hard { color: #DC2626; }

.expand-box { padding: 8px 40px 8px 48px; }
.expand-label { font-size: 12px; font-weight: 700; color: var(--zh-text-muted); margin: 8px 0 4px; }
.expand-text { font-size: 13.5px; line-height: 1.7; color: #1F2937; }
.expand-points { margin: 0; padding-left: 20px; font-size: 13px; color: #374151; line-height: 1.9; }
.expand-hint { font-size: 12.5px; color: #6B7280; margin-top: 6px; }

.pager-row { display: flex; justify-content: flex-end; }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 18px; }

.points-editor { width: 100%; display: flex; flex-direction: column; gap: 8px; }
.point-row { display: flex; align-items: center; gap: 8px; }
.point-idx {
  width: 22px; height: 22px; border-radius: 50%; background: var(--zh-primary-light, #EFF6FF);
  color: var(--zh-primary); font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
</style>
