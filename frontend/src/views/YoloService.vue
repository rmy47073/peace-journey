<template>
  <my-card>
    <h2>服务启动与监控</h2>
    <form @submit.prevent="localStartService">
      <div>
        <label>透视变换点（src_points）：</label>
        <input v-for="(pt, idx) in srcPoints" :key="idx" v-model.number="srcPoints[idx].x" placeholder="x" style="width:60px" />
        <input v-for="(pt, idx) in srcPoints" :key="idx+4" v-model.number="srcPoints[idx].y" placeholder="y" style="width:60px" />
      </div>
      <my-button type="submit">启动服务</my-button>
    </form>
    <div v-if="serviceId">
      <p>服务ID：{{ serviceId }}</p>
      <frame-preview :service-id="serviceId" />
      <my-button @click="localReleaseService">释放服务</my-button>
    </div>
  </my-card>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import MyButton from '@/components/MyButton.vue'
import MyCard from '@/components/MyCard.vue'
import FramePreview from './FramePreview.vue'
import { startService, releaseService } from '@/api/service'

const srcPoints = ref([
  { x: 0, y: 0 }, { x: 100, y: 0 }, { x: 0, y: 100 }, { x: 100, y: 100 }
])
const serviceId = ref(null)

async function localStartService() {
  const res = await startService({ 
    src_points: srcPoints.value, 
    cap_type: 'file', 
    cap_path: 'videos/test.mp4' // 使用实际视频路径
  })
  if (res.data && res.data.service_id) {
    serviceId.value = res.data.service_id
  }
}

async function localReleaseService() {
  if (serviceId.value) {
    await releaseService(serviceId.value)
    serviceId.value = null
  }
}

// 组件卸载时自动释放服务
onBeforeUnmount(() => {
  if (serviceId.value) {
    localReleaseService()
  }
})
</script>