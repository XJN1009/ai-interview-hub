<template>
  <div class="interview-room-page">
    <StateContainer :loading="loading" :error="error" @retry="loadSession">
      <div v-if="session" class="session-wrapper">
        <!-- Top Status Bar (Appendix A.7 & Mockup 07) -->
        <header class="room-top-bar">
          <div class="top-left">
            <span class="room-job-badge">{{ session.job_title }}</span>
            <span class="room-seq-indicator">第 {{ session.current_question_seq }} / {{ session.total_questions }} 题</span>
            <span class="room-stage-pill">{{ currentStage }}</span>
            <span :class="['room-qtype-pill', qtypeClass(currentQuestion?.question_type)]">
              {{ qtypeLabel(currentQuestion?.question_type) }}
            </span>
          </div>

          <div class="top-center-progress">
            <el-progress
              :percentage="Math.round((session.current_question_seq / session.total_questions) * 100)"
              :stroke-width="6"
              color="#3B82F6"
              :show-text="false"
              class="custom-room-progress"
            />
          </div>

          <div class="top-right-meta">
            <div :class="['room-timer-pill', 'question-timer', { 'timer-overtime': questionOverTime }]">
              <el-icon><Stopwatch /></el-icon>
              <span>本题用时 <strong>{{ formatTime(questionElapsed) }}</strong> / {{ questionLimitText }}</span>
            </div>
            <div class="room-timer-pill">
              <el-icon><Clock /></el-icon>
              <span>剩余时间 <strong>{{ formatTime(remainingSeconds) }}</strong></span>
            </div>
            <el-button type="danger" plain size="small" class="abort-btn" @click="handleConfirmFinish">
              结束面试
            </el-button>
          </div>
        </header>

        <!-- Main Immersive Stage (AI Left, Candidate Right) -->
        <main class="room-main-stage">
          <!-- Left: AI Interviewer & Highlighted Question -->
          <section class="ai-interviewer-card">
            <!-- AI Avatar & Pulsing Voice Ring -->
            <div class="ai-avatar-section">
              <div class="ai-avatar-circle">
                <div class="sound-wave-ring pulse-1"></div>
                <div class="sound-wave-ring pulse-2"></div>
                <div class="ai-portrait-inner">
                  <el-icon :size="42" color="#60A5FA"><UserFilled /></el-icon>
                </div>
              </div>
              <div class="ai-meta-info">
                <span class="ai-chief-title">智面舱 AI 首席面试官</span>
                <span class="ai-status-indicator">
                  <span class="status-dot-blink"></span>
                  正在提问与倾听作答
                </span>
              </div>
            </div>

            <!-- Current Big Question Text -->
            <div class="current-question-container">
              <div class="q-skill-badge-row">
                <span class="q-skill-tag">考察技能：{{ currentQuestion?.skill_name || '综合技术能力' }}</span>
                <span class="q-diff-tag">{{ currentQuestion?.difficulty || 'MEDIUM' }}</span>
                <span class="q-source-tag">
                  {{ currentQuestion?.source === 'QUESTION_BANK' ? '题库精选' : 'AI 实时出题' }}
                </span>
              </div>
              <h1 class="question-headline">
                {{ currentQuestion?.text || '正在加载题目...' }}
              </h1>
            </div>

            <!-- Question Sub-note / Hint -->
            <div v-if="currentQuestion?.hints" class="question-hint-bar">
              <el-icon color="#93C5FD"><InfoFilled /></el-icon>
              <span>{{ currentQuestion.hints }}</span>
            </div>
          </section>

          <!-- Right: Candidate Camera Feed & Answer Text Input -->
          <section class="candidate-stage-card">
            <!-- Candidate Camera Video Preview -->
            <div class="camera-monitor-box">
              <div v-if="cameraEnabled" class="video-stream-active">
                <video ref="videoRef" autoplay muted playsinline class="candidate-video-elem"></video>
                <div class="video-status-overlay">
                  <span class="video-status-dot"></span>
                  候选人音视频通道正常
                </div>
              </div>
              <div v-else class="video-stream-fallback">
                <div class="fallback-cam-icon">
                  <el-icon :size="36" color="#94A3B8"><VideoCamera /></el-icon>
                </div>
                <span class="fallback-cam-text">视频摄像头已关闭，已转为纯文本沉浸模式</span>
              </div>
            </div>

            <!-- Answer Transcription / Editor Box -->
            <div class="answer-box">
              <div class="answer-box-header">
                <span class="answer-box-title">你的回答 (支持直接语音转写或键盘输入)：</span>
                <span class="word-counter">{{ answerText.length }} 字</span>
              </div>

              <el-input
                v-model="answerText"
                type="textarea"
                :rows="5"
                placeholder="请在此清晰阐述你的解决思路、底层技术选型取舍与项目实操指标..."
                class="room-textarea"
              />

              <!-- Quick Template Demo Helper -->
              <div class="demo-template-row">
                <span class="template-label">💡 演示快捷填入：</span>
                <button type="button" class="template-btn" @click="insertTemplate">
                  【填入标准高并发 Redis 架构回答】
                </button>
              </div>

              <!-- Submit Answer Action -->
              <div class="submit-action-row">
                <el-button
                  type="primary"
                  size="large"
                  class="room-submit-btn"
                  :loading="evaluating"
                  @click="submitCurrentAnswer"
                >
                  {{ session.current_question_seq >= session.total_questions ? '提交本题并生成复盘报告' : '提交当前回答 → 下一题' }}
                </el-button>
              </div>
            </div>
          </section>
        </main>

        <!-- Bottom Hardware & Control Bar (Appendix A.7) -->
        <footer class="room-bottom-controls">
          <div class="controls-pill-group">
            <button
              type="button"
              :class="['hardware-ctrl-btn', { active: transcribing, disabled: !speechSupported }]"
              :title="speechSupported
                ? (transcribing ? '点击停止语音转写' : '点击开始语音转写（浏览器原生识别）')
                : '当前浏览器不支持语音转写，请使用 Chrome/Edge'"
              @click="toggleTranscription"
            >
              <el-icon :size="18"><Microphone /></el-icon>
              <span v-if="transcribing" class="rec-dot"></span>
              <span>{{ speechSupported ? (transcribing ? '停止口述' : '语音口述') : '不支持语音' }}</span>
            </button>

            <button
              type="button"
              :class="['hardware-ctrl-btn', { active: cameraEnabled }]"
              :title="cameraEnabled ? '摄像头已开启' : '摄像头已关闭'"
              @click="toggleCamera"
            >
              <el-icon :size="18"><VideoCamera /></el-icon>
              <span>{{ cameraEnabled ? '摄像头开' : '摄像头关' }}</span>
            </button>

            <button
              type="button"
              class="hardware-ctrl-btn"
              @click="handlePauseResume"
            >
              <el-icon :size="18"><VideoPause v-if="!isPaused" /><VideoPlay v-else /></el-icon>
              <span>{{ isPaused ? '恢复面试' : '暂停答题' }}</span>
            </button>

            <button
              type="button"
              :class="['hardware-ctrl-btn', { active: speaking, disabled: !ttsSupported }]"
              :title="ttsSupported ? (speaking ? '点击停止朗读' : '朗读本题题目') : '当前浏览器不支持语音朗读'"
              @click="handleReplayQuestion"
            >
              <el-icon :size="18"><RefreshRight /></el-icon>
              <span>{{ speaking ? '停止朗读' : '重听题目' }}</span>
            </button>
          </div>

          <!-- Drawer Toggle Button for Live Assistant (Default Folded) -->
          <div class="assistant-drawer-toggle">
            <el-button
              size="small"
              class="drawer-btn"
              @click="showAssist = !showAssist"
            >
              <el-icon><Cpu /></el-icon>
              <span>{{ showAssist ? '收起实时助手' : '展开实时助手' }}</span>
            </el-button>
          </div>
        </footer>

        <!-- Foldable Real-time Assistant Drawer -->
        <transition name="drawer-slide">
          <aside v-if="showAssist" class="live-assist-sidebar">
            <div class="assist-drawer-header">
              <span class="drawer-title">
                <el-icon color="#3B82F6"><Cpu /></el-icon>
                AI 实时表现辅助分析 (仅作参考)
              </span>
              <el-button link @click="showAssist = false">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>

            <div class="assist-drawer-body">
              <div class="assist-metric-item">
                <span class="am-label">当前实时语速</span>
                <span class="am-val text-green">158 字/分钟 (节奏适中)</span>
              </div>
              <div class="assist-metric-item">
                <span class="am-label">逻辑结构识别</span>
                <span class="am-val text-blue">总分总 · 条理层次分明</span>
              </div>
              <div class="assist-metric-item">
                <span class="am-label">技术关键词命中</span>
                <span class="am-val text-emerald">Redisson, 看门狗, 延迟双删</span>
              </div>
              <div class="assist-metric-item">
                <span class="am-label">实时建议提醒</span>
                <span class="am-val text-amber">建议结合实际生产压测 QPS 补充佐证</span>
              </div>
            </div>
          </aside>
        </transition>
      </div>
    </StateContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { interviewApi } from '@/api'
import StateContainer from '@/components/StateContainer.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Clock, UserFilled, VideoCamera, Microphone, VideoPause, VideoPlay,
  RefreshRight, Cpu, Close, InfoFilled, Stopwatch
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const error = ref(false)
const session = ref<any>(null)
const currentQuestion = ref<any>(null)
const answerText = ref('')
const evaluating = ref(false)

const remainingSeconds = ref(1800)
const isPaused = ref(false)
let timer: any = null

/* ---------- 逐题计时（用于限时提示与真实作答用时上报） ---------- */
const questionElapsed = ref(0)
const questionLimit = computed(() => currentQuestion.value?.time_limit_sec || 180)
const questionOverTime = computed(() => questionElapsed.value > questionLimit.value)
const questionLimitText = computed(() => formatTime(questionLimit.value))

const qtypeLabel = (t?: string) =>
  ({ PROFESSIONAL: '专业题', GENERAL: '通用题', STRESS: '压力题' }[t || ''] || '综合题')
const qtypeClass = (t?: string) =>
  ({ PROFESSIONAL: 'qtype-pro', GENERAL: 'qtype-gen', STRESS: 'qtype-str' }[t || ''] || 'qtype-gen')

const resetQuestionTimer = () => {
  questionElapsed.value = 0
}

const cameraEnabled = ref(true)
const videoRef = ref<HTMLVideoElement | null>(null)
let localStream: MediaStream | null = null

/* ---------- 语音转写（浏览器原生 Web Speech API，零依赖零上传） ---------- */
type SpeechRecognitionLike = {
  lang: string
  continuous: boolean
  interimResults: boolean
  start: () => void
  stop: () => void
  abort: () => void
  onresult: ((e: any) => void) | null
  onerror: ((e: any) => void) | null
  onend: (() => void) | null
}
const getRecognitionCtor = (): (new () => SpeechRecognitionLike) | null => {
  const w = window as any
  return w.SpeechRecognition || w.webkitSpeechRecognition || null
}
const speechSupported = ref(!!getRecognitionCtor())
const transcribing = ref(false)
const ttsSupported = ref(typeof window !== 'undefined' && 'speechSynthesis' in window)
const speaking = ref(false)
let recognition: SpeechRecognitionLike | null = null
// 已定稿的转写文本前缀：识别结果整体替换，避免重复追加
let committedText = ''

const startTranscription = () => {
  const Ctor = getRecognitionCtor()
  if (!Ctor) {
    speechSupported.value = false
    ElMessage.warning('当前浏览器不支持语音转写，请使用 Chrome/Edge，或直接键盘输入')
    return
  }
  if (transcribing.value) return
  committedText = answerText.value ? answerText.value.trimEnd() + ' ' : ''
  recognition = new Ctor()
  recognition.lang = 'zh-CN'
  recognition.continuous = true
  recognition.interimResults = true
  recognition.onresult = (e: any) => {
    let finalText = ''
    let interimText = ''
    for (let i = 0; i < e.results.length; i++) {
      const r = e.results[i]
      if (r.isFinal) finalText += r[0].transcript
      else interimText += r[0].transcript
    }
    answerText.value = (committedText + finalText + interimText).trimStart()
  }
  recognition.onerror = (e: any) => {
    if (e?.error === 'not-allowed' || e?.error === 'service-not-allowed') {
      ElMessage.error('麦克风权限被拒绝，无法语音作答')
      transcribing.value = false
    } else if (e?.error !== 'aborted' && e?.error !== 'no-speech') {
      ElMessage.warning(`语音转写异常：${e?.error || 'unknown'}`)
    }
  }
  recognition.onend = () => {
    // 用户仍在录音态时自动重启，避免浏览器静默结束导致中断
    if (transcribing.value) {
      try { recognition?.start() } catch { /* 已启动 */ }
    }
  }
  try {
    recognition.start()
    transcribing.value = true
    ElMessage.success('已开始语音转写，请口述你的回答')
  } catch (e) {
    ElMessage.error('语音转写启动失败，请检查麦克风权限')
    transcribing.value = false
  }
}

const stopTranscription = () => {
  if (!transcribing.value) return
  transcribing.value = false
  committedText = answerText.value ? answerText.value.trimEnd() + ' ' : ''
  try { recognition?.stop() } catch { /* ignore */ }
  recognition = null
  ElMessage.info('已停止语音转写')
}

const toggleTranscription = () => {
  transcribing.value ? stopTranscription() : startTranscription()
}

/* ---------- 题目朗读（speechSynthesis，替代原"假重播"按钮） ---------- */
const handleReplayQuestion = () => {
  const text = currentQuestion.value?.text
  if (!text) {
    ElMessage.warning('题目尚未加载完成')
    return
  }
  if (!ttsSupported.value) {
    ElMessage.warning('当前浏览器不支持语音朗读，请查看屏幕上的题目文本')
    return
  }
  const synth = window.speechSynthesis
  if (speaking.value) {
    synth.cancel()
    speaking.value = false
    return
  }
  const utter = new SpeechSynthesisUtterance(text)
  utter.lang = 'zh-CN'
  utter.rate = 1.05
  utter.onend = () => { speaking.value = false }
  utter.onerror = () => { speaking.value = false }
  speaking.value = true
  synth.speak(utter)
}

const showAssist = ref(false) // Default folded per spec

const currentStage = computed(() => {
  return currentQuestion.value?.stage || '综合考察阶段'
})

const formatTime = (secs: number) => {
  const m = Math.floor(secs / 60).toString().padStart(2, '0')
  const s = (secs % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

const startTimer = () => {
  if (timer) clearInterval(timer)
  timer = setInterval(() => {
    if (isPaused.value) return
    if (remainingSeconds.value > 0) remainingSeconds.value--
    questionElapsed.value++
  }, 1000)
}

const initCamera = async () => {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    cameraEnabled.value = false
    return
  }
  try {
    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
    if (videoRef.value) {
      videoRef.value.srcObject = localStream
    }
    cameraEnabled.value = true
  } catch (err) {
    cameraEnabled.value = false
  }
}

const toggleCamera = () => {
  cameraEnabled.value = !cameraEnabled.value
  if (!cameraEnabled.value && localStream) {
    localStream.getVideoTracks().forEach(t => t.stop())
  } else if (cameraEnabled.value) {
    initCamera()
  }
}

const handlePauseResume = () => {
  isPaused.value = !isPaused.value
  if (isPaused.value && transcribing.value) stopTranscription()
  ElMessage.info(isPaused.value ? '答题计时已暂停' : '已恢复答题')
}

const insertTemplate = () => {
  answerText.value =
    "在我们的高并发业务场景中，核心热点数据全部由 Redis 承载。对于缓存击穿，我们主要采用 Redisson 互斥锁机制，仅让获取到锁的主线程去查库重建缓存，并利用 Watchdog 机制进行安全锁续期；对于双写一致性，采用了延迟双删结合 Canal 监听 MySQL Binlog 异步补偿的策略，将并发脏读窗口压低至毫秒级，压测 QPS 提升至 4200+。"
  ElMessage.info('已填入标准实战回答模板')
}

const loadSession = async () => {
  loading.value = true
  error.value = false
  const interviewId = Number(route.params.id)
  try {
    const res: any = await interviewApi.getInterview(interviewId)
    const data = res?.data || res
    session.value = data
    // 整场剩余时间以服务端 started_at 口径为准（刷新页面不会重置）
    if (typeof data?.remaining_seconds === 'number') {
      remainingSeconds.value = data.remaining_seconds
    } else {
      remainingSeconds.value = Math.max(
        60,
        (data?.duration_minutes || (data?.total_questions || 5) * 5) * 60
      )
    }
    if (data?.current_question) {
      currentQuestion.value = data.current_question
    } else if (data?.questions?.length) {
      // 卷面已预生成，取当前序号对应的题目
      const seq = data.current_question_seq || 1
      currentQuestion.value =
        data.questions.find((q: any) => q.seq === seq) || data.questions[0]
    } else {
      currentQuestion.value = null
      ElMessage.warning('本次面试暂无题目，请返回重新创建面试')
    }
    resetQuestionTimer()
    startTimer()
    initCamera()
  } catch (err: any) {
    error.value = true
  } finally {
    loading.value = false
  }
}

const submitCurrentAnswer = async () => {
  if (!answerText.value.trim()) {
    ElMessage.warning('回答内容不能为空，请作答')
    return
  }
  if (!currentQuestion.value?.id) {
    ElMessage.error('当前题目缺失，请刷新页面重试')
    return
  }

  evaluating.value = true
  const interviewId = Number(route.params.id)
  // 上报本题真实作答用时（秒）
  const spentSec = questionElapsed.value
  try {
    const res: any = await interviewApi.answerQuestion(interviewId, {
      question_id: currentQuestion.value.id,
      text: answerText.value,
      duration_sec: spentSec
    })

    const data = res?.data || res
    if (data?.is_empty) {
      ElMessage.warning('本题未提交有效作答，已按 0 分记录')
    } else if (data?.overtime) {
      ElMessage.warning(`本题超时 ${data.overtime_sec} 秒，已轻扣分（${data.raw_score} → ${data.total_score}）`)
    } else {
      ElMessage.success('回答提交成功')
    }

    // 服务端判定完成（含追问加题后的真实总题数）
    if (data?.is_finished) {
      router.push(`/interviews/${interviewId}/report`)
    } else {
      // 同步追问加题与剩余时间（服务端口径）
      if (typeof data?.total_questions === 'number') {
        session.value.total_questions = data.total_questions
      }
      if (typeof data?.remaining_seconds === 'number') {
        remainingSeconds.value = data.remaining_seconds
      }
      session.value.current_question_seq = data.next_question?.seq ?? (session.value.current_question_seq + 1)
      // 下一题由后端卷面下发（题库预生成 / 自适应追问 / AI 补足）
      currentQuestion.value = data.next_question || null
      answerText.value = ''
      resetQuestionTimer()
      if (data?.is_followup) {
        ElMessage.info('AI 面试官根据你的回答，追加了一道针对性问题')
      }
      if (!currentQuestion.value) {
        ElMessage.warning('未获取到下一题，正在重新加载考卷')
        await loadSession()
      }
    }
  } catch (err: any) {
    ElMessage.error(err.message || '提交回答失败')
  } finally {
    evaluating.value = false
  }
}

const handleConfirmFinish = () => {
  ElMessageBox.confirm('确定要提前结束本次模拟面试并生成答题报告吗？', '提示', {
    confirmButtonText: '确定交卷',
    cancelButtonText: '继续作答',
    type: 'warning'
  }).then(async () => {
    const interviewId = Number(route.params.id)
    await interviewApi.finishInterview(interviewId)
    router.push(`/interviews/${interviewId}/report`)
  }).catch(() => {})
}

// 整场时间归零：自动交卷生成报告（当前题如有未提交内容一并交上）
let autoFinished = false
watch(remainingSeconds, async (val) => {
  if (val > 0 || autoFinished || !session.value) return
  autoFinished = true
  ElMessage.warning('整场面试时间已用完，正在自动交卷生成报告...')
  try {
    if (answerText.value.trim() && currentQuestion.value?.id) {
      await interviewApi.answerQuestion(Number(route.params.id), {
        question_id: currentQuestion.value.id,
        text: answerText.value,
        duration_sec: questionElapsed.value
      }).catch(() => {})
    }
    await interviewApi.finishInterview(Number(route.params.id))
    router.push(`/interviews/${Number(route.params.id)}/report`)
  } catch (e) {
    ElMessage.error('自动交卷失败，请手动点击"结束面试"')
    autoFinished = false
  }
})

onMounted(() => {
  loadSession()
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  transcribing.value = false
  try { recognition?.abort() } catch { /* ignore */ }
  recognition = null
  if (ttsSupported.value) window.speechSynthesis.cancel()
  if (localStream) {
    localStream.getTracks().forEach(t => t.stop())
  }
})
</script>

<style scoped>
/* Full Immersive Dark Stage per Mockup 07 */
.interview-room-page {
  min-height: 100vh;
  background: #0B0F17;
  color: #F3F4F6;
  padding: 20px 24px 32px;
  display: flex;
  flex-direction: column;
}

.session-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

/* Top Status Bar */
.room-top-bar {
  height: 60px;
  background: #111827;
  border: 1px solid #1F2937;
  border-radius: 12px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.top-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.room-job-badge {
  font-size: 14px;
  font-weight: 700;
  color: #FFFFFF;
}

.room-seq-indicator {
  font-size: 13px;
  color: #93C5FD;
  background: rgba(59, 130, 246, 0.15);
  padding: 3px 10px;
  border-radius: 6px;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.room-stage-pill {
  font-size: 12px;
  color: #9CA3AF;
}

/* 题型胶囊（专业/通用/压力） */
.room-qtype-pill {
  font-size: 11.5px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 9999px;
  border: 1px solid transparent;
}

.qtype-pro {
  color: #BFDBFE;
  background: rgba(37, 99, 235, 0.22);
  border-color: rgba(59, 130, 246, 0.45);
}

.qtype-gen {
  color: #A7F3D0;
  background: rgba(16, 185, 129, 0.18);
  border-color: rgba(52, 211, 153, 0.4);
}

.qtype-str {
  color: #FECACA;
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(248, 113, 113, 0.45);
}

/* 逐题计时超时高亮 */
.question-timer {
  transition: all 0.2s;
}

.timer-overtime {
  color: #FCA5A5;
  background: rgba(239, 68, 68, 0.18);
  border: 1px solid rgba(248, 113, 113, 0.45);
}

.top-center-progress {
  width: 280px;
}

.custom-room-progress :deep(.el-progress-bar__outer) {
  background-color: #1F2937 !important;
}

.top-right-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}

.room-timer-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #9CA3AF;
  background: #1F2937;
  padding: 4px 12px;
  border-radius: 6px;
}
.room-timer-pill strong {
  color: #EF4444;
  font-weight: 700;
}

.abort-btn {
  border-radius: 6px !important;
}

/* Main Immersive Stage: 2 Columns */
.room-main-stage {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 20px;
  flex: 1;
}

.ai-interviewer-card, .candidate-stage-card {
  background: #111827;
  border: 1px solid #1F2937;
  border-radius: 16px;
  padding: 28px;
  display: flex;
  flex-direction: column;
}

/* Left AI Column */
.ai-avatar-section {
  display: flex;
  align-items: center;
  gap: 20px;
  padding-bottom: 24px;
  border-bottom: 1px solid #1F2937;
}

.ai-avatar-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #1E293B;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.sound-wave-ring {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  border: 2px solid #3B82F6;
  opacity: 0.5;
}

.pulse-1 {
  animation: pulse 2.4s infinite ease-out;
}
.pulse-2 {
  animation: pulse 2.4s infinite ease-out 1.2s;
}

@keyframes pulse {
  0% { transform: scale(0.92); opacity: 0.8; }
  100% { transform: scale(1.3); opacity: 0; }
}

.ai-portrait-inner {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1E3A8A 0%, #0F172A 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-meta-info {
  display: flex;
  flex-direction: column;
}

.ai-chief-title {
  font-size: 16px;
  font-weight: 700;
  color: #FFFFFF;
}

.ai-status-indicator {
  font-size: 12px;
  color: #10B981;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}

.status-dot-blink {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10B981;
  box-shadow: 0 0 8px #10B981;
}

.current-question-container {
  margin: 32px 0 24px;
  flex: 1;
}

.q-skill-badge-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.q-skill-tag {
  font-size: 12px;
  font-weight: 600;
  color: #60A5FA;
  background: rgba(59, 130, 246, 0.15);
  padding: 3px 10px;
  border-radius: 4px;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.q-diff-tag {
  font-size: 11px;
  color: #F59E0B;
  background: rgba(245, 158, 11, 0.15);
  padding: 2px 8px;
  border-radius: 4px;
}

.q-source-tag {
  font-size: 11px;
  color: #93C5FD;
  background: rgba(59, 130, 246, 0.12);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px dashed rgba(59, 130, 246, 0.35);
}

.question-headline {
  font-size: 24px;
  font-weight: 700;
  color: #FFFFFF;
  line-height: 1.45;
  letter-spacing: -0.015em;
}

.question-hint-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #94A3B8;
  background: #1E293B;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid #334155;
}

/* Right Candidate Stage */
.candidate-stage-card {
  justify-content: space-between;
}

.camera-monitor-box {
  width: 100%;
  height: 220px;
  background: #0F172A;
  border: 1px solid #1F2937;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}

.video-stream-active {
  width: 100%;
  height: 100%;
  position: relative;
}

.candidate-video-elem {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-status-overlay {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(4px);
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  color: #E2E8F0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.video-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10B981;
}

.video-stream-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.fallback-cam-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #1E293B;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fallback-cam-text {
  font-size: 12px;
  color: #64748B;
}

.answer-box {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
}

.answer-box-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.answer-box-title {
  font-size: 13px;
  color: #94A3B8;
}

.word-counter {
  font-size: 12px;
  color: #64748B;
}

.room-textarea :deep(.el-textarea__inner) {
  background-color: #0F172A !important;
  border-color: #334155 !important;
  color: #F8FAFC !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
}

.room-textarea :deep(.el-textarea__inner:focus) {
  border-color: #3B82F6 !important;
  box-shadow: 0 0 0 1px #3B82F6 inset !important;
}

.demo-template-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.template-label {
  font-size: 12px;
  color: #94A3B8;
}

.template-btn {
  background: none;
  border: none;
  color: #60A5FA;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
}

.submit-action-row {
  margin-top: 16px;
}

.room-submit-btn {
  width: 100%;
  height: 44px;
  font-size: 15px !important;
  font-weight: 700 !important;
  border-radius: 8px !important;
  background: #2563EB !important;
  border-color: #2563EB !important;
}

/* Bottom Hardware Controls */
.room-bottom-controls {
  height: 64px;
  background: #111827;
  border: 1px solid #1F2937;
  border-radius: 12px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.controls-pill-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.hardware-ctrl-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #1F2937;
  border: 1px solid #374151;
  color: #D1D5DB;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.hardware-ctrl-btn:hover {
  background: #374151;
  color: #FFFFFF;
}

.hardware-ctrl-btn.active {
  background: rgba(37, 99, 235, 0.2);
  border-color: #3B82F6;
  color: #60A5FA;
}

.hardware-ctrl-btn.disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.rec-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #EF4444;
  box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6);
  animation: rec-blink 1.2s infinite;
}

@keyframes rec-blink {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.55); }
  70% { box-shadow: 0 0 0 7px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

.assistant-drawer-toggle .drawer-btn {
  background: #1F2937 !important;
  border-color: #374151 !important;
  color: #9CA3AF !important;
}

/* Foldable Live Assistant Panel */
.live-assist-sidebar {
  position: fixed;
  right: 24px;
  top: 96px;
  width: 320px;
  background: #111827;
  border: 1px solid #374151;
  border-radius: 12px;
  box-shadow: 0 16px 32px rgba(0, 0, 0, 0.5);
  z-index: 100;
  overflow: hidden;
}

.assist-drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #1E293B;
  border-bottom: 1px solid #334155;
}

.drawer-title {
  font-size: 13px;
  font-weight: 700;
  color: #F8FAFC;
  display: flex;
  align-items: center;
  gap: 6px;
}

.assist-drawer-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.assist-metric-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: #0F172A;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #1E293B;
}

.am-label {
  font-size: 11px;
  color: #64748B;
}

.am-val {
  font-size: 12.5px;
  font-weight: 600;
}

.text-green { color: #10B981; }
.text-blue { color: #3B82F6; }
.text-emerald { color: #059669; }
.text-amber { color: #F59E0B; }

.drawer-slide-enter-active, .drawer-slide-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.drawer-slide-enter-from, .drawer-slide-leave-to {
  transform: translateX(20px);
  opacity: 0;
}

@media (max-width: 1024px) {
  .room-main-stage {
    grid-template-columns: 1fr;
  }
}
</style>
