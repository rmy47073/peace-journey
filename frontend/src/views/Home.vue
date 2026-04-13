<template>
  <div class="home">
    <section class="home-hero" ref="heroRef">
      <div class="home-hero__inner" :style="heroInnerStyle">
        <p class="home-hero__eyebrow" v-reveal="0">智能交通 · 施工安全</p>
        <h1 class="home-hero__title" v-reveal="60">施工道路<br />智能监控预警</h1>
        <p class="home-hero__lead" v-reveal="120">
               实时守护现场，风险可见、可量、可控。
        </p>
        <div class="home-hero__actions" v-reveal="180">
          <router-link to="/service" class="home-btn home-btn--primary">进入服务监控</router-link>
          <router-link to="/smart" class="home-btn home-btn--ghost">智能监控</router-link>
        </div>
      </div>
    </section>

    <section class="home-section home-section--muted">
      <div class="home-section__inner home-grid">
        <article class="home-card" v-reveal="0">
          <span class="home-card__icon" aria-hidden="true">◎</span>
          <h3 class="home-card__title">全时感知</h3>
          <p class="home-card__text">多路视频实时监控，画面不间断同步更新</p>
        </article>
        <article class="home-card" v-reveal="90">
          <span class="home-card__icon" aria-hidden="true">◇</span>
          <h3 class="home-card__title">规则驱动</h3>
          <p class="home-card__text">越界、闯入、长时间停留等异常行为自动识别，记录清晰可查。</p>
        </article>
        <article class="home-card" v-reveal="180">
          <span class="home-card__icon" aria-hidden="true">◆</span>
          <h3 class="home-card__title">预警闭环</h3>
          <p class="home-card__text">分级告警并给出处置建议，快速定位问题，形成完整处理流程</p>
        </article>
      </div>
    </section>

    <section class="home-section home-section--workflow">
      <div class="home-section__inner">
        <h2 class="home-workflow-heading" v-reveal>工作流</h2>
        <ol class="home-steps">
          <li class="home-step" v-reveal="0">
            <span class="home-step__index">1</span>
            <div>
              <h3 class="home-step__title">接入视频源</h3>
              <p class="home-step__text">本地文件或网络摄像头，按项目灵活配置。</p>
            </div>
          </li>
          <li class="home-step" v-reveal="100">
            <span class="home-step__index">2</span>
            <div>
              <h3 class="home-step__title">启动检测服务</h3>
              <p class="home-step__text">基础或智能模式，按需开启深度推理辅助。</p>
            </div>
          </li>
          <li class="home-step" v-reveal="200">
            <span class="home-step__index">3</span>
            <div>
              <h3 class="home-step__title">监视与统计</h3>
              <p class="home-step__text">统计指标与告警列表同步更新。</p>
            </div>
          </li>
        </ol>
      </div>
    </section>

    <section class="home-cta" v-reveal>
      <div class="home-cta__inner">
        <h2 class="home-cta__title">准备查看实时画面？</h2>
        <p class="home-cta__text">从服务监控快速拉起一路视频，或在智能监控中体验完整能力。</p>
        <div class="home-cta__actions">
          <router-link to="/smart" class="home-btn home-btn--primary">打开智能监控</router-link>
          <router-link to="/service" class="home-btn home-btn--ghost">查看服务统计</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const heroRef = ref(null)
const scrollY = ref(0)

function onScroll() {
  scrollY.value = window.scrollY || 0
}

const heroInnerStyle = computed(() => {
  const y = scrollY.value
  const translate = Math.min(y * 0.12, 48)
  const opacity = Math.max(0.88, 1 - y / 900)
  return {
    transform: `translate3d(0, ${translate}px, 0)`,
    opacity: String(opacity)
  }
})

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
})
</script>

<style scoped>
.home {
  margin: -clamp(32px, 6vw, 72px) max(-22px, -4vw) 0;
  padding-bottom: 48px;
}

.home-hero {
  min-height: min(88vh, 820px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(48px, 12vw, 120px) max(22px, 4vw);
  text-align: center;
  background: radial-gradient(1200px 600px at 50% -20%, rgba(0, 113, 227, 0.08), transparent 55%),
    linear-gradient(180deg, #f5f5f7 0%, #ebebed 100%);
}

.home-hero__inner {
  max-width: 820px;
  will-change: transform, opacity;
  transition: opacity 0.3s var(--ease-apple);
}

.home-hero__eyebrow {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-accent);
  margin: 0 0 16px;
}

.home-hero__title {
  font-size: var(--text-hero);
  font-weight: 600;
  letter-spacing: var(--letter-tighter);
  line-height: 1.05;
  margin: 0 0 20px;
  color: var(--color-text);
}

.home-hero__lead {
  font-size: 21px;
  line-height: 1.381;
  color: var(--color-text-secondary);
  max-width: 640px;
  margin: 0 auto 32px;
}

.home-hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.home-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 22px;
  font-size: 15px;
  font-weight: 500;
  border-radius: var(--radius-pill);
  border: 1px solid transparent;
  cursor: pointer;
  transition:
    background var(--duration-normal) var(--ease-out-expo),
    color var(--duration-normal) var(--ease-out-expo),
    border-color var(--duration-normal) var(--ease-out-expo),
    transform var(--duration-fast) var(--ease-spring),
    box-shadow var(--duration-normal) var(--ease-apple);
}

.home-btn--primary {
  background: var(--color-accent);
  color: #fff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.home-btn--primary:hover {
  background: var(--color-accent-hover);
  box-shadow: 0 8px 24px rgba(0, 113, 227, 0.25);
}

.home-btn--primary:active {
  transform: scale(0.98);
}

.home-btn--ghost {
  background: rgba(255, 255, 255, 0.72);
  color: var(--color-accent);
  border-color: rgba(0, 113, 227, 0.35);
  backdrop-filter: blur(12px);
}

.home-btn--ghost:hover {
  background: #fff;
  border-color: var(--color-accent);
}

.home-btn--ghost:active {
  transform: scale(0.98);
}

.home-section {
  padding: clamp(72px, 14vw, 120px) max(22px, 4vw);
}

.home-section--muted {
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  margin: 0 max(22px, 4vw);
  padding-left: max(22px, 4vw);
  padding-right: max(22px, 4vw);
}

.home-section__inner {
  max-width: 820px;
  margin: 0 auto;
  text-align: center;
}

.home-section__eyebrow {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-tertiary);
  margin: 0 0 12px;
}

.home-section__title {
  font-size: var(--text-title);
  font-weight: 600;
  letter-spacing: var(--letter-tight);
  margin: 0 0 16px;
}

/* 单独标题「工作流」：留白与字距 */
.home-section--workflow .home-section__inner {
  padding-top: clamp(8px, 2vw, 16px);
}

.home-workflow-heading {
  font-size: var(--text-title);
  font-weight: 600;
  letter-spacing: 0.08em;
  margin: 0 auto 36px;
  color: var(--color-text);
  line-height: 1.15;
}

.home-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: clamp(16px, 4vw, 32px);
  max-width: 1000px;
  text-align: left;
}

.home-card {
  padding: 28px 24px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: linear-gradient(180deg, #fafafa 0%, #fff 100%);
  transition:
    border-color var(--duration-normal) var(--ease-apple),
    box-shadow var(--duration-slow) var(--ease-out-expo),
    transform var(--duration-normal) var(--ease-out-expo);
}

.home-card:hover {
  border-color: rgba(0, 113, 227, 0.22);
  box-shadow: var(--shadow-soft);
  transform: translateY(-4px);
}

.home-card__icon {
  display: block;
  font-size: 22px;
  color: var(--color-accent);
  margin-bottom: 12px;
  opacity: 0.85;
}

.home-card__title {
  font-size: 19px;
  font-weight: 600;
  margin: 0 0 8px;
}

.home-card__text {
  font-size: 15px;
  line-height: 1.5;
  color: var(--color-text-secondary);
  margin: 0;
}

.home-steps {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 24px;
  text-align: left;
  max-width: 720px;
  margin-left: auto;
  margin-right: auto;
}

.home-step {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 20px;
  align-items: start;
  padding: 24px 28px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: #fff;
  transition: box-shadow var(--duration-slow) var(--ease-out-expo);
}

.home-step:hover {
  box-shadow: var(--shadow-card);
}

.home-step__index {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-accent);
  background: var(--color-accent-muted);
}

.home-step__title {
  font-size: 17px;
  font-weight: 600;
  margin: 0 0 6px;
}

.home-step__text {
  font-size: 15px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.home-cta {
  margin-top: 32px;
  padding: clamp(56px, 10vw, 96px) max(22px, 4vw);
}

.home-cta__inner {
  max-width: 720px;
  margin: 0 auto;
  text-align: center;
  padding: clamp(40px, 8vw, 56px) clamp(24px, 6vw, 48px);
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, rgba(0, 113, 227, 0.09) 0%, rgba(245, 245, 247, 0.9) 50%, #fff 100%);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-soft);
}

.home-cta__title {
  font-size: clamp(1.5rem, 3vw, 2rem);
  font-weight: 600;
  letter-spacing: var(--letter-tight);
  margin: 0 0 12px;
}

.home-cta__text {
  font-size: 17px;
  color: var(--color-text-secondary);
  margin: 0 0 28px;
  line-height: 1.5;
}

.home-cta__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

@media (max-width: 900px) {
  .home-grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .home-hero__inner {
    transform: none !important;
    opacity: 1 !important;
  }

  .home-card:hover {
    transform: none;
  }

  .home-btn--primary:active,
  .home-btn--ghost:active {
    transform: none;
  }
}
</style>
