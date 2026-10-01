<template>
  <div class="public-layout">
    <Navbar />
    <main class="public-main">
      <router-view />
    </main>
    <footer class="public-footer">
      <div class="footer-container">
        <div class="footer-info">
          <div class="footer-logo">
            <span class="logo-title">经纬职引-智面仓 AI Interview Hub</span>
            <span class="logo-tag">全栈智能面试与招聘协作平台</span>
          </div>
          <p class="footer-desc">面向个人职业成长与企业人才筛选的双向闭环系统。基于能力雷达、动态追问与真实人岗匹配，赋能每一次面试与招聘抉择。</p>
        </div>
        <div class="footer-links">
          <div class="link-group">
            <h4>产品矩阵</h4>
            <router-link to="/features">核心能力</router-link>
            <router-link to="/jobs">公开岗位广场</router-link>
            <router-link to="/personal/interviews/create">AI 模拟面试舱</router-link>
            <router-link to="/personal/growth">个人成长路线</router-link>
          </div>
          <div class="link-group">
            <h4>企业协同</h4>
            <router-link to="/register/enterprise">企业免费入驻</router-link>
            <router-link to="/enterprise/dashboard">招聘协作工作台</router-link>
            <router-link to="/enterprise/pipeline">敏捷招聘看板</router-link>
          </div>
          <div class="link-group">
            <h4>支持与合规</h4>
            <router-link to="/about">关于经纬职引-智面仓</router-link>
            <router-link to="/help">帮助中心</router-link>
            <a href="javascript:void(0);">隐私政策与授权</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© 2026 经纬职引-智面仓 (AI Interview Hub) V3.0 版权所有 · 基于《智能面试仓的开发与应用》命题全栈开发</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import Navbar from '@/components/Navbar.vue'
</script>

<style scoped>
.public-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.public-main {
  flex: 1;
}

.public-footer {
  background: #0F172A;
  color: #94A3B8;
  padding: 48px 24px 24px;
  border-top: 1px solid #1E293B;
}

.footer-container {
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 2fr 3fr;
  gap: 48px;
}

.footer-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.logo-title {
  font-size: 20px;
  font-weight: 700;
  color: #FFFFFF;
}

.logo-tag {
  display: block;
  font-size: 12px;
  color: #60A5FA;
  margin-top: 4px;
}

.footer-desc {
  font-size: 13px;
  line-height: 1.6;
  max-width: 420px;
}

.footer-links {
  display: flex;
  justify-content: space-around;
  gap: 24px;
}

.link-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.link-group h4 {
  font-size: 14px;
  font-weight: 600;
  color: #F8FAFC;
  margin-bottom: 4px;
}

.link-group a {
  font-size: 13px;
  color: #94A3B8;
  transition: color 0.15s;
}

.link-group a:hover {
  color: #60A5FA;
}

.footer-bottom {
  max-width: 1280px;
  margin: 40px auto 0;
  padding-top: 20px;
  border-top: 1px solid #1E293B;
  text-align: center;
  font-size: 12px;
}
</style>
