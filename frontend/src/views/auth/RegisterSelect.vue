<template>
  <div class="auth-page">
    <div class="register-select-card">
      <div class="brand-top-center">
        <div class="brand-logo-icon">
          <el-icon :size="24" color="#FFFFFF"><Monitor /></el-icon>
        </div>
        <span class="brand-name">经纬职引-智面仓</span>
      </div>

      <div class="select-header">
        <h2 class="title">开启你的职业成长之旅</h2>
        <p class="subtitle">请选择你的身份，开启专属体验</p>
      </div>

      <div class="identity-cards">
        <!-- Personal Candidate Card -->
        <div class="identity-card" @click="$router.push('/register/personal')">
          <div class="card-icon candidate-icon">
            <el-icon :size="36"><UserFilled /></el-icon>
          </div>
          <div class="card-body">
            <h3 class="card-title">我是个人求职者 / 学生</h3>
            <p class="card-desc">探索行业前沿岗位、AI 智能简历解析优化、沉浸式模拟面试训练与能力诊断。</p>
            <ul class="feature-list">
              <li>✓ 全真 AI 模拟面试仓与动态追问</li>
              <li>✓ 智能简历诊断与技能差距雷达</li>
              <li>✓ 定向能力提升与个性化学习路径</li>
            </ul>
          </div>
          <el-button type="primary" class="card-btn">注册个人求职账号 →</el-button>
        </div>

        <!-- Enterprise Recruiter Card -->
        <div class="identity-card" @click="$router.push('/register/enterprise')">
          <div class="card-icon enterprise-icon">
            <el-icon :size="36"><OfficeBuilding /></el-icon>
          </div>
          <div class="card-body">
            <h3 class="card-title">我是企业招聘方 / HR</h3>
            <p class="card-desc">发布企业在招职位、利用 AI 辅助初筛海量简历、发送自动化 AI 面试评估并协同推进。</p>
            <ul class="feature-list">
              <li>✓ AI JD 解析快速建立胜任力模型</li>
              <li>✓ 多维度候选人人岗匹配度与初筛</li>
              <li>✓ 敏捷招聘流程看板与结构化团队评价</li>
            </ul>
          </div>
          <el-button type="success" class="card-btn">注册企业招聘账号 →</el-button>
        </div>
      </div>

      <div class="select-footer">
        已有账号？<router-link to="/login" class="link-primary">直接登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { UserFilled, OfficeBuilding, Monitor } from '@element-plus/icons-vue'
</script>

<style scoped>
.auth-page {
  min-height: calc(100vh - 64px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background-color: var(--zh-bg);
}

.brand-top-center {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 24px;
}

.brand-logo-icon {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  background: var(--zh-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
}

.brand-name {
  font-size: 20px;
  font-weight: 800;
  color: var(--zh-text-title);
  letter-spacing: -0.02em;
}

.register-select-card {
  width: 100%;
  max-width: 860px;
  background: #FFFFFF;
  border-radius: var(--zh-radius-box);
  padding: 48px;
  box-shadow: var(--zh-shadow-card);
  border: 1px solid var(--zh-border);
}

.select-header {
  text-align: center;
  margin-bottom: 40px;
}

.title {
  font-size: 26px;
  font-weight: 800;
  color: var(--zh-text-title);
  margin-bottom: 8px;
}

.subtitle {
  font-size: 14px;
  color: var(--zh-text-muted);
}

.identity-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 32px;
}

.identity-card {
  border: 1.5px solid var(--zh-border);
  border-radius: var(--zh-radius-lg);
  padding: 32px 24px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.identity-card:hover {
  border-color: var(--zh-primary);
  box-shadow: var(--zh-shadow-hover);
  transform: translateY(-3px);
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.candidate-icon {
  background: #EFF6FF;
  color: #2563EB;
}

.enterprise-icon {
  background: #ECFDF5;
  color: #10B981;
}

.card-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin-bottom: 10px;
}

.card-desc {
  font-size: 13px;
  color: var(--zh-text-muted);
  line-height: 1.6;
  margin-bottom: 16px;
}

.feature-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 12px;
  color: var(--zh-text-body);
  margin-bottom: 24px;
}

.card-btn {
  width: 100%;
  height: 42px;
  font-weight: 600;
}

.select-footer {
  text-align: center;
  font-size: 14px;
  color: var(--zh-text-muted);
}

.link-primary {
  color: var(--zh-primary);
  font-weight: 600;
  margin-left: 4px;
}

@media (max-width: 768px) {
  .identity-cards {
    grid-template-columns: 1fr;
  }
}
</style>
