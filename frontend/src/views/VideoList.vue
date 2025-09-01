<template>
  <my-card>
    <h2>视频文件列表</h2>
    <ul>
      <li v-for="file in fileList" :key="file">
        {{ file }}
        <my-button @click="selectFile(file)">选择</my-button>
      </li>
    </ul>
    <empty-state v-if="fileList.length === 0" message="暂无视频文件" />
  </my-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getFileList } from '@/api/service'
import MyButton from '@/components/MyButton.vue'
import MyCard from '@/components/MyCard.vue'
import EmptyState from '@/components/EmptyState.vue'

const fileList = ref([])

onMounted(async () => {
  const res = await getFileList()
  fileList.value = res.data.file_list || []
})

function selectFile(file) {
  // 选择视频后的逻辑
}
</script>