<template>
  <div class="help-page zh-page-container">
    <div class="page-header">
      <h1 class="title">帮助中心与常见问题</h1>
      <p class="subtitle">全面解答关于使用经纬职引-智面仓模拟面试、简历投递与企业协同的疑问</p>
    </div>

    <div class="help-content zh-card">
      <el-collapse v-model="activeNames">
        <el-collapse-item title="Q1: AI 模拟面试仓需要开启摄像头或麦克风吗？" name="1">
          <div>系统支持完整的音视频互动；若您的设备缺少摄像头或浏览器拒绝授权，系统会自动启用“文本输入模式”进行兜底演示，不影响面试整体流程与复盘报告的生成。</div>
        </el-collapse-item>
        <el-collapse-item title="Q2: 模拟面试的中途如果意外断网或关闭网页怎么办？" name="2">
          <div>面试会话状态完全持久化保存在后端数据库与会话缓存中。当您重新进入面试仓时，系统会自动恢复之前的题目序号与历史对答，支持断点继续作答。</div>
        </el-collapse-item>
        <el-collapse-item title="Q3: 企业能够看到我个人的模拟面试和学习记录吗？" name="3">
          <div>绝对不能。规格书在数据边界中严格规定：个人私人训练记录默认仅本人可见。企业仅能查看求职者在投递时明确授权的简历版本以及针对该企业特定招聘面试生成的评估报告。</div>
        </el-collapse-item>
        <el-collapse-item title="Q4: 为什么新注册的企业不能直接在岗位广场发布职位？" name="4">
          <div>为了保障求职者的合法权益与岗位真实性，新注册企业处于 UNVERIFIED 状态，需在企业设置中提交营业执照资质核验，经平台管理员审核通过后方可正式上架招聘岗位。</div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const activeNames = ref(['1', '2', '3'])
</script>

<style scoped>
.help-page {
  padding: 48px 20px 80px;
}
.page-header {
  text-align: center;
  margin-bottom: 36px;
}
.title {
  font-size: 28px;
  font-weight: 800;
  color: var(--zh-text-title);
  margin-bottom: 8px;
}
.subtitle {
  font-size: 14px;
  color: var(--zh-text-muted);
}
.help-content {
  max-width: 860px;
  margin: 0 auto;
  padding: 32px;
}
</style>
