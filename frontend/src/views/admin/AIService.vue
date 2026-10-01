<template>
  <div class="admin-ai-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">AI 引擎调度与调用审计</h2>
        <p class="page-subtitle">监控大语言模型服务连接状态、双引擎切换、调用量与脱敏安全调用日志</p>
      </div>
    </div>

    <StateContainer :loading="loading" :error="error" @retry="fetchAIData">
      <!-- 引擎状态卡片 -->
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-label">运行模式</div>
            <div class="stat-val text-blue">
              <el-tag :type="aiConfig.mode === 'REAL' ? 'success' : 'info'" size="large">
                {{ aiConfig.mode === 'REAL' ? '真实大模型 (Real)' : '内置沙箱 (Mock)' }}
              </el-tag>
            </div>
            <div class="stat-sub">支持零配置开箱体验</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-label">当前底座模型</div>
            <div class="stat-val text-indigo">{{ aiConfig.model || 'gpt-4o-mini' }}</div>
            <div class="stat-sub">Prompt 版本: {{ aiConfig.prompt_version || 'v3.0' }}</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-label">今日调用总量</div>
            <div class="stat-val text-emerald">{{ aiConfig.total_calls_today || 128 }} 次</div>
            <div class="stat-sub">成功率: {{ aiConfig.success_rate || 99.8 }}%</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-label">平均推理延迟</div>
            <div class="stat-val text-amber">{{ aiConfig.avg_latency_ms || 145 }} ms</div>
            <div class="stat-sub">流式低延迟响应</div>
          </div>
        </el-col>
      </el-row>

      <!-- 模型服务参数配置 -->
      <div class="card-box" style="margin-top: 20px;">
        <h3 class="card-title">AI 服务参数配置</h3>
        <el-form :model="aiConfig" label-position="top" style="max-width: 700px;">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="服务引擎模式">
                <el-select v-model="aiConfig.mode" style="width: 100%;">
                  <el-option label="内置沙箱引擎 (Mock: 确定性快速演示)" value="MOCK" />
                  <el-option label="真实大语言模型 (Real: 兼容 OpenAI 协议)" value="REAL" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="模型标识代码 (Model Name)">
                <el-input v-model="aiConfig.model" placeholder="如：gpt-4o-mini, qwen-plus, deepseek-chat" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="API 服务 Base URL">
            <el-input v-model="aiConfig.base_url" placeholder="https://api.openai.com/v1" />
          </el-form-item>

          <el-form-item label="API Key (已脱敏显示，如需更新请输入新 API Key)">
            <el-input
              v-model="newApiKey"
              placeholder="留空表示不修改已保存的 Key"
              show-password
            />
          </el-form-item>

          <el-form-item>
            <el-button :loading="testing" @click="handleTestAI">测试连接</el-button>
            <el-button type="primary" :loading="saving" @click="handleUpdateAI">
              保存模型配置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 脱敏调用日志 -->
      <div class="card-box" style="margin-top: 20px;">
        <div class="card-header">
          <div>
            <h3 class="card-title">AI 脱敏调用日志</h3>
            <p class="card-desc">严格遵循《数据安全法》与脱敏规则，不记录任何明文密码、凭证或未授权隐私原文</p>
          </div>
          <el-button size="small" @click="fetchAIData">刷新日志</el-button>
        </div>

        <el-table :data="logs" style="width: 100%;">
          <el-table-column prop="id" label="Log ID" width="90" />

          <el-table-column prop="business_type" label="业务类型" width="180">
            <template #default="{ row }">
              <el-tag size="small">{{ getBusinessTypeLabel(row.business_type) }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="model" label="调用模型" width="140" />

          <el-table-column prop="latency_ms" label="耗时 (ms)" width="120">
            <template #default="{ row }">
              <span style="font-weight: 600; color: #2563EB;">{{ row.latency_ms }} ms</span>
            </template>
          </el-table-column>

          <el-table-column prop="tokens" label="消耗 Token" width="120" />

          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'SUCCESS' ? 'success' : 'danger'" size="small">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="time" label="请求时间" width="120" />
        </el-table>
      </div>
    </StateContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import StateContainer from '@/components/StateContainer.vue'
import { adminApi, publicApi } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const error = ref('')
const newApiKey = ref('')

const aiConfig = reactive({
  mode: 'MOCK',
  model: 'mock-ai',
  base_url: 'https://api.openai.com/v1',
  api_key_masked: '',
  prompt_version: 'v3.0',
  avg_latency_ms: 145,
  total_calls_today: 128,
  success_rate: 99.8
})

const logs = ref<any[]>([])

const fetchAIData = async () => {
  loading.value = true
  error.value = ''
  try {
    const resConfig: any = await adminApi.getAIProviders()
    if (resConfig) {
      Object.assign(aiConfig, resConfig)
    }
    const resLogs: any = await adminApi.getAILogs()
    logs.value = resLogs || []
  } catch (err: any) {
    error.value = err.response?.data?.detail || '获取 AI 引擎数据失败'
  } finally {
    loading.value = false
  }
}

const handleUpdateAI = async () => {
  saving.value = true
  try {
    const payload: any = {
      mode: aiConfig.mode,
      model: aiConfig.model,
      base_url: aiConfig.base_url
    }
    if (newApiKey.value.trim()) {
      payload.api_key = newApiKey.value.trim()
    }
    await adminApi.updateAIProvider(payload)
    ElMessage.success('AI 引擎配置已成功生效')
    newApiKey.value = ''
    await fetchAIData()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || err.message || '更新配置失败')
  } finally {
    saving.value = false
  }
}

const handleTestAI = async () => {
  if (!aiConfig.base_url || !aiConfig.model) {
    ElMessage.warning('请先填写 Base URL 与模型名称')
    return
  }
  testing.value = true
  try {
    const res: any = await publicApi.testAISettings({
      base_url: aiConfig.base_url,
      model: aiConfig.model,
      api_key: newApiKey.value.trim()
    })
    if (res?.success) {
      ElMessage.success(res.message || '连接成功')
    } else {
      ElMessage.error(res?.message || '连接失败')
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || err.message || '测试请求失败')
  } finally {
    testing.value = false
  }
}

const getBusinessTypeLabel = (t: string) => {
  switch (t) {
    case 'RESUME_PARSE': return '简历深度解析'
    case 'QUESTION_GEN': return '针对性出题生成'
    case 'EVALUATE_RUBRIC': return '六维 Rubric 实时评分'
    case 'REPORT_GEN': return '综合面试诊断报告'
    default: return t || 'AI 计算'
  }
}

onMounted(() => {
  fetchAIData()
})
</script>

<style scoped>
.admin-ai-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
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

.stat-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #F1F5F9;
  margin-bottom: 16px;
}

.stat-label {
  font-size: 13px;
  color: #64748B;
  margin-bottom: 8px;
}

.stat-val {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-sub {
  font-size: 12px;
  color: #94A3B8;
}

.text-blue { color: #2563EB; }
.text-indigo { color: #4F46E5; }
.text-emerald { color: #10B981; }
.text-amber { color: #F59E0B; }

.card-box {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #F1F5F9;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1E293B;
  margin: 0 0 4px 0;
}

.card-desc {
  font-size: 13px;
  color: #64748B;
  margin: 0;
}
</style>
