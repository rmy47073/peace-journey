<template>
  <div id="app">
    <header class="header">
      <img src="@/assets/logo.png" alt="logo" class="logo" />
      <span class="title">YOLO-Track 智能交通监控系统</span>
      <nav class="nav">
        <router-link to="/">首页</router-link>
        <router-link to="/videos">视频列表</router-link>
        <router-link to="/camera">视频源配置</router-link>
        <router-link to="/service">服务监控</router-link>
        <router-link to="/smart">智能监控</router-link>
        <router-link to="/frames">帧预览</router-link>
        <router-link to="/statistics">统计信息</router-link>
      </nav>
    </header>
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import './assets/global.css'
</script>
