<template>
  <my-card>
      <h2>视频列表</h2>
      <p class="lead">项目目录中的可用视频文件列表。</p>
      <ul class="file-list">
        <li v-for="file in fileList" :key="file" class="file-list__item">
          <span class="file-list__name">{{ file }}</span>
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
  void file
}
</script>

<style scoped>
.lead {
  color: var(--color-text-secondary);
  font-size: 15px;
  line-height: 1.5;
  margin: 0 0 20px;
}

.file-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.file-list__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: #fafafa;
  transition:
    border-color var(--duration-normal) var(--ease-apple),
    background var(--duration-normal) var(--ease-apple);
}

.file-list__item:hover {
  border-color: rgba(0, 113, 227, 0.22);
  background: #fff;
}

.file-list__name {
  font-size: 14px;
  color: var(--color-text);
  word-break: break-all;
}
</style>
