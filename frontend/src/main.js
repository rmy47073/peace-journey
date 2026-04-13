import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/global.css'

const app = createApp(App)
app.use(router)

app.directive('reveal', {
  mounted(el, binding) {
    const raw = binding.value
    const delay = typeof raw === 'number' ? raw : raw?.delay ?? 0
    el.classList.add('reveal-block')
    el.style.setProperty('--reveal-delay', `${delay}ms`)

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) return
        requestAnimationFrame(() => {
          el.classList.add('is-revealed')
        })
        observer.disconnect()
      },
      { rootMargin: '0px 0px -10% 0px', threshold: 0.08 }
    )
    observer.observe(el)
    el.__revealObserver = observer
  },
  unmounted(el) {
    el.__revealObserver?.disconnect()
  }
})

app.mount('#app')
