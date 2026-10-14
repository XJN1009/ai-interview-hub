export interface UserInfo {
  id: number
  email: string
  phone?: string
  account_type: 'PERSONAL' | 'ENTERPRISE' | 'ADMIN'
  status: string
  roles: string[]
  name: string
  avatar_url?: string
  company_id?: number
  company_name?: string
  profile_type?: string
  target_job_title?: string
}

export interface JobItem {
  official_apply_url?: string | null
  id: number
  company_id: number
  company_name: string
  company_logo?: string
  department_name?: string
  title: string
  category: string
  city: string
  salary_min: number
  salary_max: number
  education: string
  experience: string
  type: string
  headcount: number
  description: string
  duties: string
  requirements: string
  bonus?: string
  skills_required: string
  skills: { skill_name: string; level: string; required: boolean }[]
  competencies: { competency_name: string; weight: number; required_score: number }[]
  status: string
  reject_reason?: string
  is_favorited?: boolean
  match_score?: number
  applications_count?: number
  created_at: string
}

export interface ResumeItem {
  id: number
  user_id: number
  name: string
  is_default: boolean
  file_url?: string
  file_name?: string
  target_job_title: string
  completeness: number
  created_at: string
  educations: { school: string; major: string; degree: string; start_date: string; end_date: string }[]
  projects: { name: string; role: string; description: string; technologies: string; start_date: string; end_date: string }[]
  work_experiences: { company: string; title: string; description: string; start_date: string; end_date: string }[]
  skills: { skill_name: string; level: string; evidence?: string }[]
}

export interface ResumeDocumentItem {
  id: number
  file_url: string
  file_name: string
  created_at: string
  updated_at: string
}

export interface ApplicationItem {
  id: number
  user_id: number
  candidate_name: string
  candidate_avatar?: string
  candidate_school?: string
  candidate_education?: string
  candidate_major?: string
  job_id: number
  job_title: string
  company_id: number
  company_name: string
  resume_id: number
  status: string
  match_score: number | null
  reject_reason?: string
  withdraw_reason?: string
  tags: string[]
  has_interview_invitation?: boolean
  invitation_status?: string
  created_at: string
  updated_at: string
  status_history: { id: number; from_status?: string; to_status: string; note?: string; created_at: string }[]
}

export interface InterviewQuestionView {
  id: number
  seq: number
  stage: string
  question_type: string          // PROFESSIONAL / GENERAL / STRESS
  skill_name: string
  text: string
  difficulty: string
  hints?: string
  time_limit_sec: number
  source: string                 // QUESTION_BANK / AI_GENERATED
  reference_points: string[]     // 参考答案要点（仅复盘阶段非空）
  reveal_reference: boolean
  user_answer?: string
  evaluation?: any
}

export interface InterviewSession {
  id: number
  user_id: number
  company_id?: number
  job_id?: number
  job_title: string
  type: string
  mode: string
  difficulty: string
  status: string
  current_question_seq: number
  total_questions: number
  duration_minutes: number
  questions: InterviewQuestionView[]
  current_question?: InterviewQuestionView
}

export interface QuestionBankItem {
  id: number
  job_category: string
  question_type: string
  skill_name: string
  stage: string
  difficulty: string
  text: string
  reference_points: string[]
  hints?: string | null
  time_limit_sec: number
  source: string
  batch?: string | null
  review_status: string
  enabled: boolean
  usage_count: number
  created_at: string
  updated_at: string
}

export interface QuestionBankListResult {
  items: QuestionBankItem[]
  total: number
  page: number
  page_size: number
  categories: string[]
  batches: string[]
  stats: {
    total: number
    enabled: number
    pending: number
    rejected: number
    by_type: Record<string, number>
    by_category: Record<string, number>
    by_batch: Record<string, { total: number; APPROVED: number; PENDING: number; REJECTED: number }>
  }
}

export interface HistoryComparison {
  job_id: number | null
  job_title: string | null
  sessions: {
    seq?: number
    interview_id: number
    score: number
    mode?: string
    difficulty?: string
    total_questions?: number
    created_at: string
  }[]
  dimension_trends: Record<string, { series: number[]; delta: number; improved: boolean }>
  total_delta?: number
  session_count?: number
  ready: boolean
  include_retrain?: boolean
  message?: string
}

export interface WeakQuestionItem {
  bank_id: number
  skill_name: string
  question_type: string
  difficulty: string
  text: string
  attempts: number
  latest_score: number
  best_score: number
  worst_score: number
  last_interview_id: number
}

export interface WeakQuestionsResult {
  threshold: number
  total_attempted_bank_questions: number
  weak_count: number
  items: WeakQuestionItem[]
  retrain_bank_ids: number[]
}

export interface PaperPreview {
  mode: string
  total_questions: number
  ratio: Record<string, number>
  allocated: Record<string, number>
  from_bank: number
  missing_for_ai: Record<string, number>
  matched_category: string
  job_skills: string[]
  bank_available: number
  questions: {
    seq: number
    question_type: string
    skill_name: string
    stage: string
    difficulty: string
    text: string
    time_limit_sec: number
    source: string
  }[]
}

export interface InterviewReportData {
  provenance?: { source?: string; answer_sources?: string[]; model?: string; fallback_reason?: string }
  learning_state?: string
  id: number
  interview_id: number
  job_title?: string
  interview_type?: string
  duration_minutes?: number
  total_score: number
  performance_level: string
  dimension_scores: Record<string, number>
  strengths: string[]
  weaknesses: string[]
  suggestions: string[]
  summary: string
  status: string
  created_at: string
  questions_analysis: {
    provenance?: { source?: string; model?: string; fallback_reason?: string }
    seq: number
    question: string
    answer: string
    score: number
    question_type?: string
    stage?: string
    skill_name?: string
    difficulty?: string
    source?: string
    reference_points?: string[]
    duration_sec?: number
    time_limit_sec?: number
    overtime?: boolean
    overtime_sec?: number
    is_empty?: boolean
    is_skipped?: boolean
    evidence: string[]
    weaknesses: string[]
    missing_knowledge: string[]
    suggestions: string[]
  }[]
  time_analysis?: {
    items: {
      seq: number
      skill_name: string
      duration_sec: number
      time_limit_sec: number
      usage_ratio: number
      overtime: boolean
      overtime_sec: number
    }[]
    total_answered: number
    total_time_sec: number
    avg_time_sec: number
    max_time_sec: number
    min_time_sec: number
    overtime_count: number
    overtime_rate: number
    avg_usage_ratio: number
    overtime_skills: string[]
  } | null
  /** 反问环节汇总（v2 新增）；只登记候选人的提问，旧报告无此字段时为 null */
  reverse_summary?: {
    questions: {
      seq: number
      candidate_text: string
    }[]
    question_count: number
    skipped: boolean
    comment: string
  } | null
}

export interface ExternalApplicationItem {
  id: number
  job_id: number
  job_title: string
  company_name: string
  official_apply_url: string
  channel: 'OFFICIAL_WEBSITE'
  status_source: 'USER_REPORTED'
  status: string
  note?: string
  created_at: string
  updated_at: string
  status_history: { to_status: string; note: string; created_at: string }[]
}
