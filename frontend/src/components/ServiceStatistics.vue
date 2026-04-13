<template>
  <div class="service-stats">
    <h3 class="service-stats__title">统计信息</h3>
    <div v-if="statistics" class="service-stats__grid">
      <div class="service-stats__cell">
        <span class="service-stats__value">{{ statistics.total_count ?? '—' }}</span>
        <span class="service-stats__name">总车辆数</span>
      </div>
      <div class="service-stats__cell">
        <span class="service-stats__value">{{ formatCategory(statistics.category_count) }}</span>
        <span class="service-stats__name">各类别数量</span>
      </div>
      <div class="service-stats__cell">
        <span class="service-stats__value">{{ statistics.long_stay_count ?? '—' }}</span>
        <span class="service-stats__name">长时间停留</span>
      </div>
      <div class="service-stats__cell">
        <span class="service-stats__value">{{ statistics.crossing_count ?? '—' }}</span>
        <span class="service-stats__name">过线车辆</span>
      </div>
    </div>
    <loading v-else />
  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import Loading from '@/components/Loading.vue'
import { getStatistics } from '@/api/service'

const props = defineProps({
  serviceId: {
    type: [String, Number],
    required: true
  }
})

const statistics = ref(null)
let pollTimer = null

function formatCategory(v) {
  if (v == null || v === '') return '—'
  if (typeof v === 'object') {
    const entries = Object.entries(v)
    return entries.length ? entries.map(([k, x]) => `${k}:${x}`).join(', ') : '—'
  }
  return String(v)
}

async function load() {
  try {
    const res = await getStatistics(props.serviceId)
    statistics.value = res.data.statistics ?? null
  } catch {
    statistics.value = {
      total_count: 0,
      category_count: '暂无数据',
      long_stay_count: 0,
      crossing_count: 0
    }
  }
}

function startPoll() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  statistics.value = null
  load()
  pollTimer = setInterval(load, 2000)
}

watch(
  () => props.serviceId,
  (id) => {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
    statistics.value = null
    if (id == null || id === '') return
    startPoll()
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.service-stats__title {
  font-size: 19px;
  font-weight: 600;
  margin: 0 0 20px;
  letter-spacing: var(--letter-tight);
}

.service-stats__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

@media (min-width: 720px) {
  .service-stats__grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.service-stats__cell {
  padding: 18px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: linear-gradient(180deg, #fafafa 0%, #fff 100%);
  transition:
    border-color var(--duration-normal) var(--ease-apple),
    box-shadow var(--duration-slow) var(--ease-out-expo);
}

.service-stats__cell:hover {
  border-color: rgba(0, 113, 227, 0.2);
  box-shadow: var(--shadow-card);
}

.service-stats__value {
  display: block;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: var(--letter-tight);
  color: var(--color-text);
  margin-bottom: 6px;
  word-break: break-word;
}

.service-stats__name {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-tertiary);
  letter-spacing: 0.02em;
}
</style>
