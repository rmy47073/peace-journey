import { createRouter, createWebHistory } from 'vue-router'

import Home from '@/views/Home.vue'
import VideoList from '@/views/VideoList.vue'
import CameraConfig from '@/views/CameraConfig.vue'
import YoloService from '@/views/YoloService.vue'
import Statistics from '@/views/Statistics.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/videos', name: 'VideoList', component: VideoList },
  { path: '/camera', name: 'CameraConfig', component: CameraConfig },
  { path: '/service', name: 'YoloService', component: YoloService },
  { path: '/statistics', name: 'Statistics', component: Statistics }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router