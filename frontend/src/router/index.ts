import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Layouts
import PublicLayout from '@/layouts/PublicLayout.vue'
import PersonalLayout from '@/layouts/PersonalLayout.vue'
import EnterpriseLayout from '@/layouts/EnterpriseLayout.vue'
import AdminLayout from '@/layouts/AdminLayout.vue'

// Error views
import NotFound from '@/views/error/NotFound.vue'
import Forbidden from '@/views/error/Forbidden.vue'

// Auth views
import Login from '@/views/auth/Login.vue'
import RegisterSelect from '@/views/auth/RegisterSelect.vue'
import RegisterPersonal from '@/views/auth/RegisterPersonal.vue'
import RegisterEnterprise from '@/views/auth/RegisterEnterprise.vue'
import Onboarding from '@/views/auth/Onboarding.vue'
import ForgotPassword from '@/views/auth/ForgotPassword.vue'
import AdminLogin from '@/views/auth/AdminLogin.vue'

// Public views
import Home from '@/views/public/Home.vue'
import JobSquare from '@/views/public/JobSquare.vue'
import JobDetail from '@/views/public/JobDetail.vue'
import CompanyPublic from '@/views/public/CompanyPublic.vue'
import Features from '@/views/public/Features.vue'
import About from '@/views/public/About.vue'
import Help from '@/views/public/Help.vue'

// Personal views
import PersonalDashboard from '@/views/personal/Dashboard.vue'
import JobExplore from '@/views/personal/JobExplore.vue'
import Applications from '@/views/personal/Applications.vue'
import Resumes from '@/views/personal/Resumes.vue'
import ResumeEdit from '@/views/personal/ResumeEdit.vue'
import ResumeAnalysis from '@/views/personal/ResumeAnalysis.vue'
import Assessment from '@/views/personal/Assessment.vue'
import InterviewCreate from '@/views/personal/InterviewCreate.vue'
import InterviewSession from '@/views/personal/InterviewSession.vue'
import InterviewsList from '@/views/personal/InterviewsList.vue'
import InterviewReportView from '@/views/personal/InterviewReportView.vue'
import GrowthCenter from '@/views/personal/GrowthCenter.vue'
import LearningRoadmap from '@/views/personal/LearningRoadmap.vue'
import Notifications from '@/views/personal/Notifications.vue'
import Profile from '@/views/personal/Profile.vue'
import Settings from '@/views/personal/Settings.vue'

// Enterprise views
import EnterpriseDashboard from '@/views/enterprise/Dashboard.vue'
import EnterpriseJobs from '@/views/enterprise/Jobs.vue'
import JobCreate from '@/views/enterprise/JobCreate.vue'
import JobEdit from '@/views/enterprise/JobEdit.vue'
import Candidates from '@/views/enterprise/Candidates.vue'
import CandidateDetail from '@/views/enterprise/CandidateDetail.vue'
import PipelineKanban from '@/views/enterprise/PipelineKanban.vue'
import EnterpriseInterviews from '@/views/enterprise/Interviews.vue'
import Evaluation from '@/views/enterprise/Evaluation.vue'
import TalentPool from '@/views/enterprise/TalentPool.vue'
import Analytics from '@/views/enterprise/Analytics.vue'
import Members from '@/views/enterprise/Members.vue'
import EnterpriseSettings from '@/views/enterprise/Settings.vue'

// Admin views
import AdminDashboard from '@/views/admin/Dashboard.vue'
import AdminUsers from '@/views/admin/Users.vue'
import AdminCompanies from '@/views/admin/Companies.vue'
import AdminVerifications from '@/views/admin/Verifications.vue'
import AdminJobReview from '@/views/admin/JobReview.vue'
import AdminComplaints from '@/views/admin/Complaints.vue'
import AdminContent from '@/views/admin/Content.vue'
import AdminQuestionBank from '@/views/admin/QuestionBank.vue'
import AdminAIService from '@/views/admin/AIService.vue'
import AdminSecurityAudit from '@/views/admin/SecurityAudit.vue'

const routes: RouteRecordRaw[] = [
  // 公共门户
  {
    path: '/',
    component: PublicLayout,
    children: [
      { path: '', name: 'Home', component: Home, meta: { title: '智面舱 - AI 智能面试协同平台' } },
      { path: 'jobs', name: 'JobSquare', component: JobSquare, meta: { title: '职位广场' } },
      { path: 'jobs/:id', name: 'JobDetail', component: JobDetail, meta: { title: '职位详情' } },
      { path: 'companies/:id', name: 'CompanyPublic', component: CompanyPublic, meta: { title: '企业主页' } },
      { path: 'features', name: 'Features', component: Features, meta: { title: '核心特性' } },
      { path: 'about', name: 'About', component: About, meta: { title: '关于智面舱' } },
      { path: 'help', name: 'Help', component: Help, meta: { title: '帮助支持' } },
    ]
  },

  // 认证流程
  { path: '/login', name: 'Login', component: Login, meta: { title: '用户登录', guestOnly: true } },
  { path: '/register', name: 'RegisterSelect', component: RegisterSelect, meta: { title: '注册选择', guestOnly: true } },
  { path: '/register/personal', name: 'RegisterPersonal', component: RegisterPersonal, meta: { title: '求职者注册', guestOnly: true } },
  { path: '/register/enterprise', name: 'RegisterEnterprise', component: RegisterEnterprise, meta: { title: '企业雇主注册', guestOnly: true } },
  { path: '/onboarding', name: 'Onboarding', component: Onboarding, meta: { title: '新用户入驻指引', requiresAuth: true } },
  { path: '/forgot-password', name: 'ForgotPassword', component: ForgotPassword, meta: { title: '找回密码' } },
  { path: '/admin/login', name: 'AdminLogin', component: AdminLogin, meta: { title: '平台治理后台登录' } },

  // 独立全屏沉浸式路由 (模拟面试间与报告)
  {
    path: '/personal/interviews/:id/room',
    name: 'PersonalInterviewSession',
    component: InterviewSession,
    meta: { requiresAuth: true, accountType: 'PERSONAL', title: 'AI 实时模拟面试间' }
  },
  {
    path: '/interviews/:id/report',
    name: 'InterviewReport',
    component: InterviewReportView,
    meta: { requiresAuth: true, title: '面试答题诊断报告' }
  },

  // 个人求职者工作台
  {
    path: '/personal',
    component: PersonalLayout,
    meta: { requiresAuth: true, accountType: 'PERSONAL' },
    children: [
      { path: '', redirect: '/personal/dashboard' },
      { path: 'dashboard', name: 'PersonalDashboard', component: PersonalDashboard, meta: { title: '求职者工作台' } },
      { path: 'jobs', name: 'PersonalJobExplore', component: JobExplore, meta: { title: '智能岗位探索' } },
      { path: 'applications', name: 'PersonalApplications', component: Applications, meta: { title: '我的应聘申请' } },
      { path: 'resumes', name: 'PersonalResumes', component: Resumes, meta: { title: '我的简历中心' } },
      { path: 'resumes/create', name: 'PersonalResumeCreate', component: ResumeEdit, meta: { title: '创建在线简历' } },
      { path: 'resumes/:id/edit', name: 'PersonalResumeEdit', component: ResumeEdit, meta: { title: '编辑简历' } },
      { path: 'resumes/:id/analysis', name: 'PersonalResumeAnalysis', component: ResumeAnalysis, meta: { title: '简历 AI 诊断优化' } },
      { path: 'assessment', name: 'PersonalAssessment', component: Assessment, meta: { title: '六维胜任力诊断' } },
      { path: 'interviews', name: 'PersonalInterviewsList', component: InterviewsList, meta: { title: '我的模拟面试' } },
      { path: 'interviews/create', name: 'PersonalInterviewCreate', component: InterviewCreate, meta: { title: '创建模拟面试' } },
      { path: 'growth', name: 'PersonalGrowth', component: GrowthCenter, meta: { title: '个人成长中心' } },
      { path: 'learning', name: 'PersonalLearning', component: LearningRoadmap, meta: { title: 'AI 学习路线图' } },
      { path: 'notifications', name: 'PersonalNotifications', component: Notifications, meta: { title: '消息通知' } },
      { path: 'profile', name: 'PersonalProfile', component: Profile, meta: { title: '求职意向与资料' } },
      { path: 'settings', name: 'PersonalSettings', component: Settings, meta: { title: '账号与安全设置' } },
    ]
  },

  // 企业招聘协作中心
  {
    path: '/enterprise',
    component: EnterpriseLayout,
    meta: { requiresAuth: true, accountType: 'ENTERPRISE' },
    children: [
      { path: '', redirect: '/enterprise/dashboard' },
      { path: 'dashboard', name: 'EnterpriseDashboard', component: EnterpriseDashboard, meta: { title: '企业招聘工作台' } },
      { path: 'jobs', name: 'EnterpriseJobs', component: EnterpriseJobs, meta: { title: '职位管理' } },
      { path: 'jobs/create', name: 'EnterpriseJobCreate', component: JobCreate, meta: { title: '发布职位 (AI-JD)' } },
      { path: 'jobs/:id/edit', name: 'EnterpriseJobEdit', component: JobEdit, meta: { title: '编辑职位' } },
      { path: 'candidates', name: 'EnterpriseCandidates', component: Candidates, meta: { title: '候选人管理' } },
      { path: 'candidates/:id', name: 'EnterpriseCandidateDetail', component: CandidateDetail, meta: { title: '候选人全貌档案' } },
      { path: 'pipeline', name: 'EnterprisePipeline', component: PipelineKanban, meta: { title: '招聘管道看板' } },
      { path: 'interviews', name: 'EnterpriseInterviews', component: EnterpriseInterviews, meta: { title: '面试管理' } },
      { path: 'evaluations', name: 'EnterpriseEvaluation', component: Evaluation, meta: { title: '面试官结构化打分' } },
      { path: 'talent-pool', name: 'EnterpriseTalentPool', component: TalentPool, meta: { title: '企业储备人才库' } },
      { path: 'analytics', name: 'EnterpriseAnalytics', component: Analytics, meta: { title: '招聘数据分析中心' } },
      { path: 'members', name: 'EnterpriseMembers', component: Members, meta: { title: '团队成员与权限' } },
      { path: 'settings', name: 'EnterpriseSettings', component: EnterpriseSettings, meta: { title: '企业资料与实名认证' } },
    ]
  },

  // 平台管理后台
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, roles: ['PLATFORM_ADMIN', 'SUPER_ADMIN'] },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'AdminDashboard', component: AdminDashboard, meta: { title: '平台运营总览' } },
      { path: 'users', name: 'AdminUsers', component: AdminUsers, meta: { title: '全平台用户治理' } },
      { path: 'companies', name: 'AdminCompanies', component: AdminCompanies, meta: { title: '企业治理' } },
      { path: 'verifications', name: 'AdminVerifications', component: AdminVerifications, meta: { title: '企业资质审核' } },
      { path: 'jobs/review', name: 'AdminJobReview', component: AdminJobReview, meta: { title: '岗位审核与下架' } },
      { path: 'jobs-review', redirect: '/admin/jobs/review' },
      { path: 'complaints', name: 'AdminComplaints', component: AdminComplaints, meta: { title: '举报投诉处置' } },
      { path: 'content', name: 'AdminContent', component: AdminContent, meta: { title: '门户内容运营' } },
      { path: 'question-bank', name: 'AdminQuestionBank', component: AdminQuestionBank, meta: { title: '结构化题库管理' } },
      { path: 'ai', name: 'AdminAIService', component: AdminAIService, meta: { title: 'AI 引擎与脱敏日志' } },
      { path: 'security', name: 'AdminSecurityAudit', component: AdminSecurityAudit, meta: { title: '安全与操作审计' } },
    ]
  },

  // 错误路由
  { path: '/403', name: 'Forbidden', component: Forbidden, meta: { title: '403 无访问权限' } },
  { path: '/404', name: 'NotFound', component: NotFound, meta: { title: '404 页面未找到' } },
  { path: '/:pathMatch(.*)*', redirect: '/404' }
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// Navigation Guard
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // Set document title
  if (to.meta.title) {
    document.title = `${to.meta.title} - 智面舱`
  }

  // Check guestOnly routes (e.g. login/register when already logged in)
  if (to.meta.guestOnly && authStore.isAuthenticated) {
    if (authStore.isAdmin) return next('/admin/dashboard')
    if (authStore.isEnterprise) return next('/enterprise/dashboard')
    return next('/personal/dashboard')
  }

  // Check requiresAuth
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      if (to.path.startsWith('/admin')) {
        return next({ path: '/admin/login', query: { redirect: to.fullPath } })
      }
      return next({ path: '/login', query: { redirect: to.fullPath } })
    }

    // Role check for admin
    if (to.meta.roles && Array.isArray(to.meta.roles)) {
      const userRoles = authStore.user?.roles || []
      const hasRole = to.meta.roles.some((r: string) => userRoles.includes(r))
      if (!hasRole) {
        return next('/403')
      }
    }

    // Account type check
    if (to.meta.accountType) {
      if (authStore.user?.account_type !== to.meta.accountType) {
        return next('/403')
      }
    }
  }

  next()
})

export default router
