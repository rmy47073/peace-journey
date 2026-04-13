<template>
  <button class="my-btn" :type="type" :disabled="disabled" @click="$emit('click')">
    <slot />
  </button>
</template>

<script setup>
defineProps({
  type: { type: String, default: 'button' },
  disabled: { type: Boolean, default: false }
})
</script>

<style scoped>
.my-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 20px;
  font-family: inherit;
  font-size: 15px;
  font-weight: 500;
  color: #fff;
  background: var(--color-accent);
  border: none;
  border-radius: var(--radius-pill);
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
  transition:
    background var(--duration-normal) var(--ease-out-expo),
    box-shadow var(--duration-normal) var(--ease-out-expo),
    transform var(--duration-fast) var(--ease-spring);
}

.my-btn:hover {
  background: var(--color-accent-hover);
  box-shadow: 0 6px 20px rgba(0, 113, 227, 0.22);
}

.my-btn:active {
  transform: scale(0.98);
}

.my-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.my-btn:disabled:hover {
  background: var(--color-accent);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.my-btn:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 4px var(--color-accent-muted),
    0 6px 20px rgba(0, 113, 227, 0.22);
}

@media (prefers-reduced-motion: reduce) {
  .my-btn:active {
    transform: none;
  }
}
</style>
