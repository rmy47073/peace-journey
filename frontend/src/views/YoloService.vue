<template>
  <my-card>
    <h2>服务监控</h2>
    <p class="subtitle">
      从项目 <code class="code-tag">videos</code> 目录选择视频启动基础检测，统计信息在画面下方实时显示。
    </p>

    <videos-folder-picker
      v-if="!serviceId"
      api-base="/api"
      :busy="startBusy"
      :active-cap-path="lastCapPath"
      @analyze="onPickVideo"
    />

    <div class="actions">
      <my-button v-if="serviceId" @click="localReleaseService">停止服务</my-button>
    </div>

    <p v-if="statusMessage" class="status">{{ statusMessage }}</p>

    <Transition name="service-dock">
      <section v-if="serviceId" :key="serviceId" class="service-dock">
        <service-frame-grid embedded :service-id="serviceId" />
        <my-card class="service-dock__stats">
          <service-statistics :service-id="serviceId" />
        </my-card>
      </section>
    </Transition>
  </my-card>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'
import MyButton from '@/components/MyButton.vue'
import MyCard from '@/components/MyCard.vue'
import VideosFolderPicker from '@/components/VideosFolderPicker.vue'
import ServiceFrameGrid from '@/components/ServiceFrameGrid.vue'
import ServiceStatistics from '@/components/ServiceStatistics.vue'
import { startService, releaseService } from '@/api/service'
import { uiErrorMessage } from '@/utils/uiError'

const defaultSrcPoints = [
  { x: 120, y: 420 },
  { x: 520, y: 420 },
  { x: 60, y: 760 },
  { x: 620, y: 760 }
]

const serviceId = ref(null)
const statusMessage = ref('')
const startBusy = ref(false)
const lastCapPath = ref('')

async function onPickVideo({ capPath }) {
  statusMessage.value = ''
  startBusy.value = true
  try {
    const res = await startService({
      src_points: defaultSrcPoints,
      cap_type: 'file',
      cap_path: capPath
    })
    if (res.data && res.data.service_id) {
      serviceId.value = res.data.service_id
      lastCapPath.value = capPath
      statusMessage.value = '基础检测服务运行中'
    } else {
      statusMessage.value = '服务启动失败'
    }
  } catch (error) {
    const apiErr = error?.response?.data?.error
    statusMessage.value =
      uiErrorMessage(apiErr) || (!apiErr ? error.message || '服务启动失败' : '')
  } finally {
    startBusy.value = false
  }
}

async function localReleaseService() {
  if (!serviceId.value) return
  try {
    await releaseService(serviceId.value)
  } catch (error) {
    const apiErr = error?.response?.data?.error
    statusMessage.value =
      uiErrorMessage(apiErr) || (!apiErr ? error.message || '服务停止失败' : '')
  } finally {
    serviceId.value = null
    statusMessage.value = '服务已停止'
  }
}

onBeforeUnmount(() => {
  if (serviceId.value) {
    localReleaseService()
  }
})
</script>

<style scoped>
.subtitle {
  color: var(--color-text-secondary);
  margin-bottom: 18px;
  font-size: 17px;
  line-height: 1.47;
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
  margin-top: 16px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.status {
  color: var(--color-text-secondary);
  font-size: 15px;
  margin-bottom: 8px;
}

.service-dock {
  margin-top: 8px;
}

.service-dock__stats {
  margin-top: 24px;
}

.service-dock-enter-active {
  transition:
    opacity 0.55s var(--ease-out-expo),
    transform 0.65s var(--ease-out-expo);
}

.service-dock-leave-active {
  transition:
    opacity 0.4s var(--ease-apple),
    transform 0.45s var(--ease-apple);
}

.service-dock-enter-from,
.service-dock-leave-to {
  opacity: 0;
  transform: translateY(22px);
}

.service-dock-enter-to,
.service-dock-leave-from {
  opacity: 1;
  transform: translateY(0);
}

.service-dock-enter-active .service-dock__stats {
  animation: statsRise 0.55s var(--ease-out-expo) 0.1s both;
}

@keyframes statsRise {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .service-dock-enter-active,
  .service-dock-leave-active {
    transition: none;
  }

  .service-dock-enter-from,
  .service-dock-leave-to,
  .service-dock-enter-to,
  .service-dock-leave-from {
    opacity: 1;
    transform: none;
  }

  .service-dock-enter-active .service-dock__stats {
    animation: none;
  }
}
</style>
