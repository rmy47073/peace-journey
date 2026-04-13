<template>
  <my-card>
      <h2>相机配置</h2>
      <p class="lead">选择本地文件或网络摄像头作为视频源，可在下方查看原始与检测画面。</p>
      <form class="form" @submit.prevent="submit">
        <label class="radio-line">
          <input type="radio" v-model="type" value="file" />
          本地视频文件
        </label>
        <label class="radio-line">
          <input type="radio" v-model="type" value="ip_camera" />
          网络摄像头
        </label>
        <div v-if="type === 'file'">
          <label>
            路径
            <input v-model="filePath" placeholder="请输入视频文件路径" />
          </label>
        </div>
        <div v-else>
          <label>
            地址
            <input v-model="cameraUrl" placeholder="请输入摄像头 URL" />
          </label>
        </div>
        <div class="actions">
          <my-button type="submit">连接视频源</my-button>
          <my-button v-if="serviceId" type="button" @click="startAnalysis">启动分析</my-button>
        </div>
      </form>
      <Transition name="service-dock">
        <div v-if="serviceId" :key="serviceId" class="preview-wrap">
          <service-frame-grid embedded :service-id="serviceId" />
        </div>
      </Transition>
  </my-card>
</template>

<script setup>
import { ref } from 'vue'
import MyButton from '@/components/MyButton.vue'
import MyCard from '@/components/MyCard.vue'
import ServiceFrameGrid from '@/components/ServiceFrameGrid.vue'
import { startService } from '@/api/service'

const type = ref('file')
const filePath = ref('')
const cameraUrl = ref('')
const serviceId = ref('')

async function submit() {
  try {
    const res = await startService({
      src_points: [
        { x: 0, y: 0 },
        { x: 100, y: 0 },
        { x: 0, y: 100 },
        { x: 100, y: 100 }
      ],
      cap_type: type.value,
      cap_path: type.value === 'file' ? filePath.value : cameraUrl.value
    })
    if (res.data?.service_id) {
      serviceId.value = res.data.service_id
    } else {
      serviceId.value = ''
    }
  } catch (e) {
    console.error('startService failed:', e)
  }
}

function startAnalysis() {
  if (!serviceId.value) {
    console.warn('无法启动分析：无效的 serviceId')
    return
  }
  alert('分析服务已启动')
}
</script>

<style scoped>
.lead {
  color: var(--color-text-secondary);
  font-size: 15px;
  line-height: 1.5;
  margin: 0 0 20px;
}

.form {
  display: grid;
  gap: 16px;
}

.radio-line {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 0;
}

.radio-line input {
  width: auto;
  margin: 0;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.preview-wrap {
  margin-top: 12px;
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
  transform: translateY(20px);
}

.service-dock-enter-to,
.service-dock-leave-from {
  opacity: 1;
  transform: translateY(0);
}

@media (prefers-reduced-motion: reduce) {
  .service-dock-enter-active,
  .service-dock-leave-active {
    transition: none;
  }

  .service-dock-enter-from,
  .service-dock-leave-to {
    opacity: 1;
    transform: none;
  }
}
</style>
