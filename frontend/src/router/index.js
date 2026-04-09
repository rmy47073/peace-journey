import { createRouter, createWebHistory } from 'vue-router'

import Home from '@/views/Home.vue'
import VideoList from '@/views/VideoList.vue'
import CameraConfig from '@/views/CameraConfig.vue'
import YoloService from '@/views/YoloService.vue'
import Statistics from '@/views/Statistics.vue'
import FramePreview from '@/views/FramePreview.vue'
import SmartMonitor from '@/views/SmartMonitor.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/videos', name: 'VideoList', component: VideoList },
  { path: '/camera', name: 'CameraConfig', component: CameraConfig },
  { path: '/service', name: 'YoloService', component: YoloService },
  { path: '/frames', name: 'FramePreview', component: FramePreview, props: { serviceId: 1 } },
  { path: '/statistics', name: 'Statistics', component: Statistics },
  { path: '/smart', name: 'SmartMonitor', component: SmartMonitor }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
