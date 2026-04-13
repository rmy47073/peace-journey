<template>
  <div class="loading">
    <img src="@/assets/loading.gif" alt="" role="presentation" />
    <span>加载中…</span>
  </div>
</template>

<style scoped>
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: var(--color-text-tertiary);
  margin: 24px 0;
  font-size: 15px;
}

.loading img {
  width: 44px;
  height: 44px;
  margin-bottom: 10px;
  opacity: 0.85;
}
</style>
