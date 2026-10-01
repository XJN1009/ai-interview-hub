<template>
  <div class="enterprise-interviews-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">面试管理中心</h2>
        <p class="page-subtitle">统一查看 AI 初筛面试与真人结构化面试安排，跟进评测报告与面试官协同评价</p>
      </div>
      <el-button type="primary" @click="openInviteDialog">
        <el-icon style="margin-right: 4px;"><Calendar /></el-icon> 发起面试邀请
      </el-button>
    </div>

    <!-- 筛选面板 -->
    <div class="filter-card">
      <el-row :gutter="16">
        <el-col :xs="24" :sm="8" :md="6">
          <el-select v-model="filters.type" placeholder="面试类型" clearable @change="fetchInterviews">
            <el-option label="全部类型" value="" />
            <el-option label="AI 智能初筛 (AI_MOCK)" value="AI_MOCK" />
            <el-option label="企业真人面试 (ENTERPRISE_RECRUITMENT)" value="ENTERPRISE_RECRUITMENT" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="8" :md="6">
          <el-select v-model="filters.status" placeholder="面试状态" clearable @change="fetchInterviews">
            <el-option label="全部状态" value="" />
            <el-option label="待面试 (PENDING)" value="PENDING" />
            <el-option label="进行中 (IN_PROGRESS)" value="IN_PROGRESS" />
            <el-option label="已完成 (COMPLETED)" value="COMPLETED" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="8" :md="6">
          <el-button type="primary" @click="fetchInterviews">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 数据表格 -->
    <StateContainer :loading="loading" :error="error" :empty="interviews.length === 0" @retry="fetchInterviews">
      <div class="table-card">
        <el-table :data="interviews" style="width: 100%;">
          <el-table-column prop="candidate_name" label="候选人" min-width="140">
            <template #default="{ row }">
              <span style="font-weight: 600; color: #1E293B;">
                {{ row.user?.profile?.name || row.user?.name || `用户 #${row.user_id}` }}
              </span>
            </template>
          </el-table-column>

          <el-table-column prop="job_title" label="应聘职位" min-width="160">
            <template #default="{ row }">
              <span>{{ row.job?.title || '未关联职位' }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="session_type" label="面试类型" width="160">
            <template #default="{ row }">
              <el-tag :type="row.session_type === 'AI_MOCK' ? 'primary' : 'warning'" size="small">
                {{ row.session_type === 'AI_MOCK' ? 'AI 智能初筛' : '企业真人面试' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="status" label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="row.status === 'COMPLETED' ? 'success' : 'info'">
                {{ row.status === 'COMPLETED' ? '已完成' : (row.status === 'IN_PROGRESS' ? '进行中' : '待面试') }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="total_score" label="AI 评分" width="110">
            <template #default="{ row }">
              <span v-if="row.report?.total_score" class="score-text">
                {{ row.report.total_score }} 分
              </span>
              <span v-else style="color: #94A3B8; font-size: 13px;">未出报告</span>
            </template>
          </el-table-column>

          <el-table-column prop="created_at" label="面试时间" width="150">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>

          <el-table-column label="操作" width="220" fixed="right" align="right">
            <template #default="{ row }">
              <el-button
                v-if="row.report"
                type="primary"
                link
                size="small"
                @click="$router.push(`/interviews/${row.id}/report`)"
              >
                查看报告
              </el-button>
              <el-button
                type="success"
                link
                size="small"
                @click="$router.push(`/enterprise/evaluations?interview_id=${row.id}`)"
              >
                面试官评价
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </StateContainer>

    <!-- 发起邀请弹窗 -->
    <el-dialog v-model="showInviteDialog" title="发起面试邀请" width="540px">
      <el-form :model="inviteForm" label-position="top">
        <el-form-item label="选择应聘候选人">
          <el-select v-model="inviteForm.application_id" placeholder="选择候选人" style="width: 100%;">
            <el-option
              v-for="c in candidatesList"
              :key="c.id"
              :label="`${c.user?.profile?.name || c.user?.name} - ${c.job?.title}`"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="面试类型">
          <el-radio-group v-model="inviteForm.session_type">
            <el-radio label="AI_MOCK">AI 智能初筛 (自主限时完成)</el-radio>
            <el-radio label="ENTERPRISE_RECRUITMENT">企业真人结构化面试 (视频协同)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="计划面试时间">
          <el-date-picker
            v-model="inviteForm.scheduled_at"
            type="datetime"
            placeholder="选择面试时间"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="会议地点/说明">
          <el-input v-model="inviteForm.location" placeholder="如：经纬职引-智面仓协同会议室 / 腾讯会议" />
        </el-form-item>
        <el-form-item label="附言">
          <el-input v-model="inviteForm.note" type="textarea" :rows="2" placeholder="请提前测试麦克风与摄像头..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showInviteDialog = false">取消</el-button>
        <el-button type="primary" :loading="inviting" @click="handleSendInvite">发送邀请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Calendar } from '@element-plus/icons-vue'
import StateContainer from '@/components/StateContainer.vue'
import { enterpriseApi } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const error = ref('')
const interviews = ref<any[]>([])
const candidatesList = ref<any[]>([])

const filters = reactive({
  type: '',
  status: ''
})

const fetchInterviews = async () => {
  loading.value = true
  error.value = ''
  try {
    const res: any = await enterpriseApi.listInterviews()
    let list = res || []
    if (filters.type) list = list.filter((i: any) => i.session_type === filters.type)
    if (filters.status) list = list.filter((i: any) => i.status === filters.status)
    interviews.value = list
  } catch (err: any) {
    error.value = err.response?.data?.detail || '获取面试列表失败'
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.type = ''
  filters.status = ''
  fetchInterviews()
}

// 邀请弹窗
const showInviteDialog = ref(false)
const inviting = ref(false)
const inviteForm = reactive({
  application_id: undefined as number | undefined,
  session_type: 'ENTERPRISE_RECRUITMENT',
  scheduled_at: new Date(Date.now() + 86400000),
  location: '经纬职引-智面仓实时视频协同会议室',
  note: '请准时出席面试'
})

const openInviteDialog = async () => {
  try {
    const res: any = await enterpriseApi.listCandidates()
    candidatesList.value = res.items || res || []
    if (candidatesList.value.length > 0) {
      inviteForm.application_id = candidatesList.value[0].id
    }
  } catch {}
  showInviteDialog.value = true
}

const handleSendInvite = async () => {
  if (!inviteForm.application_id) {
    ElMessage.warning('请选择候选人')
    return
  }
  inviting.value = true
  try {
    await enterpriseApi.sendInvitation({
      application_id: inviteForm.application_id,
      session_type: inviteForm.session_type,
      scheduled_at: inviteForm.scheduled_at.toISOString(),
      location: inviteForm.location,
      note: inviteForm.note
    })
    ElMessage.success('面试邀请已发送')
    showInviteDialog.value = false
    fetchInterviews()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '发送面试邀请失败')
  } finally {
    inviting.value = false
  }
}

const formatDate = (val: string) => {
  if (!val) return '-'
  return new Date(val).toLocaleString('zh-CN', { hour12: false })
}

onMounted(() => {
  fetchInterviews()
})
</script>

<style scoped>
.enterprise-interviews-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #0F2347;
  margin: 0 0 6px 0;
}

.page-subtitle {
  font-size: 14px;
  color: #64748B;
  margin: 0;
}

.filter-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #F1F5F9;
}

.table-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #F1F5F9;
}

.score-text {
  font-weight: 700;
  color: #10B981;
}
</style>
