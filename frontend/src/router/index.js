import { createRouter, createWebHistory } from 'vue-router'

import Home from '@/views/Home.vue'
import CameraConfig from '@/views/CameraConfig.vue'
import YoloService from '@/views/YoloService.vue'
import SmartMonitor from '@/views/SmartMonitor.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/camera', name: 'CameraConfig', component: CameraConfig },
  { path: '/service', name: 'YoloService', component: YoloService },
  { path: '/smart', name: 'SmartMonitor', component: SmartMonitor },
  { path: '/frames', redirect: '/service' },
  { path: '/statistics', redirect: '/service' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
