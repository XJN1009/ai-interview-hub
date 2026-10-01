<template>
  <div class="about-page zh-page-container">
    <div class="about-card zh-card">
      <h1 class="title">关于经纬职引-智面仓 (AI Interview Hub)</h1>
      <p class="subtitle">设计依据：企业命题 05《智能面试仓的开发与应用》全栈开发规格书 V3.0</p>
      <div class="divider"></div>

      <div class="content-section">
        <h3>项目定位与设计初衷</h3>
        <p>
          在传统求职与招聘过程中，求职者往往面临“缺乏高质量实战面试演练”、“无法量化自身技术差距”、“难以获得专业即时反馈”等痛点；而企业招聘方则承受着“简历海选成本高”、“面试评价标准不一”、“部门协同流程冗长”等挑战。
        </p>
        <p>
          经纬职引-智面仓 (AI Interview Hub) 旨在通过大模型与智能音视频交互技术，打破传统面试的黑箱与壁垒，构建“个人训练—岗位投递—企业筛选—面试协作—成长提升”的双向业务闭环。
        </p>
      </div>

      <div class="content-section">
        <h3>安全、隐私与数据边界</h3>
        <p>
          系统严守国家个人信息保护及算法治理合规标准：
        </p>
        <ul>
          <li><strong>隐私可见性隔离：</strong>个人私人模拟面试与日常学习记录绝对默认企业不可见；仅当投递或授权时，企业才可按范围调阅特定授权材料。</li>
          <li><strong>招聘公平与防偏见：</strong>招聘 AI 筛选仅作为企业辅助参考，最终录用与淘汰决策权在企业人员；严禁基于性别、年龄、外貌等敏感属性进行招聘评分。</li>
          <li><strong>严密 RBAC 权限体系：</strong>从后端底层彻底阻断跨企业、跨个人以及越权篡改角色的安全风险。</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.about-page {
  padding: 48px 20px 80px;
}
.about-card {
  max-width: 860px;
  margin: 0 auto;
  padding: 48px;
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
.divider {
  height: 1px;
  background: var(--zh-border-light);
  margin: 24px 0;
}
.content-section {
  margin-bottom: 32px;
}
h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--zh-text-title);
  margin-bottom: 12px;
}
p {
  font-size: 14px;
  color: var(--zh-text-body);
  line-height: 1.8;
  margin-bottom: 12px;
}
ul {
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 14px;
  color: var(--zh-text-body);
  line-height: 1.6;
}
</style>
