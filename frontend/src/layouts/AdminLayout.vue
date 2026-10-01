<template>
  <div class="admin-layout">
    <!-- Admin Top Bar -->
    <header class="admin-header">
      <div class="header-brand">
        <el-icon :size="22" color="#EF4444"><Cpu /></el-icon>
        <span class="brand-title">经纬职引-智面仓 · 平台独立治理与运营后台</span>
      </div>
      <div class="header-right">
        <span class="admin-badge">系统管理员</span>
        <span class="admin-name">{{ authStore.user?.name || '管理员' }}</span>
        <el-button size="small" type="danger" plain @click="authStore.logout">退出后台</el-button>
      </div>
    </header>

    <div class="admin-body">
      <!-- Admin Sidebar -->
      <aside class="admin-sidebar">
        <el-menu
          :default-active="$route.path"
          class="sidebar-menu"
          router
        >
          <el-menu-item index="/admin/dashboard">
            <el-icon><Odometer /></el-icon>
            <span>平台运营总览</span>
          </el-menu-item>
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <span>用户治理管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/companies">
            <el-icon><OfficeBuilding /></el-icon>
            <span>入驻企业管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/verifications">
            <el-icon><Check /></el-icon>
            <span>企业认证审核</span>
          </el-menu-item>
          <el-menu-item index="/admin/jobs/review">
            <el-icon><DocumentChecked /></el-icon>
            <span>发布岗位审核</span>
          </el-menu-item>
          <el-menu-item index="/admin/complaints">
            <el-icon><Warning /></el-icon>
            <span>举报投诉处置</span>
          </el-menu-item>
          <el-menu-item index="/admin/content">
            <el-icon><Tickets /></el-icon>
            <span>首页与公告配置</span>
          </el-menu-item>
          <el-menu-item index="/admin/question-bank">
            <el-icon><Collection /></el-icon>
            <span>结构化题库管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/ai">
            <el-icon><Cpu /></el-icon>
            <span>AI 服务与脱敏日志</span>
          </el-menu-item>
          <el-menu-item index="/admin/security">
            <el-icon><Lock /></el-icon>
            <span>权限与安全审计</span>
          </el-menu-item>
        </el-menu>
      </aside>

      <!-- Admin Main View -->
      <main class="admin-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import {
  Cpu, Odometer, User, OfficeBuilding, Check, DocumentChecked,
  Warning, Tickets, Lock, Collection
} from '@element-plus/icons-vue'

const authStore = useAuthStore()
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.admin-header {
  height: 56px;
  background: #0F172A;
  color: #FFFFFF;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #1E293B;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.admin-badge {
  background: rgba(239, 68, 68, 0.2);
  color: #F87171;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.admin-name {
  font-size: 14px;
  color: #CBD5E1;
}

.admin-body {
  flex: 1;
  display: flex;
  background-color: #F8FAFC;
}

.admin-sidebar {
  width: 230px;
  min-width: 230px;
  background: #FFFFFF;
  border-right: 1px solid var(--zh-border);
}

.sidebar-menu {
  border-right: none;
  padding: 16px 0;
}

.sidebar-menu :deep(.el-menu-item) {
  height: 44px;
  line-height: 44px;
  margin: 2px 10px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background-color: #FEF2F2;
  color: #EF4444;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: #FEF2F2;
  color: #EF4444;
  font-weight: 600;
}

.admin-content {
  flex: 1;
  min-width: 0;
  padding: 24px 28px 48px;
  overflow-y: auto;
}
</style>
