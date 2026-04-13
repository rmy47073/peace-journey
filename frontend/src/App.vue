<template>
  <div id="app">
    <header class="app-header">
      <div class="app-header__brand">
        <img src="@/assets/logo.png" alt="系统标识" class="app-header__logo" />
        <span class="app-header__title">施工道路智能监控预警系统</span>
      </div>
      <nav class="app-nav" aria-label="主导航">
        <router-link to="/">首页</router-link>
        <router-link to="/service">服务监控</router-link>
        <router-link to="/smart">智能监控</router-link>
        <router-link to="/camera">相机配置</router-link>
      </nav>
    </header>
    <main class="app-main">
      <div class="app-main__view">
        <router-view v-slot="{ Component, route }">
          <transition name="page" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup>
</script>
