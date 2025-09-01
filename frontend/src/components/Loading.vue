<!-- filepath: frontend/src/components/Loading.vue -->
<template>
  <div class="loading">
    <img src="@/assets/loading.gif" alt="loading" />
    <span>加载中...</span>
  </div>
</template>

<style scoped>
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #888;
  margin: 20px 0;
}
.loading img {
  width: 48px;
  height: 48px;
  margin-bottom: 8px;
}
</style>