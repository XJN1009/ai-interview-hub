import client from './client'
import type { UserInfo, ExternalApplicationItem, JobItem, ResumeItem, ResumeDocumentItem, ApplicationItem, InterviewSession, InterviewReportData, PaperPreview, HistoryComparison, WeakQuestionsResult, QuestionBankListResult } from '@/types'

export const authApi = {
  getRealtimeTicket: (channel: string, resource_id: number) => client.post("/realtime/ticket", { channel, resource_id }),
  login: (data: any) => client.post('/auth/login', data),
  logout: () => client.post('/auth/logout'),
  getMe: () => client.get<any, UserInfo>('/auth/me'),
  registerPersonal: (data: any) => client.post('/auth/register/personal', data),
  registerEnterprise: (data: any) => client.post('/auth/register/enterprise', data),
  updateOnboarding: (data: any) => client.put('/personal/onboarding', data),
  changePassword: (data: any) => client.post('/auth/change-password', data),
  forgotPassword: (email: string) => client.post('/auth/forgot-password', { email }),
  resetPassword: (data: any) => client.post('/auth/reset-password', data),
}

export const publicApi = {
  getHome: () => client.get('/public/home'),
  getHotJobs: () => client.get('/jobs/hot'),
  getCompanyPublic: (id: number) => client.get(`/companies/${id}/public`),
  getCompanyJobs: (id: number) => client.get(`/companies/${id}/jobs`),
  getAISettings: () => client.get('/public/ai-settings'),
  updateAISettings: (data: any) => client.put('/public/ai-settings', data),
  testAISettings: (data: any) => client.post('/public/ai-settings/test', data),
  getAIStats: () => client.get('/public/ai-stats'),
}

export const jobApi = {
  listJobs: (params: any) => client.get<any, { items: JobItem[]; total: number; page: number; total_pages: number }>('/jobs', { params }),
  getJobDetail: (id: number) => client.get<any, JobItem>(`/jobs/${id}`),
  favoriteJob: (id: number) => client.post(`/jobs/${id}/favorite`),
  unfavoriteJob: (id: number) => client.delete(`/jobs/${id}/favorite`),
  recordOfficialVisit: (id: number) => client.post(`/jobs/${id}/official-visit`),
}

export const resumeApi = {
  listResumes: () => client.get<any, ResumeItem[]>('/resumes'),
  getResume: (id: number) => client.get<any, ResumeItem>(`/resumes/${id}`),
  createResume: (data: any) => client.post<any, ResumeItem>('/resumes', data),
  updateResume: (id: number, data: any) => client.put<any, ResumeItem>(`/resumes/${id}`, data),
  deleteResume: (id: number) => client.delete(`/resumes/${id}`),
  optimizeResume: (id: number) => client.post(`/resumes/${id}/optimize`),
  applyOptimization: (id: number) => client.post(`/resumes/${id}/optimize/apply`),
  uploadFile: (formData: FormData) => client.post('/files/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
}

export const resumeDocumentApi = {
  list: () => client.get<any, ResumeDocumentItem[]>('/resume-documents'),
  create: (data: { file_url: string; file_name: string }) => client.post<any, ResumeDocumentItem>('/resume-documents', data),
  remove: (id: number) => client.delete(`/resume-documents/${id}`),
  parse: (id: number) => client.post<any, ResumeItem>(`/resume-documents/${id}/parse`, null, { timeout: 150000 }),
}

export const applicationApi = {
  listExternal: () => client.get<any, ExternalApplicationItem[]>('/external-applications'),
  updateExternal: (id: number, data: { status: string; note: string }) => client.patch(`/external-applications/${id}`, data),
  listApplications: (params?: any) => client.get<any, ApplicationItem[]>('/applications', { params }),
  getApplication: (id: number) => client.get<any, ApplicationItem>(`/applications/${id}`),
  withdrawApplication: (id: number, data: { reason: string }) => client.post(`/applications/${id}/withdraw`, data),
  acceptInvitation: (id: number) => client.post(`/interview-invitations/${id}/accept`),
  declineInvitation: (id: number) => client.post(`/interview-invitations/${id}/decline`),
}

export const personalApi = {
  getDashboard: () => client.get('/personal/dashboard'),
  getRecommendedJobs: () => client.get('/personal/jobs/recommended'),
  getJobMatch: (jobId: number) => client.get(`/personal/job-match/${jobId}`),
  getAssessment: (jobId?: number) => client.get('/personal/assessment', { params: { job_id: jobId } }),
  getCompetencies: () => client.get('/personal/competencies'),
  getGrowth: (period?: string) => client.get('/personal/growth', { params: { period } }),
  getLearningPlan: () => client.get('/learning/plans/current'),
  regenerateLearningPlan: (data?: any) => client.post('/learning/plans/generate', data || {}),
  completeTask: (id: number) => client.post(`/learning/tasks/${id}/complete`),
  updateTaskProgress: (id: number, progress: number) => client.patch(`/learning/tasks/${id}`, null, { params: { progress } }),
  getProfile: () => client.get('/personal/profile'),
  updateProfile: (data: any) => client.patch('/personal/profile', data),
  getNotifications: () => client.get('/notifications'),
  markNotificationRead: (id: number) => client.patch(`/notifications/${id}/read`),
  markAllNotificationsRead: () => client.post('/notifications/read-all'),
  getNotificationPreferences: () => client.get('/notifications/preferences'),
  updateNotificationPreferences: (data: any) => client.patch('/notifications/preferences', data),
  getConsents: () => client.get('/consents'),
  revokeConsent: (id: number) => client.delete(`/consents/${id}`),
  getSessions: () => client.get('/security/sessions'),
  revokeSession: (id: string) => client.delete(`/security/sessions/${id}`),
  getPersonalAIConfig: () => client.get('/personal/ai-config'),
  updatePersonalAIConfig: (data: any) => client.put('/personal/ai-config', data),
  resetPersonalAIConfig: () => client.delete('/personal/ai-config'),
  testPersonalAIConfig: (data: any) => client.post('/personal/ai-config/test', data),
  getPersonalAIUsage: () => client.get('/personal/ai-usage'),
}

export const interviewApi = {
  createInterview: (data: any) => client.post<any, InterviewSession>('/interviews', data),
  listInterviews: () => client.get('/interviews'),
  getInterview: (id: number) => client.get<any, InterviewSession>(`/interviews/${id}`),
  startInterview: (id: number) => client.post(`/interviews/${id}/start`),
  pauseInterview: (id: number) => client.post(`/interviews/${id}/pause`),
  resumeInterview: (id: number) => client.post(`/interviews/${id}/resume`),
  answerQuestion: async (id: number, data: any) => {
    const key = `zh_answer_request_${id}_${data.question_id}`
    const saved = sessionStorage.getItem(key)
    const pending = saved ? JSON.parse(saved) : { ...data, request_id: crypto.randomUUID() }
    if (pending.text !== data.text || !!pending.skipped !== !!data.skipped) {
      throw new Error('上次提交的答案已保存，请先恢复原答案并重试；成功后再回答下一题')
    }
    sessionStorage.setItem(key, JSON.stringify(pending))
    const result = await client.post(`/interviews/${id}/answer`, pending, { timeout: 120000 })
    sessionStorage.removeItem(key)
    return result
  },
  finishInterview: (id: number) => client.post(`/interviews/${id}/finish`, null, { timeout: 120000 }),
  // 反问环节：逐题作答结束后进入，候选人的提问不计入总分
  getReverse: (id: number) => client.get<any, any>(`/interviews/${id}/reverse`),
  submitReverse: (id: number, text: string) =>
    client.post<any, any>(`/interviews/${id}/reverse`, { text }, { timeout: 120000 }),
  skipReverse: (id: number) => client.post<any, any>(`/interviews/${id}/reverse/skip`),
  abortInterview: (id: number) => client.post(`/interviews/${id}/abort`),
  getReport: (id: number) => client.get<any, InterviewReportData>(`/interviews/${id}/report`),
  // 结构化题库组卷：配比查询 / 组卷预览 / 题库统计
  getPaperRatio: (params: { mode: string; total_questions: number }) =>
    client.get<any, { mode: string; ratio: Record<string, number>; allocated: Record<string, number>; bank_available: number; bank_ready: boolean }>('/interviews/paper-ratio', { params }),
  previewPaper: (data: any) => client.post<any, PaperPreview>('/interviews/paper-preview', data),
  getBankStats: () => client.get<any, { total: number; by_type: Record<string, number>; by_category: Record<string, number>; ready: boolean }>('/interviews/bank-stats'),
  // 面试历史对比（同岗位逐维趋势）与薄弱题清单
  getHistoryComparison: (params?: { job_id?: number; include_retrain?: boolean }) =>
    client.get<any, HistoryComparison>('/interviews/history-comparison', { params }),
  getWeakQuestions: (params?: { threshold?: number; limit?: number }) =>
    client.get<any, WeakQuestionsResult>('/interviews/weak-questions', { params }),
}

export const enterpriseApi = {
  getDashboard: () => client.get('/enterprise/dashboard'),
  listJobs: (params?: any) => client.get<any, JobItem[]>('/enterprise/jobs', { params }),
  createJob: (data: any) => client.post<any, JobItem>('/enterprise/jobs', data),
  getJob: (id: number) => client.get<any, JobItem>(`/enterprise/jobs/${id}`),
  updateJob: (id: number, data: any) => client.put<any, JobItem>(`/enterprise/jobs/${id}`, data),
  deleteJob: (id: number) => client.delete(`/enterprise/jobs/${id}`),
  submitJob: (id: number) => client.post(`/enterprise/jobs/${id}/submit`),
  pauseJob: (id: number) => client.post(`/enterprise/jobs/${id}/pause`),
  resumeJob: (id: number) => client.post(`/enterprise/jobs/${id}/resume`),
  closeJob: (id: number) => client.post(`/enterprise/jobs/${id}/close`),
  copyJob: (id: number) => client.post(`/enterprise/jobs/${id}/copy`),
  parseJD: (jd_text: string) => client.post('/enterprise/jobs/parse-jd', { jd_text }),
  listCandidates: (params?: any) => client.get<any, ApplicationItem[]>('/enterprise/candidates', { params }),
  getCandidate: (id: number) => client.get(`/enterprise/candidates/${id}`),
  advanceCandidate: (id: number, data: any) => client.post(`/enterprise/candidates/${id}/advance`, data),
  assignCandidate: (id: number, user_id: number) => client.post(`/enterprise/candidates/${id}/assign`, null, { params: { user_id } }),
  addTag: (id: number, tag: string) => client.post(`/enterprise/candidates/${id}/tags`, null, { params: { tag } }),
  getPipeline: (job_id?: number) => client.get('/enterprise/pipeline', { params: { job_id } }),
  listInterviews: () => client.get('/enterprise/interviews'),
  sendInvitation: (data: any) => client.post('/enterprise/interview-invitations', data),
  submitEvaluation: (id: number, data: any) => client.post(`/enterprise/interviews/${id}/evaluation`, data),
  listTalentPool: () => client.get('/enterprise/talent-pool'),
  addToTalentPool: (id: number) => client.post(`/enterprise/talent-pool/${id}`),
  removeFromTalentPool: (id: number) => client.delete(`/enterprise/talent-pool/${id}`),
  getAnalytics: (params?: any) => client.get('/enterprise/analytics', { params }),
  listMembers: () => client.get('/enterprise/members'),
  inviteMember: (data: any) => client.post('/enterprise/members', data),
  updateMember: (id: number, data: any) => client.patch(`/enterprise/members/${id}`, null, { params: data }),
  removeMember: (id: number) => client.delete(`/enterprise/members/${id}`),
  getSettings: () => client.get('/enterprise/settings'),
  updateSettings: (data: any) => client.patch('/enterprise/settings', data),
  submitVerification: (data: any) => client.post('/enterprise/verification', data),
  getLogs: () => client.get('/enterprise/operation-logs'),
}

export const adminApi = {
  login: (data: any) => client.post('/admin/auth/login', data),
  getDashboard: () => client.get('/admin/dashboard'),
  listUsers: (params?: any) => client.get('/admin/users', { params }),
  toggleUserStatus: (id: number) => client.post(`/admin/users/${id}/toggle-status`),
  listCompanies: () => client.get('/admin/companies'),
  toggleCompanyStatus: (id: number) => client.post(`/admin/companies/${id}/toggle-status`),
  listVerifications: () => client.get('/admin/verifications'),
  approveVerification: (id: number, opinion?: string) => client.post(`/admin/verifications/${id}/approve`, null, { params: { opinion } }),
  rejectVerification: (id: number, opinion: string) => client.post(`/admin/verifications/${id}/reject`, null, { params: { opinion } }),
  listJobsReview: () => client.get('/admin/jobs/review'),
  approveJob: (id: number) => client.post(`/admin/jobs/${id}/approve`),
  rejectJob: (id: number, reason: string) => client.post(`/admin/jobs/${id}/reject`, null, { params: { reason } }),
  takedownJob: (id: number, reason: string) => client.post(`/admin/jobs/${id}/take-down`, null, { params: { reason } }),
  listComplaints: () => client.get('/admin/complaints'),
  resolveComplaint: (id: number, resolution: string) => client.post(`/admin/complaints/${id}/resolve`, null, { params: { resolution } }),
  getContent: () => client.get('/admin/content'),
  updateContent: (data: any) => client.patch('/admin/content', data),
  getAIProviders: () => client.get('/admin/ai/providers'),
  updateAIProvider: (data: any) => client.patch('/admin/ai/providers', data),
  getAILogs: () => client.get('/admin/ai/logs'),
  getAuditLogs: () => client.get('/admin/audit-logs'),
  // 结构化题库管理（M08）
  listQuestionBank: (params?: any) => client.get<any, QuestionBankListResult>('/admin/question-bank', { params }),
  createQuestion: (data: any) => client.post('/admin/question-bank', data),
  updateQuestion: (id: number, data: any) => client.put(`/admin/question-bank/${id}`, data),
  toggleQuestion: (id: number, enabled: boolean) => client.patch(`/admin/question-bank/${id}/toggle`, { enabled }),
}

export const privateFileApi = {
  async preview(fileUrl: string): Promise<string> {
    if (!/^\/uploads\/[a-zA-Z0-9_.-]+$/.test(fileUrl)) throw new Error('文件地址无效')
    const blob = await client.get<any, Blob>(fileUrl, { baseURL: '', responseType: 'blob' })
    return URL.createObjectURL(blob)
  },
}
