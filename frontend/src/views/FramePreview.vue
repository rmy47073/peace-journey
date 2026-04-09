<template>
  <my-card>
    <h2>帧预览</h2>
    <div class="frames">
      <div>
        <h3>原始帧</h3>
        <img :src="rowFrameUrl" v-if="rowFrameUrl" />
      </div>
      <div>
        <h3>检测帧</h3>
        <img :src="processedFrameUrl" v-if="processedFrameUrl" />
      </div>
      <div>
        <h3>鸟瞰帧</h3>
        <img :src="birdViewFrameUrl" v-if="birdViewFrameUrl" />
      </div>
    </div>
  </my-card>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import MyCard from '@/components/MyCard.vue'
import { getRowFrame, getProcessedFrame, getBirdViewFrame } from '@/api/service'

// 接收父组件传入的 serviceId
const props = defineProps({
  serviceId: {
    type: [String, Number],
    required: true,
    validator: (value) => {
      const isValid = !!value && (typeof value === 'string' || typeof value === 'number');
      if (!isValid) {
        console.error(`FramePreview: Invalid serviceId: ${value}`);
      }
      return isValid;
    }
  }
});

const rowFrameUrl = ref('')
const processedFrameUrl = ref('')
const birdViewFrameUrl = ref('')
let refreshInterval = null

function setUrl(urlRef, blob) {
  if (urlRef.value) {
    URL.revokeObjectURL(urlRef.value)
  }
  urlRef.value = URL.createObjectURL(blob)
}

onMounted(async () => {
  if (!props.serviceId) {
    console.error('FramePreview mounted without serviceId');
    return;
  }
  
  // 添加服务ID有效性检查
  if (typeof props.serviceId !== 'string' && typeof props.serviceId !== 'number') {
    console.error('FramePreview: serviceId must be string or number');
    return;
  }
  
  const refreshFrames = async () => {
    try {
      console.log('Fetching frames for service:', props.serviceId)
      const rowRes = await getRowFrame(props.serviceId)
      console.log('Row frame response:', rowRes.status, rowRes.data.size)
      setUrl(rowFrameUrl, rowRes.data)
      
      const processedRes = await getProcessedFrame(props.serviceId)
      console.log('Processed frame response:', processedRes.status, processedRes.data.size)
      setUrl(processedFrameUrl, processedRes.data)
      
      const birdRes = await getBirdViewFrame(props.serviceId)
      console.log('Bird view response:', birdRes.status, birdRes.data.size)
      setUrl(birdViewFrameUrl, birdRes.data)
    } catch (error) {
      console.error('Failed to fetch frame data:', error)
    }
  }
  
  // 从100ms调整为200ms，减轻后端压力
  refreshInterval = setInterval(refreshFrames, 200)
  await refreshFrames()
})

onBeforeUnmount(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  if (rowFrameUrl.value) URL.revokeObjectURL(rowFrameUrl.value)
  if (processedFrameUrl.value) URL.revokeObjectURL(processedFrameUrl.value)
  if (birdViewFrameUrl.value) URL.revokeObjectURL(birdViewFrameUrl.value)
})
</script>

<style scoped>
.frames {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

img {
  width: 100%;
  border-radius: 10px;
  background: #eef3f8;
}
</style>
