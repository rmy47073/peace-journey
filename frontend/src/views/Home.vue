<template>
  <div class="home">
    <img src="@/assets/logo.png" class="logo" alt="logo" />
    <h1>施工道路智能监测与预警系统</h1>
    <p>基于 YOLO 检测、目标跟踪、规则引擎和 DeepSeek 推理的实时监控平台。</p>
    <div class="entry-links">
      <router-link to="/service" class="entry-link">基础检测</router-link>
      <router-link to="/smart" class="entry-link">智能监控</router-link>
    </div>
  </div>
</template>

<style scoped>
.home { text-align: center; margin-top: 80px; }
.logo { width: 120px; margin-bottom: 24px; }
.entry-links { display: flex; gap: 12px; justify-content: center; margin-top: 24px; }
.entry-link {
  background: #1890ff;
  color: #fff;
  padding: 10px 18px;
  border-radius: 999px;
  text-decoration: none;
}
</style>
