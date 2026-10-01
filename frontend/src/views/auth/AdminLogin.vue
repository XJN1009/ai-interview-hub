<template>
  <div class="admin-login-page">
    <div class="admin-card">
      <div class="admin-header">
        <div class="admin-icon">
          <el-icon :size="32" color="#EF4444"><Cpu /></el-icon>
        </div>
        <h2 class="title">经纬职引-智面仓 · 平台独立治理后台</h2>
        <p class="subtitle">仅限平台管理员与超管登入，所有操作均计入全局审计日志</p>
      </div>

      <el-form class="login-form" @submit.prevent="handleAdminLogin">
        <el-form-item label="管理员账号">
          <el-input
            v-model="account"
            placeholder="admin@example.com"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item label="安全访问密码">
          <el-input
            v-model="password"
            type="password"
            placeholder="请输入密码 (演示: 123456)"
            size="large"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-button
          type="danger"
          class="submit-btn"
          size="large"
          :loading="loading"
          @click="handleAdminLogin"
        >
          安全认证并登入后台
        </el-button>
      </el-form>

      <div class="admin-footer">
        <router-link to="/" class="link-muted">← 返回前台官网</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { Cpu, User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const account = ref('admin@example.com')
const password = ref('123456')
const loading = ref(false)

const handleAdminLogin = async () => {
  if (!account.value || !password.value) {
    ElMessage.warning('请输入管理员账号与密码')
    return
  }

  loading.value = true
  try {
    await authStore.adminLogin({
      account: account.value,
      password: password.value
    })
    ElMessage.success('管理员认证通过，进入平台治理总览')
    router.push('/admin/dashboard')
  } catch (e) {
    // handled
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.admin-login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0F172A;
  padding: 20px;
}

.admin-card {
  width: 100%;
  max-width: 440px;
  background: #1E293B;
  border: 1px solid #334155;
  border-radius: var(--zh-radius-xl);
  padding: 44px 36px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.admin-header {
  text-align: center;
  margin-bottom: 32px;
}

.admin-icon {
  width: 56px;
  height: 56px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.title {
  font-size: 20px;
  font-weight: 700;
  color: #F8FAFC;
  margin-bottom: 6px;
}

.subtitle {
  font-size: 12px;
  color: #94A3B8;
  line-height: 1.5;
}

.login-form :deep(.el-form-item__label) {
  color: #CBD5E1;
  font-size: 13px;
}

.login-form :deep(.el-input__wrapper) {
  background-color: #0F172A;
  box-shadow: 0 0 0 1px #334155 inset !important;
}

.login-form :deep(.el-input__inner) {
  color: #F8FAFC;
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-weight: 600;
  margin-top: 12px;
}

.admin-footer {
  text-align: center;
  margin-top: 24px;
}

.link-muted {
  color: #94A3B8;
  font-size: 13px;
}
.link-muted:hover {
  color: #F8FAFC;
}
</style>
