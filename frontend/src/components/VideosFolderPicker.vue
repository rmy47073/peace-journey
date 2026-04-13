<template>
  <div class="video-picker">
    <p v-if="loadError" class="video-picker__error">{{ loadError }}</p>
    <empty-state v-else-if="!loadingList && fileNames.length === 0" message="videos 目录下暂无支持的视频文件（如 mp4、mov、avi）" />
    <p v-else-if="loadingList" class="video-picker__loading">正在读取视频列表…</p>
    <ul v-else class="video-picker__list" role="list">
      <li
        v-for="name in fileNames"
        :key="name"
        class="video-picker__row"
        :class="{ 'is-active': capPathFor(name) === activeCapPath }"
      >
        <div class="video-picker__thumb" aria-hidden="true">
          <img v-if="thumbs[name]" :src="thumbs[name]" alt="" class="video-picker__thumb-img" />
          <div v-else-if="thumbLoading[name]" class="video-picker__thumb-placeholder">加载封面…</div>
          <div v-else class="video-picker__thumb-placeholder">无预览</div>
        </div>
        <div class="video-picker__meta">
          <span class="video-picker__name" :title="name">{{ name }}</span>
        </div>
        <my-button type="button" :disabled="busy" class="video-picker__btn" @click="emitAnalyze(name)">
          {{ busy && capPathFor(name) === activeCapPath ? '启动中…' : '分析' }}
        </my-button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import axios from 'axios'
import MyButton from '@/components/MyButton.vue'
import EmptyState from '@/components/EmptyState.vue'
import { isLikelyJpegBlob } from '@/utils/blobImage'

const props = defineProps({
  /** `/api` 或 `/smart`（与 vite 代理一致） */
  apiBase: {
    type: String,
    required: true
  },
  busy: {
    type: Boolean,
    default: false
  },
  activeCapPath: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['analyze'])

const fileNames = ref([])
const loadingList = ref(true)
const loadError = ref('')
const thumbs = ref({})
const thumbLoading = ref({})
const objectUrls = []

function capPathFor(name) {
  return `videos/${name}`
}

function emitAnalyze(name) {
  emit('analyze', { capPath: capPathFor(name) })
}

async function fetchFileList() {
  loadingList.value = true
  loadError.value = ''
  try {
    const { data } = await axios.get(`${props.apiBase}/fileList`)
    fileNames.value = data.file_list || []
  } catch (e) {
    loadError.value = e?.response?.data?.error || e.message || '无法获取视频列表'
    fileNames.value = []
  } finally {
    loadingList.value = false
  }
}

async function loadThumbnails(names) {
  for (const name of names) {
    thumbLoading.value = { ...thumbLoading.value, [name]: true }
    try {
      const { data } = await axios.post(
        `${props.apiBase}/getOneFrame`,
        { cap_type: 'file', cap_path: capPathFor(name) },
        { responseType: 'blob' }
      )
      if (await isLikelyJpegBlob(data)) {
        const url = URL.createObjectURL(data)
        objectUrls.push(url)
        thumbs.value = { ...thumbs.value, [name]: url }
      } else {
        thumbs.value = { ...thumbs.value, [name]: '' }
      }
    } catch {
      thumbs.value = { ...thumbs.value, [name]: '' }
    } finally {
      thumbLoading.value = { ...thumbLoading.value, [name]: false }
    }
  }
}

function revokeThumbs() {
  objectUrls.splice(0).forEach((u) => URL.revokeObjectURL(u))
  thumbs.value = {}
  thumbLoading.value = {}
}

watch(
  fileNames,
  (names) => {
    revokeThumbs()
    if (names.length) {
      void loadThumbnails(names)
    }
  },
  { flush: 'post' }
)

watch(
  () => props.apiBase,
  () => {
    revokeThumbs()
    void fetchFileList()
  }
)

void fetchFileList()

onBeforeUnmount(() => {
  revokeThumbs()
})
</script>

<style scoped>
.video-picker {
  width: 100%;
}

.video-picker__error {
  margin: 0;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  font-size: 15px;
  color: #c41e16;
  background: rgba(255, 59, 48, 0.1);
  border: 1px solid rgba(255, 59, 48, 0.2);
}

.video-picker__loading {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 15px;
}

.video-picker__list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.video-picker__row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: #fafafa;
  transition:
    border-color var(--duration-normal) var(--ease-apple),
    background var(--duration-normal) var(--ease-apple),
    box-shadow var(--duration-slow) var(--ease-out-expo);
}

.video-picker__row:hover {
  border-color: rgba(0, 113, 227, 0.22);
  background: #fff;
}

.video-picker__row.is-active {
  border-color: rgba(0, 113, 227, 0.35);
  box-shadow: var(--shadow-card);
  background: #fff;
}

.video-picker__thumb {
  flex-shrink: 0;
  width: 120px;
  height: 68px;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: #eef3f8;
  box-shadow: inset 0 0 0 1px var(--color-border);
}

.video-picker__thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.video-picker__thumb-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: var(--color-text-tertiary);
  padding: 4px;
  text-align: center;
}

.video-picker__meta {
  flex: 1;
  min-width: 0;
}

.video-picker__name {
  display: block;
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text);
  word-break: break-all;
  line-height: 1.35;
}

.video-picker__btn {
  flex-shrink: 0;
}

@media (max-width: 640px) {
  .video-picker__row {
    flex-wrap: wrap;
  }

  .video-picker__thumb {
    width: 100%;
    height: auto;
    aspect-ratio: 16 / 9;
  }

  .video-picker__btn {
    width: 100%;
  }
}
</style>
