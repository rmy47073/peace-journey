<template>
  <div :class="['service-frames', embedded && 'service-frames--embedded']">
    <div class="service-frames__item">
      <h3 class="service-frames__label">原始画面</h3>
      <img v-if="rowFrameUrl" :src="rowFrameUrl" alt="原始视频帧" class="service-frames__img" />
    </div>
    <div class="service-frames__item">
      <h3 class="service-frames__label">检测画面</h3>
      <img v-if="processedFrameUrl" :src="processedFrameUrl" alt="检测叠加帧" class="service-frames__img" />
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount, watch } from 'vue'
import { getRowFrame, getProcessedFrame } from '@/api/service'
import { isLikelyJpegBlob } from '@/utils/blobImage'

const props = defineProps({
  serviceId: {
    type: [String, Number],
    required: true
  },
  embedded: {
    type: Boolean,
    default: false
  }
})

const rowFrameUrl = ref('')
const processedFrameUrl = ref('')
let refreshInterval = null
let refreshBusy = false

function setUrl(urlRef, blob) {
  if (urlRef.value) URL.revokeObjectURL(urlRef.value)
  urlRef.value = URL.createObjectURL(blob)
}

function clearTimers() {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

function revokeAll() {
  if (rowFrameUrl.value) URL.revokeObjectURL(rowFrameUrl.value)
  if (processedFrameUrl.value) URL.revokeObjectURL(processedFrameUrl.value)
  rowFrameUrl.value = ''
  processedFrameUrl.value = ''
}

async function refreshFrames() {
  if (!props.serviceId || refreshBusy) return
  refreshBusy = true
  try {
    const settled = await Promise.allSettled([
      getRowFrame(props.serviceId),
      getProcessedFrame(props.serviceId)
    ])
    const rowRes = settled[0]
    const procRes = settled[1]
    if (rowRes.status === 'fulfilled' && (await isLikelyJpegBlob(rowRes.value.data))) {
      setUrl(rowFrameUrl, rowRes.value.data)
    }
    if (procRes.status === 'fulfilled' && (await isLikelyJpegBlob(procRes.value.data))) {
      setUrl(processedFrameUrl, procRes.value.data)
    }
  } catch (e) {
    console.error('ServiceFrameGrid refresh failed:', e)
  } finally {
    refreshBusy = false
  }
}

function startPolling() {
  clearTimers()
  revokeAll()
  if (!props.serviceId) return
  refreshFrames()
  refreshInterval = setInterval(refreshFrames, 500)
}

watch(
  () => props.serviceId,
  () => {
    clearTimers()
    revokeAll()
    startPolling()
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  clearTimers()
  revokeAll()
})
</script>

<style scoped>
.service-frames {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: clamp(16px, 3vw, 24px);
}

.service-frames--embedded {
  margin-top: 12px;
}

.service-frames__label {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin: 0 0 10px;
  letter-spacing: var(--letter-tight);
}

.service-frames__img {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: var(--radius-lg);
  background: #eef3f8;
  box-shadow: var(--shadow-card);
  transition:
    box-shadow var(--duration-slow) var(--ease-out-expo),
    transform var(--duration-normal) var(--ease-out-expo);
}

.service-frames__img:hover {
  box-shadow: var(--shadow-soft);
}

@media (max-width: 768px) {
  .service-frames {
    grid-template-columns: 1fr;
  }
}
</style>
