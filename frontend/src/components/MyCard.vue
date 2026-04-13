<template>
  <div class="my-card">
    <slot />
  </div>
</template>

<style scoped>
.my-card {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  padding: clamp(24px, 4vw, 32px);
  margin: 0 0 20px;
  transition:
    box-shadow var(--duration-slow) var(--ease-out-expo),
    border-color var(--duration-normal) var(--ease-apple);
}

.my-card:hover {
  box-shadow: var(--shadow-soft);
  border-color: rgba(0, 0, 0, 0.08);
}
</style>
