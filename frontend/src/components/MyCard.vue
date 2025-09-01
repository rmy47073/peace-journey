<!-- filepath: frontend/src/components/MyCard.vue -->
<template>
  <div class="my-card">
    <slot />
  </div>
</template>

<style scoped>
.my-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  padding: 24px;
  margin: 16px 0;
}
</style>