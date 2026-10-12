<template>
  <div class="interview-room-page">
    <StateContainer :loading="loading" :error="error" @retry="loadSession">
      <div v-if="session" class="session-wrapper">
        <!-- Top Status Bar -->
        <header class="room-top-bar">
          <div class="top-left">
            <span class="room-job-badge">{{ session.job_title }}</span>
            <span class="room-seq-indicator">
              {{ isOpening ? '开场环节' : (isReverse ? '反问环节' : `第 ${session.current_question_seq} / ${session.total_questions} 题`) }}
            </span>
            <span
              v-if="!isOpening && !isReverse"
              :class="['room-qtype-pill', qtypeClass(currentQuestion?.question_type)]"
            >
              {{ qtypeLabel(currentQuestion?.question_type) }}
            </span>
          </div>

          <div class="top-right-meta">
            <div
              v-if="!isOpening && !isReverse"
              :class="['room-timer-pill', 'question-timer', { 'timer-overtime': questionOverTime }]"
            >
              <el-icon><Stopwatch /></el-icon>
              <span>本题用时 <strong>{{ formatTime(questionElapsed) }}</strong> / {{ questionLimitText }}</span>
            </div>
            <div v-if="!isOpening" class="room-timer-pill">
              <el-icon><Clock /></el-icon>
              <span>剩余 <strong>{{ formatTime(remainingSeconds) }}</strong></span>
            </div>
            <el-button type="danger" plain size="small" class="abort-btn" @click="endDialogVisible = true">
              结束面试
            </el-button>
          </div>
        </header>

        <!-- 开场环节：固定引导语模板（不调 LLM），点击开始后进入逐题作答 -->
        <main v-if="isOpening" class="room-main-stage opening-stage">
          <section class="ai-interviewer-card opening-card">
            <div class="ai-avatar-section">
              <div class="ai-avatar-circle">
                <el-icon :size="30" color="#2563EB"><UserFilled /></el-icon>
              </div>
              <div class="ai-meta-info">
                <span class="ai-chief-title">智面仓AI面试官</span>
                <span class="ai-status-indicator">
                  <span class="status-dot-blink"></span>
                  面试即将开始
                </span>
              </div>
            </div>

            <div class="opening-speech">
              <h1 class="question-headline">
                你好，欢迎参加「{{ session.job_title }}」模拟面试
              </h1>
              <p class="opening-line">
                我是本次的 AI 面试官。接下来会围绕岗位要求与你简历中的经历提问，共
                <strong>{{ session.total_questions }}</strong>
                题，预计
                <strong>{{ session.duration_minutes }}</strong>
                分钟。
              </p>
              <p class="opening-line">
                建议按「背景 — 做法 — 结果」的结构回答；不确定的问题也请说出你的思路，而不是直接空着。
              </p>
              <p class="opening-line">
                过程中你可以随时暂停、跳过或结束面试；结束时若已有作答，会生成一份能力诊断报告。
              </p>
            </div>

            <ul class="opening-tips">
              <li>闭卷作答：面试中不展示参考答案，复盘阶段才能逐题对照要点</li>
              <li>每题有建议限时，超时会少量扣分但不会归零；主动跳过按 0 分但不产生严厉评语</li>
              <li>
                支持语音口述：
                {{ speechSupported ? '当前浏览器可用，可边想边说' : '当前浏览器不支持，建议改用 Chrome / Edge' }}
              </li>
            </ul>

            <div class="opening-actions">
              <el-button type="primary" size="large" :loading="starting" @click="startFromOpening">
                准备好了，开始面试
              </el-button>
            </div>
          </section>
        </main>

        <!-- 反问环节：逐题作答结束后的候选人提问（不计入总分） -->
        <main v-else-if="isReverse" class="room-main-stage opening-stage">
          <section class="ai-interviewer-card opening-card">
            <div class="ai-avatar-section">
              <div class="ai-avatar-circle">
                <el-icon :size="30" color="#2563EB"><UserFilled /></el-icon>
              </div>
              <div class="ai-meta-info">
                <span class="ai-chief-title">智面仓AI面试官</span>
                <span class="ai-status-indicator">
                  <span class="status-dot-blink"></span>
                  反问环节
                </span>
              </div>
            </div>

            <div class="opening-speech">
              <h1 class="question-headline">我的问题问完了，你有什么想问我的吗？</h1>
              <p class="opening-line">
                可以问团队、业务、协作方式或成长路径；薪酬福利这类问题我们放到 HR 环节详谈。
                你最多可以问
                <strong>{{ reverseState?.max_count || 3 }}</strong>
                条，也可以直接交卷。
              </p>
            </div>

            <div v-if="reverseState?.questions?.length" class="reverse-thread">
              <div v-for="item in reverseState.questions" :key="item.seq" class="reverse-item">
                <div class="reverse-ask">
                  <span class="reverse-role">你</span>
                  <span class="reverse-text">{{ item.candidate_text }}</span>
                </div>
                <div class="reverse-reply">
                  <span class="reverse-role reply">面试官</span>
                  <span class="reverse-text">{{ item.ai_response }}</span>
                </div>
                <div v-if="item.evaluation?.comment" class="reverse-comment">
                  {{ item.evaluation.comment }}
                </div>
              </div>
            </div>

            <div class="answer-box">
              <div class="answer-box-header">
                <span class="answer-box-title">你想问的问题</span>
                <span class="word-counter">{{ reverseText.length }} 字</span>
              </div>
              <el-input
                v-model="reverseText"
                type="textarea"
                :rows="3"
                :disabled="!reverseState || reverseState.remaining <= 0"
                placeholder="例如：团队目前最看重候选人的哪项能力？最近半年遇到的最大挑战是什么？"
                class="room-textarea"
              />
              <div class="submit-action-row">
                <el-button
                  size="large"
                  class="room-skip-btn"
                  :disabled="reverseSubmitting"
                  @click="skipReverse"
                >
                  跳过反问，直接交卷
                </el-button>
                <el-button
                  type="primary"
                  size="large"
                  class="room-submit-btn"
                  :loading="reverseSubmitting"
                  :disabled="!reverseState || reverseState.remaining <= 0 || !reverseText.trim()"
                  @click="submitReverseQuestion"
                >
                  {{ reverseState && reverseState.remaining > 0 ? `提交提问（还可问 ${reverseState.remaining} 条）` : '已达提问上限，请交卷' }}
                </el-button>
              </div>
            </div>
          </section>
        </main>

        <!-- Main Immersive Stage (AI Left, Candidate Right) -->
        <main v-else class="room-main-stage">
          <!-- Left: AI Interviewer & Highlighted Question -->
          <section class="ai-interviewer-card">
            <div class="ai-avatar-section">
              <div class="ai-avatar-circle">
                <el-icon :size="30" color="#2563EB"><UserFilled /></el-icon>
              </div>
              <div class="ai-meta-info">
                <span class="ai-chief-title">智面仓AI面试官</span>
                <span class="ai-status-indicator">
                  <span class="status-dot-blink"></span>
                  {{ currentStage }}
                </span>
              </div>
            </div>

            <!-- Current Big Question Text -->
            <div class="current-question-container">
              <div class="q-skill-badge-row">
                <span class="q-skill-tag">{{ currentQuestion?.skill_name || '综合能力' }}</span>
                <span class="q-source-tag">
                  {{ currentQuestion?.source === 'QUESTION_BANK' ? '题库' : 'AI 出题' }}
                </span>
              </div>
              <h1 class="question-headline">
                {{ currentQuestion?.text || '正在加载题目...' }}
              </h1>
            </div>

            <!-- Question Sub-note / Hint -->
            <div v-if="currentQuestion?.hints" class="question-hint-bar">
              <el-icon color="#3B82F6"><InfoFilled /></el-icon>
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
                  摄像头已开启
                </div>
              </div>
              <div v-else class="video-stream-fallback">
                <div class="fallback-cam-icon">
                  <el-icon :size="36" color="#94A3B8"><VideoCamera /></el-icon>
                </div>
                <span class="fallback-cam-text">摄像头已关闭，纯文本作答模式</span>
              </div>
            </div>

            <!-- Answer Transcription / Editor Box -->
            <div class="answer-box">
              <div class="answer-box-header">
                <span class="answer-box-title">你的回答</span>
                <span class="word-counter">{{ answerText.length }} 字</span>
              </div>

              <el-input
                v-model="answerText"
                type="textarea"
                :rows="6"
                placeholder="清晰阐述你的解决思路、技术选型取舍与项目实操指标..."
                class="room-textarea"
              />

              <!-- Quick Template Demo Helper -->
              <div class="demo-template-row">
                <button type="button" class="template-btn" @click="insertTemplate">
                  填入演示答案
                </button>
              </div>

              <!-- 答题草稿提示 -->
              <div v-if="draftRestored" class="draft-notice-bar">
                <el-icon><InfoFilled /></el-icon>
                <span>已恢复上次未提交的草稿</span>
                <el-button link size="small" @click="clearDraft">清除草稿</el-button>
              </div>

              <!-- Submit Answer Action -->
              <div class="submit-action-row">
                <el-button
                  :disabled="evaluating"
                  size="large"
                  class="room-skip-btn"
                  @click="handleSkipQuestion"
                >
                  跳过本题 →
                </el-button>
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

        <!-- Bottom Hardware & Control Bar（开场/反问环节隐藏：这两个环节无需作答） -->
        <footer v-if="!isOpening && !isReverse" class="room-bottom-controls">
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
            <span v-if="transcribing" class="asr-phase-indicator">{{ asrPhaseText }}</span>

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
        </footer>
      </div>
    </StateContainer>

    <!-- 结束面试：交卷出报告 / 取消不生成报告 -->
    <el-dialog v-model="endDialogVisible" title="结束本次模拟面试" width="420px" align-center>
      <p class="end-dialog-tip">
        你已作答 <strong>{{ session?.answered_count || 0 }}</strong> / {{ session?.total_questions || 0 }} 题。
      </p>
      <ul class="end-dialog-options">
        <li><strong>交卷并生成报告</strong>：按已答内容结算，生成能力诊断报告（需至少作答 1 题）。</li>
        <li><strong>取消面试</strong>：直接中止本次会话，不生成报告，已答部分仅保留在记录中。</li>
      </ul>
      <template #footer>
        <div class="end-dialog-footer">
          <el-button @click="endDialogVisible = false">继续作答</el-button>
          <el-button type="warning" plain @click="doAbort">取消面试</el-button>
          <el-button type="danger" :disabled="!session?.answered_count" @click="doFinish">交卷并生成报告</el-button>
        </div>
      </template>
    </el-dialog>
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
  RefreshRight, InfoFilled, Stopwatch
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const error = ref(false)
const session = ref<any>(null)
const currentQuestion = ref<any>(null)
const answerText = ref('')
const evaluating = ref(false)
const starting = ref(false)

// 开场环节：新会话创建后 phase=OPENING，等用户点击「开始面试」再由后端推进为 QA
const isOpening = computed(() =>
  session.value?.phase === 'OPENING' && ['READY', 'CREATED'].includes(session.value?.status)
)

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

/* ====== 草稿保护：自动保存/恢复答题文本 ====== */
const draftRestored = ref(false)
let _draftTimer: any = null

const getDraftKey = () => {
  const ivId = Number(route.params.id)
  const seq = session.value?.current_question_seq || 1
  return `zhimeicang_draft_${ivId}_q${seq}`
}

const saveDraft = () => {
  const text = answerText.value.trim()
  if (text) {
    localStorage.setItem(getDraftKey(), text)
  } else {
    localStorage.removeItem(getDraftKey())
  }
}

const restoreDraftIfAny = () => {
  const key = getDraftKey()
  const saved = localStorage.getItem(key)
  if (saved) {
    answerText.value = saved
    draftRestored.value = true
    localStorage.removeItem(key)  // 恢复后立即删除，避免重复恢复
  } else {
    draftRestored.value = false
  }
}

const clearDraft = () => {
  draftRestored.value = false
  answerText.value = ''
}

// 每 2 秒自动保存一次草稿
watch(answerText, () => {
  if (_draftTimer) clearTimeout(_draftTimer)
  _draftTimer = setTimeout(saveDraft, 2000)
})

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
// 本场转写是否收到过识别结果（用于停止时"未识别到语音"的诚实提示）
let heardSpeech = false
// 分级诊断：是否已采集音频 / 是否检测到人声 / no-speech 次数
let audioCaptured = false
let speechDetected = false
let noSpeechCount = 0
// 识别生命周期阶段（常驻显示在按钮旁，不依赖 toast）：listening=等待采音 audio=已开麦 speech=检测到人声 result=已出结果
const asrPhase = ref<'listening' | 'audio' | 'speech' | 'result'>('listening')
// 本地音量计（WebAudio 直采，不经网络）：用于区分"麦克风没声音"与"识别服务无响应"
const asrLevel = ref(0)
let asrPeakLevel = 0
let micMeterStream: MediaStream | null = null
let micMeterCtx: AudioContext | null = null
let micMeterTimer: any = null

const startMicLevelMeter = () => {
  asrLevel.value = 0
  asrPeakLevel = 0
  navigator.mediaDevices?.getUserMedia({ audio: true }).then((stream) => {
    micMeterStream = stream
    const Ctx = window.AudioContext || (window as any).webkitAudioContext
    micMeterCtx = new Ctx()
    const src = micMeterCtx.createMediaStreamSource(stream)
    const analyser = micMeterCtx.createAnalyser()
    analyser.fftSize = 512
    src.connect(analyser)
    const data = new Uint8Array(analyser.frequencyBinCount)
    micMeterTimer = setInterval(() => {
      analyser.getByteTimeDomainData(data)
      let sum = 0
      for (let i = 0; i < data.length; i++) {
        const v = (data[i] - 128) / 128
        sum += v * v
      }
      const rms = Math.sqrt(sum / data.length)
      asrLevel.value = Math.min(100, Math.round(rms * 300))
      asrPeakLevel = Math.max(asrPeakLevel, asrLevel.value)
    }, 120)
  }).catch(() => { /* 音量计失败不影响转写本身 */ })
}

const stopMicLevelMeter = () => {
  if (micMeterTimer) { clearInterval(micMeterTimer); micMeterTimer = null }
  if (micMeterStream) { micMeterStream.getTracks().forEach(t => t.stop()); micMeterStream = null }
  if (micMeterCtx) { micMeterCtx.close().catch(() => {}); micMeterCtx = null }
  asrLevel.value = 0
}

const asrPhaseText = computed(() => {
  const base = {
    listening: '识别：等待音频…',
    audio: '识别：麦克风已开启，等待人声…',
    speech: '识别：已检测到人声，等待返回…',
    result: '识别：正常出字中'
  }[asrPhase.value]
  return asrPhase.value === 'audio' ? `${base}（本地音量 ${asrLevel.value}%）` : base
})

const startTranscription = () => {
  const Ctor = getRecognitionCtor()
  if (!Ctor) {
    speechSupported.value = false
    ElMessage.warning('当前浏览器不支持语音转写，请使用 Chrome/Edge，或直接键盘输入')
    return
  }
  if (transcribing.value) return
  committedText = answerText.value ? answerText.value.trimEnd() + ' ' : ''
  heardSpeech = false
  audioCaptured = false
  speechDetected = false
  noSpeechCount = 0
  asrPhase.value = 'listening'
  recognition = new Ctor()
  recognition.lang = 'zh-CN'
  recognition.continuous = true
  recognition.interimResults = true
  recognition.onresult = (e: any) => {
    heardSpeech = true
    asrPhase.value = 'result'
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
    } else if (e?.error === 'network') {
      // Chrome 的识别需联网访问 Google 语音服务；国内网络下必失败
      ElMessage.error('语音识别服务连接失败：Chrome 需能访问 Google 服务，建议改用 Edge 浏览器')
      transcribing.value = false
    } else if (e?.error === 'no-speech') {
      // 麦克风持续无声会反复触发 no-speech → onend 自动重启；连续两次仍无内容则提示
      noSpeechCount++
      if (noSpeechCount === 2 && !heardSpeech) {
        ElMessage.warning('麦克风未采到声音：请对着麦克风清晰说话，或检查系统默认输入设备')
      }
    } else if (e?.error !== 'aborted') {
      ElMessage.warning(`语音转写异常：${e?.error || 'unknown'}`)
    }
  }
  recognition.onend = () => {
    // 用户仍在录音态时自动重启，避免浏览器静默结束导致中断
    if (transcribing.value) {
      try { recognition?.start() } catch { /* 已启动 */ }
    }
  }
  // 分级事件探针：audiostart=已拿到麦克风流；speechstart=检测到人声
  try {
    (recognition as any).addEventListener?.('audiostart', () => {
      audioCaptured = true
      if (asrPhase.value === 'listening') asrPhase.value = 'audio'
    })
    (recognition as any).addEventListener?.('speechstart', () => {
      speechDetected = true
      if (asrPhase.value === 'audio' || asrPhase.value === 'listening') asrPhase.value = 'speech'
    })
  } catch { /* 部分浏览器不支持这些事件 */ }
  try {
    recognition.start()
    transcribing.value = true
    startMicLevelMeter()
    ElMessage.success('已开始语音转写，请口述你的回答')
    // 8 秒无任何识别结果：用本地音量峰值裁决卡点（麦克风无声 vs 服务无响应）
    const iv = setInterval(() => {
      if (!transcribing.value || heardSpeech) { clearInterval(iv); return }
      if (asrPeakLevel >= 12) {
        ElMessage.warning(`本地已采到声音（峰值 ${asrPeakLevel}%）但识别服务无返回：网络无法访问浏览器语音服务，建议检查网络/代理或改用键盘输入`)
      } else if (audioCaptured) {
        ElMessage.warning('麦克风已开启但本地音量过低：请靠近麦克风、提高输入音量，或检查系统默认录音设备')
      } else {
        ElMessage.warning('未采集到任何音频：请检查 Windows「设置→隐私→麦克风」全局开关与「允许桌面应用访问」，以及系统默认录音设备')
      }
      clearInterval(iv)
    }, 8000)
  } catch (e) {
    ElMessage.error('语音转写启动失败，请检查麦克风权限')
    transcribing.value = false
  }
}

const stopTranscription = () => {
  if (!transcribing.value) return
  transcribing.value = false
  stopMicLevelMeter()
  // 保留当前已显示文本（含未定稿的临时结果）作为定稿前缀，防止停止时丢字
  committedText = answerText.value ? answerText.value.trimEnd() + ' ' : ''
  const rec = recognition
  recognition = null
  if (!rec) { ElMessage.info('已停止语音转写'); return }
  let finalized = false
  const settle = () => {
    if (finalized) return
    finalized = true
    // 以最终识别结果整体定稿，覆盖"停止前一刻"的临时文本
    let finalText = ''
    try {
      const results = (rec as any).results
      for (let i = 0; results && i < results.length; i++) {
        if (results[i].isFinal) finalText += results[i][0].transcript
      }
    } catch { /* 部分浏览器 stop 后不可读 */ }
    if (finalText) answerText.value = (committedText + finalText).trimStart()
    if (!heardSpeech && !answerText.value.trim()) {
      ElMessage.warning('未识别到语音内容，请确认已允许麦克风权限并靠近麦克风重试')
    } else {
      ElMessage.info('已停止语音转写')
    }
    try { rec.abort() } catch { /* ignore */ }
  }
  rec.onend = settle
  try { rec.stop() } catch { settle() }
  // 兜底：某些实现 stop 后不再触发 onend
  setTimeout(settle, 1500)
}

const toggleTranscription = () => {
  transcribing.value ? stopTranscription() : startTranscription()
}

// 完整复位语音转写状态：中止识别、清空已定稿前缀，避免上一题口述内容串到下一题
const resetTranscription = () => {
  if (transcribing.value) {
    transcribing.value = false
    stopMicLevelMeter()
    try { recognition?.abort() } catch { /* ignore */ }
    recognition = null
  }
  committedText = ''
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

const handlePauseResume = async () => {
  try {
    const id = Number(route.params.id)
    if (isPaused.value) await interviewApi.resumeInterview(id)
    else await interviewApi.pauseInterview(id)
    isPaused.value = !isPaused.value
    if (isPaused.value && transcribing.value) stopTranscription()
    ElMessage.info(isPaused.value ? '面试已暂停' : '已恢复答题')
  } catch { /* API 已显示错误 */ }
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
    let res: any = await interviewApi.getInterview(interviewId)
    if (res.status === 'COMPLETED') { router.replace(`/personal/interviews/${interviewId}/report`); return }
    // 开场环节不自动开始：留给用户读完引导语后点击「开始面试」，
    // 后端会在 start 时把 phase 从 OPENING 推进为 QA。
    const openingPending = res.phase === 'OPENING' && ['READY', 'CREATED'].includes(res.status)
    if (!openingPending && ['READY', 'CREATED'].includes(res.status)) {
      await interviewApi.startInterview(interviewId)
      res = await interviewApi.getInterview(interviewId)
    }
    const data = res?.data || res
    isPaused.value = data.status === 'PAUSED'
    session.value = data
    // 反问环节中途刷新：补拉反问状态，保证问答记录不丢
    if (data.phase === 'REVERSE') {
      try {
        const rs: any = await interviewApi.getReverse(interviewId)
        reverseState.value = rs?.data || rs
      } catch (err) {
        // 静默失败：不影响主流程，用户仍可跳过反问
      }
    }
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
    // 开场阶段不计时、不初始化摄像头（此时入口卡片未渲染），避免无谓的计时与权限请求
    if (!openingPending) {
      startTimer()
      initCamera()
      restoreDraftIfAny()
    }
  } catch (err: any) {
    error.value = true
  } finally {
    loading.value = false
  }
}

// 开场引导结束：开始面试并重新加载会话（此后 phase=QA，进入逐题作答）
const startFromOpening = async () => {
  const interviewId = Number(route.params.id)
  starting.value = true
  try {
    await interviewApi.startInterview(interviewId)
    await loadSession()
  } catch (err: any) {
    ElMessage.error('开始面试失败，请稍后重试')
  } finally {
    starting.value = false
  }
}

// ===== 反问环节（逐题作答结束后进入；问答不计入总分）=====
const reverseState = ref<any>(null)
const reverseText = ref('')
const reverseSubmitting = ref(false)
const isReverse = computed(() => session.value?.phase === 'REVERSE')

// 逐题作答结束：拉取反问状态并切换界面（整场计时继续，反问不设单题倒计时）
const enterReverse = async () => {
  const interviewId = Number(route.params.id)
  resetTranscription()
  await loadSession()
  ElMessage.success('逐题作答已结束，进入反问环节')
  if (!reverseState.value) {
    ElMessage.warning('反问环节加载失败，可点击「跳过反问」直接交卷')
  }
}

const submitReverseQuestion = async () => {
  const text = reverseText.value.trim()
  if (!text) {
    ElMessage.warning('请先输入你想问的问题')
    return
  }
  const interviewId = Number(route.params.id)
  reverseSubmitting.value = true
  try {
    const res: any = await interviewApi.submitReverse(interviewId, text)
    reverseState.value = res?.data || res
    reverseText.value = ''
    ElMessage.success('已记录你的提问，面试官已回答')
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '提问失败，请稍后重试')
  } finally {
    reverseSubmitting.value = false
  }
}

// 跳过反问并直接交卷
const skipReverse = async () => {
  const interviewId = Number(route.params.id)
  reverseSubmitting.value = true
  try {
    await interviewApi.skipReverse(interviewId)
  } catch (err) {
    // 已跳过或状态已变化时不阻塞交卷
  } finally {
    reverseSubmitting.value = false
  }
  await doFinish()
}

const handleSkipQuestion = () => {
  if (!currentQuestion.value?.id) return
  ElMessageBox.confirm(
    '确定跳过本题吗？本题将按 0 分记录，但不会产生严厉评语（视为主动放弃）。',
    '跳过本题',
    { confirmButtonText: '确定跳过', cancelButtonText: '继续作答', type: 'warning' }
  ).then(async () => {
    evaluating.value = true
    resetTranscription()
    const interviewId = Number(route.params.id)
    const spentSec = questionElapsed.value
    try {
      const res: any = await interviewApi.answerQuestion(interviewId, {
        question_id: currentQuestion.value!.id,
        text: '',
        duration_sec: spentSec,
        skipped: true
      })
      const data = res?.data || res
      ElMessage.info('已跳过本题，继续下一题')

      if (data?.finished_qa || data?.is_finished) {
        await enterReverse()
      } else {
        if (typeof data?.total_questions === 'number') {
          session.value.total_questions = data.total_questions
        }
        if (typeof data?.remaining_seconds === 'number') {
          remainingSeconds.value = data.remaining_seconds
        }
        session.value.current_question_seq = data.next_question?.seq ?? (session.value.current_question_seq + 1)
        currentQuestion.value = data.next_question || null
        answerText.value = ''
        draftRestored.value = false
        localStorage.removeItem(getDraftKey())
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
      ElMessage.error(err.message || '跳过失败')
    } finally {
      evaluating.value = false
    }
  }).catch(() => {})
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

  // 提交前冻结语音转写，防止上一题口述结果在下一题继续写入
  resetTranscription()

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

    // 逐题作答结束 → 进入反问环节（v2 起不再自动结算）
    if (data?.finished_qa || data?.is_finished) {
      await enterReverse()
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
      draftRestored.value = false
      localStorage.removeItem(getDraftKey())
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

// 结束面试对话框（交卷 / 取消二合一）
const endDialogVisible = ref(false)

const doFinish = async () => {
  if (!session.value?.answered_count) return
  endDialogVisible.value = false
  const interviewId = Number(route.params.id)
  await interviewApi.finishInterview(interviewId)
  router.push(`/interviews/${interviewId}/report`)
}

// 取消面试：中止会话、不生成报告，随时可退出（含一题未答的场景）
const doAbort = async () => {
  endDialogVisible.value = false
  await interviewApi.abortInterview(Number(route.params.id))
  router.push('/personal/interviews')
}

// 快捷键 Esc：打开"结束面试"对话框（交卷/取消在其中选择）
const handleGlobalKeydown = (e: KeyboardEvent) => {
  if (e.key !== 'Escape' || evaluating.value) return
  // 已有弹窗打开时，Esc 归弹窗自身处理（关闭弹窗），不重复触发
  if (document.querySelector('.el-message-box, .el-overlay')) return
  endDialogVisible.value = true
}

// 整场时间归零：自动交卷生成报告（当前题如有未提交内容一并交上）；一题未答则自动中止
let autoFinished = false
watch(remainingSeconds, async (val) => {
  if (val > 0 || autoFinished || !session.value) return
  autoFinished = true
  const interviewId = Number(route.params.id)
  try {
    if (answerText.value.trim() && currentQuestion.value?.id) {
      await interviewApi.answerQuestion(interviewId, {
        question_id: currentQuestion.value.id,
        text: answerText.value,
        duration_sec: questionElapsed.value
      }).catch(() => {})
    }
    if (!session.value.answered_count) {
      // 无任何作答：交卷必 409，自动走中止归档
      ElMessage.warning('整场面试时间已用完且无作答记录，本次面试已自动中止')
      await interviewApi.abortInterview(interviewId).catch(() => {})
      router.push('/personal/interviews')
      return
    }
    ElMessage.warning('整场面试时间已用完，正在自动交卷生成报告...')
    await interviewApi.finishInterview(interviewId)
    router.push(`/interviews/${interviewId}/report`)
  } catch (e) {
    ElMessage.error('自动交卷失败，请手动点击"结束面试"')
    autoFinished = false
  }
})

onMounted(() => {
  loadSession()
  window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
  if (timer) clearInterval(timer)
  transcribing.value = false
  stopMicLevelMeter()
  try { recognition?.abort() } catch { /* ignore */ }
  recognition = null
  if (ttsSupported.value) window.speechSynthesis.cancel()
  if (localStream) {
    localStream.getTracks().forEach(t => t.stop())
  }
})
</script>

<style scoped>
/* 简约浅色主题：与全站设计系统统一，纵向铺满可用区域 */
.interview-room-page {
  height: 100%;
  background: #F6F7F9;
  color: #1F2937;
  display: flex;
  flex-direction: column;
}

/* StateContainer 包裹层透传高度，使内容区铺满 */
.interview-room-page :deep(.state-container),
.interview-room-page :deep(.state-content) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.session-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 14px;
  flex: 1;
  min-height: 0;
}

/* Top Status Bar */
.room-top-bar {
  min-height: 56px;
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 10px;
  padding: 8px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.top-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.room-job-badge {
  font-size: 14px;
  font-weight: 700;
  color: #111827;
}

.room-seq-indicator {
  font-size: 13px;
  color: #2563EB;
  background: #EFF6FF;
  padding: 3px 10px;
  border-radius: 6px;
}

/* 题型胶囊（专业/通用/压力） */
.room-qtype-pill {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 9999px;
}

.qtype-pro {
  color: #1D4ED8;
  background: #DBEAFE;
}

.qtype-gen {
  color: #047857;
  background: #D1FAE5;
}

.qtype-str {
  color: #B91C1C;
  background: #FEE2E2;
}

.top-right-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.room-timer-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #6B7280;
  background: #F3F4F6;
  padding: 4px 12px;
  border-radius: 6px;
}
.room-timer-pill strong {
  color: #111827;
  font-weight: 700;
}

/* 逐题计时超时高亮 */
.question-timer {
  transition: all 0.2s;
}

.timer-overtime {
  color: #B91C1C;
  background: #FEE2E2;
}
.timer-overtime strong {
  color: #B91C1C;
}

.abort-btn {
  border-radius: 6px !important;
}

/* Main Stage: 2 Columns */
.room-main-stage {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 16px;
  flex: 1;
}

.ai-interviewer-card, .candidate-stage-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* Left AI Column */
.ai-avatar-section {
  display: flex;
  align-items: center;
  gap: 14px;
}

.ai-avatar-circle {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: #EFF6FF;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ai-meta-info {
  display: flex;
  flex-direction: column;
}

.ai-chief-title {
  font-size: 15px;
  font-weight: 700;
  color: #111827;
}

.ai-status-indicator {
  font-size: 12px;
  color: #6B7280;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 3px;
}

.status-dot-blink {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10B981;
}

.current-question-container {
  margin: 24px 0 20px;
  flex: 1;
}

.q-skill-badge-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.q-skill-tag {
  font-size: 12px;
  font-weight: 600;
  color: #2563EB;
  background: #EFF6FF;
  padding: 3px 10px;
  border-radius: 4px;
}

.q-source-tag {
  font-size: 11px;
  color: #6B7280;
  background: #F3F4F6;
  padding: 2px 8px;
  border-radius: 4px;
}

.question-headline {
  font-size: 21px;
  font-weight: 600;
  color: #111827;
  line-height: 1.55;
}

.question-hint-bar {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 12.5px;
  color: #6B7280;
  background: #F9FAFB;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid #F3F4F6;
}
.question-hint-bar .el-icon {
  margin-top: 2px;
  flex-shrink: 0;
}

/* Right Candidate Stage */
.candidate-stage-card {
  justify-content: flex-start;
}

.camera-monitor-box {
  width: 100%;
  height: 200px;
  background: #F3F4F6;
  border: 1px solid #E5E7EB;
  border-radius: 10px;
  overflow: hidden;
  position: relative;
  flex-shrink: 0;
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
  transform: scaleX(-1); /* 水平翻转，消除镜像效果 */
}

.video-status-overlay {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(17, 24, 39, 0.65);
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 11px;
  color: #F9FAFB;
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
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: #E5E7EB;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fallback-cam-text {
  font-size: 12px;
  color: #9CA3AF;
}

.answer-box {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.answer-box-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.answer-box-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.word-counter {
  font-size: 12px;
  color: #9CA3AF;
}

.room-textarea {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 160px;
}

.room-textarea :deep(.el-textarea),
.room-textarea :deep(.el-textarea__inner) {
  height: 100% !important;
}

.room-textarea :deep(.el-textarea__inner) {
  background-color: #FFFFFF !important;
  border-color: #E5E7EB !important;
  color: #1F2937 !important;
  font-size: 14px !important;
  line-height: 1.6 !important;
  box-shadow: none !important;
  resize: none;
}

.room-textarea :deep(.el-textarea__inner:focus) {
  border-color: #2563EB !important;
}

.demo-template-row {
  display: flex;
  align-items: center;
  margin-top: 8px;
}

.template-btn {
  background: none;
  border: none;
  color: #2563EB;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}
.template-btn:hover {
  text-decoration: underline;
}

.submit-action-row {
  margin-top: 14px;
  display: flex;
  gap: 10px;
}

.room-skip-btn {
  background: #FFFFFF !important;
  border: 1px solid #D1D5DB !important;
  color: #6B7280 !important;
  font-size: 14px !important;
  border-radius: 8px !important;
  flex-shrink: 0;
}
.room-skip-btn:hover {
  border-color: #9CA3AF !important;
  color: #374151 !important;
}

.room-submit-btn {
  flex: 1;
  height: 44px;
  font-size: 15px !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  background: #2563EB !important;
  border-color: #2563EB !important;
}

.draft-notice-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  border-radius: 6px;
  padding: 8px 14px;
  font-size: 12px;
  color: #1D4ED8;
  margin-top: 10px;
}

/* Bottom Controls */
.room-bottom-controls {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 10px;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.controls-pill-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.hardware-ctrl-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  color: #4B5563;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.hardware-ctrl-btn:hover {
  background: #F3F4F6;
  border-color: #D1D5DB;
  color: #111827;
}

.hardware-ctrl-btn.active {
  background: #EFF6FF;
  border-color: #2563EB;
  color: #1D4ED8;
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

.asr-phase-indicator {
  font-size: 12px;
  color: #6B7280;
  background: #F3F4F6;
  border: 1px dashed #D1D5DB;
  border-radius: 6px;
  padding: 6px 12px;
}

@keyframes rec-blink {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.55); }
  70% { box-shadow: 0 0 0 7px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

/* 结束面试对话框 */
.end-dialog-tip {
  margin: 0 0 10px;
  font-size: 14px;
  color: #374151;
}
.end-dialog-tip strong {
  color: #2563EB;
}
.end-dialog-options {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: #6B7280;
  line-height: 1.9;
}
.end-dialog-options strong {
  color: #111827;
}
.end-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
}

@media (max-width: 1024px) {
  .room-main-stage {
    grid-template-columns: 1fr;
  }
}

/* ===== 开场环节（固定引导语模板）===== */
.opening-stage {
  grid-template-columns: 1fr;
  align-items: start;
}

.opening-card {
  gap: 18px;
}

.opening-speech {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.opening-speech .question-headline {
  margin: 0;
}

.opening-line {
  margin: 0;
  color: #475569;
  font-size: 15px;
  line-height: 1.8;
}

.opening-line strong {
  color: #1e293b;
}

.opening-tips {
  margin: 0;
  padding: 14px 18px 14px 34px;
  list-style: disc;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.9;
}

.opening-actions {
  display: flex;
  justify-content: flex-start;
}

/* ===== 反问环节 ===== */
.reverse-thread {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 320px;
  overflow-y: auto;
  padding-right: 4px;
}

.reverse-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
}

.reverse-ask,
.reverse-reply {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.reverse-role {
  flex: 0 0 auto;
  padding: 2px 8px;
  border-radius: 6px;
  background: #eff6ff;
  color: #2563eb;
  font-size: 12px;
  line-height: 20px;
}

.reverse-role.reply {
  background: #f1f5f9;
  color: #475569;
}

.reverse-text {
  font-size: 14px;
  line-height: 1.8;
  color: #334155;
}

.reverse-comment {
  padding-left: 10px;
  border-left: 2px solid #cbd5e1;
  color: #64748b;
  font-size: 13px;
  line-height: 1.7;
}
</style>
