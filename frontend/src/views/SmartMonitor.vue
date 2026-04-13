<template>
  <div class="smart-monitor">
    <my-card>
      <h2>智能监控服务</h2>
      <p class="subtitle">启动施工道路实时监测，查看处理画面与最新警告。</p>
      <form class="config-form" @submit.prevent>
        <label>
          视频源类型
          <select v-model="form.cap_type">
            <option value="file">本地视频</option>
            <option value="ip_camera">网络摄像头</option>
          </select>
        </label>

        <template v-if="form.cap_type === 'file'">
          <div class="local-videos-block">
            <span class="field-label">本地视频</span>
            <p class="field-hint">
             <code class="code-tag">videos</code> 目录下的视频
            </p>
            <videos-folder-picker
              api-base="/smart"
              :busy="startBusy"
              :active-cap-path="form.cap_path"
              @analyze="onAnalyzeLocalVideo"
            />
          </div>
        </template>

        <label v-else>
          网络摄像头地址
          <input v-model.trim="form.cap_path" type="text" placeholder="例如 rtsp://用户名:密码@IP:554/..." />
        </label>

        <label class="checkbox-row">
          <input v-model="form.enable_ai" type="checkbox" />
          启用 DeepSeek 推理
        </label>

        <div class="actions">
          <my-button v-if="form.cap_type === 'ip_camera'" type="button" @click="handleStart">启动智能监控</my-button>
          <my-button v-if="serviceId" type="button" @click="handleStop">停止服务</my-button>
        </div>
      </form>

      <p v-if="serviceId" class="status success">智能服务已启动</p>
      <p v-if="errorMessage" class="status error">{{ errorMessage }}</p>
    </my-card>

    <div v-if="serviceId" class="monitor-grid">
      <my-card>
        <h3>实时监控</h3>
        <div class="frame-grid">
          <div class="frame-panel">
            <div class="frame-heading">
              <span class="frame-title">现场</span>
              <span class="frame-note">原始视频</span>
            </div>
            <img v-if="frameUrls.row" :src="frameUrls.row" alt="原始帧" />
          </div>
          <div class="frame-panel">
            <div class="frame-heading">
              <span class="frame-title">识别</span>
              <span class="frame-note">实时分析</span>
            </div>
            <img v-if="frameUrls.processed" :src="frameUrls.processed" alt="处理帧" />
          </div>
        </div>
      </my-card>

      <my-card>
        <h3>最新告警</h3>
        <div v-if="liveStatus" class="monitor-live-status">
          <p
            v-for="(item, li) in liveStatus.rules_result?.alerts || []"
            :key="'live-' + li + (item.rule_id || '')"
            class="live-status-line"
          >
            {{ item.message }}
          </p>
        </div>
        <div v-if="alerts.length" class="alert-list alert-list-scroll">
          <article
            v-for="(alert, index) in alerts"
            :key="alertKey(alert, index)"
            class="alert-item"
          >
            <p class="alert-title">风险等级: {{ alert.rules_result?.risk_level || 'unknown' }}</p>
            <p
              v-for="(item, ai) in alert.rules_result?.alerts || []"
              :key="(alert.alert_seq ?? index) + '-' + ai + (item.rule_id || '')"
            >
              {{ item.message }}
            </p>
            <p v-if="alert.recorded_at" class="alert-time">告警时间：{{ alert.recorded_at }}</p>
          </article>
        </div>
        <p v-if="!alerts.length" class="alert-empty">当前暂无警告</p>
      </my-card>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, reactive, ref } from 'vue'
import MyButton from '@/components/MyButton.vue'
import MyCard from '@/components/MyCard.vue'
import VideosFolderPicker from '@/components/VideosFolderPicker.vue'
import {
  getSmartAlerts,
  getSmartProcessedFrame,
  getSmartRowFrame,
  releaseSmartService,
  startSmartService
} from '@/api/smart'
import { isLikelyJpegBlob } from '@/utils/blobImage'
import { uiErrorMessage } from '@/utils/uiError'

const form = reactive({
  cap_type: 'file',
  cap_path: '',
  enable_ai: false
})

const serviceId = ref(null)
const startBusy = ref(false)
const errorMessage = ref('')
const alerts = ref([])
/** 运行状态（心跳），与历史告警分离，不占用滚动列表 */
const liveStatus = ref(null)
const frameUrls = reactive({
  row: '',
  processed: ''
})

let frameRefreshTimer = null
let metaRefreshTimer = null
const defaultSrcPoints = [
  { x: 120, y: 420 },
  { x: 520, y: 420 },
  { x: 60, y: 760 },
  { x: 620, y: 760 }
]
const defaultDangerZones = [[[180, 300], [460, 300], [460, 620], [180, 620]]]

function revokeAllFrameUrls() {
  Object.keys(frameUrls).forEach((key) => {
    if (frameUrls[key]) {
      URL.revokeObjectURL(frameUrls[key])
      frameUrls[key] = ''
    }
  })
}

function setFrameUrl(key, blob) {
  if (frameUrls[key]) URL.revokeObjectURL(frameUrls[key])
  frameUrls[key] = URL.createObjectURL(blob)
}

/** 稳定 key：历史告警只追加，用服务端序号避免列表重排闪烁 */
function alertKey(alert, index) {
  if (alert?.alert_seq != null && alert.alert_seq !== '') {
    return `alert-${alert.alert_seq}`
  }
  return `${alert?.timestamp ?? 't'}-${index}`
}

async function refreshSmartFrames() {
  if (!serviceId.value) return

  try {
    const settled = await Promise.allSettled([
      getSmartRowFrame(serviceId.value),
      getSmartProcessedFrame(serviceId.value)
    ])
    const rowRes = settled[0]
    const procRes = settled[1]
    let anyFrameOk = false
    if (rowRes.status === 'fulfilled' && (await isLikelyJpegBlob(rowRes.value.data))) {
      setFrameUrl('row', rowRes.value.data)
      anyFrameOk = true
    }
    if (procRes.status === 'fulfilled' && (await isLikelyJpegBlob(procRes.value.data))) {
      setFrameUrl('processed', procRes.value.data)
      anyFrameOk = true
    }
    if (!anyFrameOk) {
      const error = rowRes.status === 'rejected' ? rowRes.reason : procRes.reason
      const serverError = error?.response?.data?.error
      const line =
        serverError && serverError !== 'No frame available' ? uiErrorMessage(serverError) : ''
      errorMessage.value = line
    }
  } catch (error) {
    const serverError = error?.response?.data?.error
    const line =
      serverError && serverError !== 'No frame available' ? uiErrorMessage(serverError) : ''
    errorMessage.value = line
  }
}

async function refreshSmartMeta() {
  if (!serviceId.value) return

  const settled = await Promise.allSettled([getSmartAlerts(serviceId.value, 50)])
  const [alertsRes] = settled

  if (alertsRes.status === 'fulfilled') {
    alerts.value = alertsRes.value.data.alerts || []
    liveStatus.value = alertsRes.value.data.live_status ?? null
  }

  const firstErr = settled.find((r) => r.status === 'rejected')
  if (firstErr && firstErr.status === 'rejected') {
    const serverError = firstErr.reason?.response?.data?.error
    const line =
      serverError && serverError !== 'No frame available' ? uiErrorMessage(serverError) : ''
    errorMessage.value = line
  } else {
    errorMessage.value = ''
  }
}

async function onAnalyzeLocalVideo({ capPath }) {
  errorMessage.value = ''
  startBusy.value = true
  try {
    if (serviceId.value) {
      await handleStop()
    }
    form.cap_path = capPath
    await handleStart()
  } finally {
    startBusy.value = false
  }
}

async function handleStart() {
  errorMessage.value = ''

  if (form.cap_type === 'ip_camera' && !form.cap_path.trim()) {
    errorMessage.value = '请填写网络摄像头地址'
    return
  }

  try {
    const response = await startSmartService({
      src_points: defaultSrcPoints,
      cap_type: form.cap_type,
      cap_path: form.cap_path,
      danger_zones: defaultDangerZones,
      enable_ai: form.enable_ai
    })

    serviceId.value = response.data.service_id
    if (frameRefreshTimer) clearInterval(frameRefreshTimer)
    if (metaRefreshTimer) clearInterval(metaRefreshTimer)
    frameRefreshTimer = setInterval(refreshSmartFrames, 350)
    metaRefreshTimer = setInterval(refreshSmartMeta, 1500)
    // 不 await：首帧推理可能较慢，避免按钮长时间无响应
    void refreshSmartFrames()
    void refreshSmartMeta()
  } catch (error) {
    const apiErr = error?.response?.data?.error
    errorMessage.value =
      uiErrorMessage(apiErr) || (!apiErr ? error.message || '启动智能监控失败' : '')
  }
}

async function handleStop() {
  if (!serviceId.value) return
  try {
    await releaseSmartService(serviceId.value)
  } catch (error) {
    const apiErr = error?.response?.data?.error
    errorMessage.value =
      uiErrorMessage(apiErr) || (!apiErr ? error.message || '停止服务失败' : '')
  } finally {
    if (frameRefreshTimer) clearInterval(frameRefreshTimer)
    if (metaRefreshTimer) clearInterval(metaRefreshTimer)
    frameRefreshTimer = null
    metaRefreshTimer = null
    serviceId.value = null
    alerts.value = []
    liveStatus.value = null
    revokeAllFrameUrls()
  }
}

onBeforeUnmount(() => {
  if (frameRefreshTimer) clearInterval(frameRefreshTimer)
  if (metaRefreshTimer) clearInterval(metaRefreshTimer)
  revokeAllFrameUrls()
})
</script>

<style scoped>
.subtitle {
  color: var(--color-text-secondary);
  margin-bottom: 18px;
  font-size: 17px;
  line-height: 1.47;
}

.config-form {
  display: grid;
  gap: 14px;
}

.config-form select,
.config-form label input[type='text'] {
  width: 100%;
  margin-top: 6px;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-strong);
  font-size: 15px;
  font-family: inherit;
  background: var(--color-bg-elevated);
}

.config-form select {
  cursor: pointer;
}

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.checkbox-row input {
  width: auto;
  margin: 0;
}

.local-videos-block {
  display: grid;
  gap: 10px;
}

.field-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
}

.field-hint {
  margin: 0;
  font-size: 14px;
  line-height: 1.45;
  color: var(--color-text-secondary);
}

.code-tag {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.92em;
  padding: 2px 6px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.05);
  color: var(--color-text);
}

.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.status {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  font-size: 15px;
  transition: opacity var(--duration-normal) var(--ease-apple);
}

.success {
  background: rgba(52, 199, 89, 0.12);
  color: #1e6f42;
  border: 1px solid rgba(52, 199, 89, 0.25);
}

.error {
  background: rgba(255, 59, 48, 0.1);
  color: #c41e16;
  border: 1px solid rgba(255, 59, 48, 0.2);
}

.monitor-grid {
  display: grid;
  gap: 20px;
}

.frame-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.frame-panel {
  display: grid;
  gap: 12px;
}

.frame-heading {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.frame-title {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: var(--letter-tight);
  color: var(--color-text);
}

.frame-note {
  font-size: 13px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.frame-panel img {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: var(--radius-lg);
  background: #eef3f8;
  box-shadow: var(--shadow-soft);
  transition: box-shadow var(--duration-slow) var(--ease-out-expo);
}

.alert-item p {
  margin: 8px 0;
  color: var(--color-text-secondary);
}

.alert-list {
  display: grid;
  gap: 12px;
}

.alert-list-scroll {
  max-height: min(420px, 55vh);
  overflow-y: auto;
  padding-right: 6px;
  scrollbar-gutter: stable;
}

.monitor-live-status {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 14px;
  padding: 12px 14px;
  background: #f5f5f7;
  border-radius: var(--radius-md);
  line-height: 1.5;
}

.live-status-line {
  margin: 0 0 6px;
}

.live-status-line:last-child {
  margin-bottom: 0;
}

.alert-time {
  margin-top: 10px;
  margin-bottom: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  opacity: 0.92;
}

.alert-empty {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
  font-size: 15px;
}

.alert-item {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 14px 16px;
  background: #fafafa;
  transition:
    border-color var(--duration-normal) var(--ease-apple),
    box-shadow var(--duration-slow) var(--ease-out-expo);
}

.alert-item:hover {
  border-color: rgba(0, 113, 227, 0.18);
  box-shadow: var(--shadow-card);
}

.alert-title {
  font-weight: 600;
  color: var(--color-text);
}

@media (max-width: 900px) {
  .frame-grid {
    grid-template-columns: 1fr;
  }

  .frame-title {
    font-size: 20px;
  }
}
</style>
