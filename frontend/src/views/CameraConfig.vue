<template>
  <my-card>
    <h2>选择视频源</h2>
    <form @submit.prevent="submit">
      <label>
        <input type="radio" v-model="type" value="file" /> 本地视频文件
      </label>
      <label>
        <input type="radio" v-model="type" value="ip_camera" /> 网络摄像头
      </label>
      <div v-if="type === 'file'">
        <input v-model="filePath" placeholder="请输入视频文件路径" />
      </div>
      <div v-else>
        <input v-model="cameraUrl" placeholder="请输入摄像头URL" />
      </div>
      <my-button type="submit">获取帧预览</my-button>
      <!-- 删除这行 -->
      <my-button @click="startAnalysis" v-if="frameUrl">启动分析</my-button>
    </form>
    <frame-preview 
      v-if="serviceId.value" 
      :service-id="serviceId.value" 
      :src="frameUrl"
    />
  </my-card>
</template>

<script setup>
import { ref } from 'vue'
import MyButton from '@/components/MyButton.vue'
import MyCard from '@/components/MyCard.vue'
import FramePreview from './FramePreview.vue'
import { getOneFrame, startService } from '@/api/service'

const type = ref('file')
const filePath = ref('')
const cameraUrl = ref('')
const frameUrl = ref('')
const serviceId = ref('')

async function submit() {
  console.log('[DEBUG] submit方法开始执行');
  console.log('[DEBUG] 提交表单数据:', {
    type: type.value,
    path: type.value === 'file' ? filePath.value : cameraUrl.value
  })
  
  try {
    console.log('[DEBUG] 准备调用startService');
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
    console.log('[DEBUG] startService调用完成');
    if (res.data?.service_id) {
      serviceId.value = res.data.service_id
      console.log('serviceId已设置:', serviceId.value)
    } else {
      serviceId.value = '' // 清空无效值
    }
  } catch (e) {
    console.error('[ERROR] startService调用失败:', e);
  }
}

async function startAnalysis() {
  console.log('[DEBUG] 启动分析服务, serviceId:', serviceId.value)
  if (!serviceId.value) {
    console.warn('[WARN] 无法启动分析: 无效的serviceId')
    return
  }
  // 这里可以添加调用分析API的逻辑
  // 例如: const res = await analyzeVideo(serviceId.value)
  alert('分析服务已启动')
}
</script>


