<!-- filepath: frontend/src/components/EmptyState.vue -->
<template>
  <div class="empty-state">
    <img src="@/assets/empty.png" alt="empty" />
    <p>{{ message }}</p>
  </div>
</template>

<script setup>
defineProps({
  message: { type: String, default: '暂无数据' }
});
</script>

<style scoped>
.empty-state {
  text-align: center;
  color: #aaa;
  margin: 40px 0;
}
.empty-state img {
  width: 80px;
  height: 80px;
  margin-bottom: 12px;
}
</style>