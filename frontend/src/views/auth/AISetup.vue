<template>
  <div class="ai-setup-page">
    <div class="setup-card">
      <div class="setup-header">
        <div class="setup-logo">
          <el-icon :size="20" color="#FFFFFF"><Cpu /></el-icon>
        </div>
        <div>
          <h2 class="setup-title">AI 引擎初始化配置</h2>
          <p class="setup-desc">配置您的大语言模型服务（兼容 OpenAI 协议），保存后立即生效，无需重启</p>
        </div>
      </div>

      <el-alert
        v-if="!loading && !configured"
        type="info"
        :closable="false"
        class="setup-alert"
        title="当前未配置 API Key，系统将以内置沙箱引擎 (Mock) 运行，AI 功能为演示数据。"
      />
      <el-alert
        v-else-if="!loading"
        :type="form.mode === 'MOCK' ? 'warning' : 'success'"
        :closable="false"
        class="setup-alert"
        :title="form.mode === 'MOCK' ? '当前引擎模式：内置沙箱 (Mock)' : '当前引擎模式：真实大语言模型 (Real)'"
      />

      <el-form :model="form" label-position="top" class="setup-form">
        <el-form-item label="服务引擎模式">
          <el-radio-group v-model="form.mode">
            <el-radio-button label="REAL">真实大模型 (Real)</el-radio-button>
            <el-radio-button label="MOCK">内置沙箱 (Mock)</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="API 服务 Base URL" required>
          <el-input
            v-model="form.base_url"
            placeholder="https://api.openai.com/v1"
            :disabled="form.mode === 'MOCK'"
          />
          <div class="field-tip">
            常见服务商示例：
            <span
              v-for="p in presets"
              :key="p.url"
              class="preset-link"
              @click="applyPreset(p)"
            >{{ p.name }}</span>
          </div>
        </el-form-item>

        <el-form-item label="模型标识 (Model Name)" required>
          <el-input
            v-model="form.model"
            placeholder="如：gpt-4o-mini, deepseek-chat, qwen-plus"
            :disabled="form.mode === 'MOCK'"
          />
        </el-form-item>

        <el-form-item label="API Key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            :placeholder="apiKeyMasked ? `已保存 (${apiKeyMasked})，留空表示不修改` : '请输入 API Key'"
            :disabled="form.mode === 'MOCK'"
          />
          <div class="field-tip">Key 仅保存在本实例数据库中，页面只回显掩码，不会明文展示。</div>
        </el-form-item>

        <div class="setup-actions">
          <el-button
            :loading="testing"
            :disabled="form.mode === 'MOCK'"
            @click="handleTest"
          >
            测试连接
          </el-button>
          <el-button type="primary" :loading="saving" @click="handleSave">保存配置</el-button>
          <el-button text @click="goBack">返回登录</el-button>
        </div>

        <el-alert
          v-if="testResult"
          :type="testResult.success ? 'success' : 'error'"
          :closable="true"
          class="test-result"
          :title="testResult.message"
          @close="testResult = null"
        />
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Cpu } from '@element-plus/icons-vue'
import { publicApi } from '@/api'

const router = useRouter()

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const configured = ref(false)
const apiKeyMasked = ref('')
const testResult = ref<{ success: boolean; message: string } | null>(null)

const form = reactive({
  mode: 'REAL',
  base_url: 'https://api.openai.com/v1',
  model: 'gpt-4o-mini',
  api_key: ''
})

const presets = [
  { name: 'OpenAI', url: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  { name: 'DeepSeek', url: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  { name: '通义千问', url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus' },
  { name: 'Kimi', url: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k' },
  { name: '本地 Ollama', url: 'http://localhost:11434/v1', model: 'qwen2.5' }
]

const applyPreset = (p: typeof presets[number]) => {
  form.base_url = p.url
  form.model = p.model
}

const fetchCurrent = async () => {
  loading.value = true
  try {
    const res: any = await publicApi.getAISettings()
    if (res) {
      form.mode = res.mode === 'MOCK' ? 'MOCK' : 'REAL'
      form.base_url = res.base_url || form.base_url
      form.model = res.model || form.model
      apiKeyMasked.value = res.api_key_masked || ''
      configured.value = !!res.configured
    }
  } catch {
    // 读取失败时保持默认值，允许用户直接填写
  } finally {
    loading.value = false
  }
}

const handleTest = async () => {
  if (!form.base_url || !form.model) {
    ElMessage.warning('请先填写 Base URL 与模型名称')
    return
  }
  if (!form.api_key && !configured.value) {
    ElMessage.warning('请先填写 API Key')
    return
  }
  testing.value = true
  testResult.value = null
  try {
    const res: any = await publicApi.testAISettings({
      base_url: form.base_url,
      api_key: form.api_key,
      model: form.model
    })
    testResult.value = res || { success: false, message: '测试接口无返回' }
  } catch (err: any) {
    testResult.value = { success: false, message: err.message || '测试请求失败' }
  } finally {
    testing.value = false
  }
}

const handleSave = async () => {
  if (form.mode === 'REAL' && (!form.base_url || !form.model)) {
    ElMessage.warning('真实模型模式下必须填写 Base URL 与模型名称')
    return
  }
  saving.value = true
  try {
    const payload: any = { mode: form.mode, base_url: form.base_url, model: form.model }
    if (form.api_key) payload.api_key = form.api_key
    const res: any = await publicApi.updateAISettings(payload)
    ElMessage.success(res?.message || '配置已保存并生效')
    await fetchCurrent()
    form.api_key = ''
  } catch (err: any) {
    ElMessage.error(err.message || '保存配置失败')
  } finally {
    saving.value = false
  }
}

const goBack = () => {
  router.push('/login')
}

onMounted(fetchCurrent)
</script>

<style scoped>
.ai-setup-page {
  min-height: calc(100vh - 64px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  background: linear-gradient(145deg, #172554 0%, #0F172A 100%);
}

.setup-card {
  width: 100%;
  max-width: 640px;
  background: #FFFFFF;
  border-radius: 16px;
  padding: 36px 40px;
  box-shadow: 0 20px 50px rgba(15, 35, 71, 0.35);
}

.setup-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
}

.setup-logo {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #2563EB;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.setup-title {
  font-size: 20px;
  font-weight: 800;
  color: #0F2347;
  margin: 0 0 4px 0;
}

.setup-desc {
  font-size: 13px;
  color: #64748B;
  margin: 0;
}

.setup-alert {
  margin-bottom: 18px;
}

.setup-form {
  margin-top: 8px;
}

.field-tip {
  font-size: 12px;
  color: #94A3B8;
  margin-top: 6px;
  line-height: 1.6;
}

.preset-link {
  color: #2563EB;
  cursor: pointer;
  margin-right: 10px;
}

.preset-link:hover {
  text-decoration: underline;
}

.setup-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-top: 8px;
}

.test-result {
  margin-top: 16px;
}
</style>
