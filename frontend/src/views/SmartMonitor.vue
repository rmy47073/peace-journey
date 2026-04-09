<template>
  <div class="smart-monitor">
    <my-card>
      <h2>智能监控服务</h2>
      <p class="subtitle">启动施工道路实时监测，查看处理画面、风险规则和最新告警。</p>
      <form class="config-form" @submit.prevent="handleStart">
        <label>
          视频源类型
          <select v-model="form.cap_type">
            <option value="file">本地视频</option>
            <option value="ip_camera">网络摄像头</option>
          </select>
        </label>

        <label>
          视频路径或地址
          <input v-model.trim="form.cap_path" placeholder="例如 videos/test.mp4 或 rtsp://..." />
        </label>

        <label>
          透视点 src_points
          <textarea
            v-model="srcPointsText"
            rows="4"
            placeholder='[{"x":120,"y":420},{"x":520,"y":420},{"x":60,"y":760},{"x":620,"y":760}]'
          />
        </label>

        <label>
          危险区域 danger_zones
          <textarea
            v-model="dangerZonesText"
            rows="4"
            placeholder='[[[180,300],[460,300],[460,620],[180,620]]]'
          />
        </label>

        <label class="checkbox-row">
          <input v-model="form.enable_ai" type="checkbox" />
          启用 DeepSeek 辅助推理
        </label>

        <div class="actions">
          <my-button type="submit">启动智能监控</my-button>
          <my-button v-if="serviceId" @click="handleStop">停止服务</my-button>
        </div>
      </form>

      <p v-if="serviceId" class="status success">智能服务已启动，service_id: {{ serviceId }}</p>
      <p v-if="errorMessage" class="status error">{{ errorMessage }}</p>
    </my-card>

    <div v-if="serviceId" class="monitor-grid">
      <my-card>
        <h3>实时画面</h3>
        <div class="frame-grid">
          <div class="frame-panel">
            <span>原始帧</span>
            <img v-if="frameUrls.row" :src="frameUrls.row" alt="原始帧" />
          </div>
          <div class="frame-panel">
            <span>处理帧</span>
            <img v-if="frameUrls.processed" :src="frameUrls.processed" alt="处理帧" />
          </div>
          <div class="frame-panel">
            <span>鸟瞰帧</span>
            <img v-if="frameUrls.bird" :src="frameUrls.bird" alt="鸟瞰帧" />
          </div>
        </div>
      </my-card>

      <my-card>
        <h3>运行状态</h3>
        <div class="stats-list">
          <p>累计车辆: {{ statistics.total_count ?? 0 }}</p>
          <p>长时间停留: {{ statistics.long_stay_count ?? 0 }}</p>
          <p>越线计数: {{ statistics.crossing_count ?? 0 }}</p>
          <p>类别统计: {{ formatCategoryCount(statistics.category_count) }}</p>
        </div>
        <div class="rules-section">
          <h4>活动规则</h4>
          <ul v-if="rules.length">
            <li v-for="rule in rules" :key="rule.rule_id">
              {{ rule.rule_id }} - {{ rule.name }} ({{ rule.level }})
            </li>
          </ul>
          <p v-else>暂无规则数据</p>
        </div>
      </my-card>

      <my-card>
        <h3>最新告警</h3>
        <div v-if="alerts.length" class="alert-list">
          <article v-for="(alert, index) in alerts" :key="`${alert.timestamp}-${index}`" class="alert-item">
            <p class="alert-title">风险等级: {{ alert.rules_result?.risk_level || 'unknown' }}</p>
            <p v-for="item in alert.rules_result?.alerts || []" :key="item.rule_id + String(item.object_id || item.worker_id || item.vehicle_id)">
              {{ item.message }}
            </p>
            <p v-if="alert.decision?.final_decision?.suggestions?.length">
              处置建议: {{ alert.decision.final_decision.suggestions.join('；') }}
            </p>
          </article>
        </div>
        <p v-else>当前暂无告警</p>
      </my-card>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, reactive, ref } from 'vue'
import MyButton from '@/components/MyButton.vue'
import MyCard from '@/components/MyCard.vue'
import {
  getSmartAlerts,
  getSmartBirdViewFrame,
  getSmartProcessedFrame,
  getSmartRowFrame,
  getSmartRules,
  getSmartStatistics,
  releaseSmartService,
  startSmartService
} from '@/api/smart'

const form = reactive({
  cap_type: 'file',
  cap_path: 'videos/test.mp4',
  enable_ai: false
})

const srcPointsText = ref('[{"x":120,"y":420},{"x":520,"y":420},{"x":60,"y":760},{"x":620,"y":760}]')
const dangerZonesText = ref('[[[180,300],[460,300],[460,620],[180,620]]]')
const serviceId = ref(null)
const errorMessage = ref('')
const statistics = ref({})
const rules = ref([])
const alerts = ref([])
const frameUrls = reactive({
  row: '',
  processed: '',
  bird: ''
})

let refreshTimer = null

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

function parseJsonInput(text) {
  try {
    return JSON.parse(text)
  } catch (error) {
    throw new Error('JSON 配置格式不正确，请检查透视点或危险区域输入')
  }
}

function formatCategoryCount(categoryCount) {
  if (!categoryCount) return '暂无'
  if (typeof categoryCount === 'string') return categoryCount
  const entries = Object.entries(categoryCount)
  return entries.length ? entries.map(([key, value]) => `${key}:${value}`).join(', ') : '暂无'
}

async function refreshSmartData() {
  if (!serviceId.value) return

  try {
    const [rowRes, processedRes, birdRes, statsRes, rulesRes, alertsRes] = await Promise.all([
      getSmartRowFrame(serviceId.value),
      getSmartProcessedFrame(serviceId.value),
      getSmartBirdViewFrame(serviceId.value),
      getSmartStatistics(serviceId.value),
      getSmartRules(serviceId.value),
      getSmartAlerts(serviceId.value, 8)
    ])

    setFrameUrl('row', rowRes.data)
    setFrameUrl('processed', processedRes.data)
    setFrameUrl('bird', birdRes.data)
    statistics.value = statsRes.data.statistics || {}
    rules.value = rulesRes.data.rules || []
    alerts.value = alertsRes.data.alerts || []
  } catch (error) {
    errorMessage.value = error?.response?.data?.error || error.message || '刷新智能监控数据失败'
  }
}

async function handleStart() {
  errorMessage.value = ''

  try {
    const response = await startSmartService({
      src_points: parseJsonInput(srcPointsText.value),
      cap_type: form.cap_type,
      cap_path: form.cap_path,
      danger_zones: parseJsonInput(dangerZonesText.value),
      enable_ai: form.enable_ai
    })

    serviceId.value = response.data.service_id
    await refreshSmartData()
    if (refreshTimer) clearInterval(refreshTimer)
    refreshTimer = setInterval(refreshSmartData, 1200)
  } catch (error) {
    errorMessage.value = error?.response?.data?.error || error.message || '启动智能监控失败'
  }
}

async function handleStop() {
  if (!serviceId.value) return
  try {
    await releaseSmartService(serviceId.value)
  } catch (error) {
    errorMessage.value = error?.response?.data?.error || error.message || '停止服务失败'
  } finally {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
    serviceId.value = null
    statistics.value = {}
    rules.value = []
    alerts.value = []
    revokeAllFrameUrls()
  }
}

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  revokeAllFrameUrls()
})
</script>

<style scoped>
.subtitle {
  color: #52606d;
  margin-bottom: 18px;
}

.config-form {
  display: grid;
  gap: 12px;
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

.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.status {
  margin-top: 14px;
  padding: 10px 12px;
  border-radius: 8px;
}

.success {
  background: #e8f7ef;
  color: #146c43;
}

.error {
  background: #fdecec;
  color: #b42318;
}

.monitor-grid {
  display: grid;
  gap: 16px;
}

.frame-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.frame-panel {
  display: grid;
  gap: 8px;
}

.frame-panel img {
  width: 100%;
  border-radius: 10px;
  background: #eef3f8;
}

.stats-list p,
.alert-item p {
  margin: 8px 0;
}

.rules-section {
  margin-top: 18px;
}

.alert-list {
  display: grid;
  gap: 12px;
}

.alert-item {
  border: 1px solid #d9e2ec;
  border-radius: 10px;
  padding: 12px;
  background: #fafcff;
}

.alert-title {
  font-weight: 700;
}
</style>
