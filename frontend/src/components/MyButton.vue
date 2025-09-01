<!-- filepath: frontend/src/components/MyButton.vue -->
<template>
  <button class="my-btn" :type="type" @click="$emit('click')">
    <slot />
  </button>
</template>

<script setup>
defineProps({
  type: { type: String, default: 'button' }
});
</script>

<style scoped>
.my-btn {
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 8px 20px;
  cursor: pointer;
  transition: background 0.2s;
}
.my-btn:hover {
  background: #40a9ff;
}
</style>