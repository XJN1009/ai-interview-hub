<template>
  <div class="admin-content-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">门户与运营内容配置</h2>
        <p class="page-subtitle">动态配置经纬职引-智面仓公共门户 Banner、热门搜索关键词与官方公告信息</p>
      </div>
      <el-button type="primary" :loading="saving" @click="handleSave">
        保存并发布配置
      </el-button>
    </div>

    <StateContainer :loading="loading" :error="error" @retry="fetchContent">
      <div class="content-card">
        <el-form :model="form" label-position="top">
          <h3 class="section-title">首页 Hero 主视觉横幅</h3>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="主标题标语">
                <el-input v-model="form.hero_title" placeholder="如：AI 驱动的下一代智能面试与人岗精准协同平台" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="副标题描述">
                <el-input v-model="form.hero_subtitle" placeholder="如：为求职者提供多维胜任力雷达图诊断，为企业提供高效闭环招聘" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-divider />

          <h3 class="section-title">广场热门搜索关键词</h3>
          <p class="section-desc">求职者在职位广场搜索栏下方展示的高频热词标签</p>
          <div class="tags-row">
            <el-tag
              v-for="(tag, idx) in form.hot_keywords"
              :key="idx"
              closable
              style="margin-right: 8px; margin-bottom: 8px;"
              @close="removeKeyword(idx)"
            >
              {{ tag }}
            </el-tag>
            <el-input
              v-if="inputTagVisible"
              ref="tagInputRef"
              v-model="inputTagVal"
              size="small"
              style="width: 120px; margin-bottom: 8px;"
              @keyup.enter="handleTagConfirm"
              @blur="handleTagConfirm"
            />
            <el-button v-else size="small" style="margin-bottom: 8px;" @click="showTagInput">
              + 添加关键词
            </el-button>
          </div>

          <el-divider />

          <h3 class="section-title">官方全局公告通知</h3>
          <el-form-item label="全站广播横幅内容 (留空则不展示)">
            <el-input
              v-model="form.broadcast_notice"
              type="textarea"
              :rows="3"
              placeholder="例如：系统将于本周日凌晨 02:00-04:00 进行底层 AI 算力集群升级维护..."
            />
          </el-form-item>
        </el-form>
      </div>
    </StateContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, onMounted } from 'vue'
import StateContainer from '@/components/StateContainer.vue'
import { adminApi } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const error = ref('')

const form = reactive({
  hero_title: 'AI 驱动的下一代智能面试与人岗精准协同平台',
  hero_subtitle: '多维胜任力深度评测 · 沉浸式模拟实战 · 企业精准招募全闭环',
  hot_keywords: ['Python', 'Go', '大模型算法', 'FastAPI', '分布式微服务', 'Vue3', '后端架构师'],
  broadcast_notice: ''
})

const inputTagVisible = ref(false)
const inputTagVal = ref('')
const tagInputRef = ref()

const showTagInput = () => {
  inputTagVisible.value = true
  nextTick(() => {
    tagInputRef.value?.focus()
  })
}

const handleTagConfirm = () => {
  if (inputTagVal.value.trim() && !form.hot_keywords.includes(inputTagVal.value.trim())) {
    form.hot_keywords.push(inputTagVal.value.trim())
  }
  inputTagVisible.value = false
  inputTagVal.value = ''
}

const removeKeyword = (idx: number) => {
  form.hot_keywords.splice(idx, 1)
}

const fetchContent = async () => {
  loading.value = true
  error.value = ''
  try {
    const res: any = await adminApi.getContent()
    if (res) {
      if (res.hero_title) form.hero_title = res.hero_title
      if (res.hero_subtitle) form.hero_subtitle = res.hero_subtitle
      if (res.hot_keywords && Array.isArray(res.hot_keywords)) form.hot_keywords = res.hot_keywords
      if (res.broadcast_notice) form.broadcast_notice = res.broadcast_notice
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || '获取内容配置失败'
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    await adminApi.updateContent(form)
    ElMessage.success('运营内容配置已生效并更新')
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchContent()
})
</script>

<style scoped>
.admin-content-page {
  max-width: 1100px;
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

.content-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #F1F5F9;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1E293B;
  margin: 0 0 8px 0;
}

.section-desc {
  font-size: 13px;
  color: #64748B;
  margin: 0 0 16px 0;
}

.tags-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}
</style>
