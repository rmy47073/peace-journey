import axios from 'axios'

const BASE_URL = 'http://localhost:5000/api'

// 获取视频文件列表
export function getFileList() {
  return axios.get(`${BASE_URL}/fileList`)
}

// 获取单帧图片（本地视频或摄像头）
export function getOneFrame(data) {
  // data: { cap_type: 'file'|'ip_camera', cap_path: 'xxx' }
  return axios.post(`${BASE_URL}/getOneFrame`, data, { responseType: 'blob' })
}

// 启动服务
export function startService(data) {
  // data: { src_points: [{x, y}, ...], cap_type, cap_path }
  return axios.post(`${BASE_URL}/start`, data)
}

// 获取原始帧
export function getRowFrame(serviceId) {
  console.log('[DEBUG] 调用getRowFrame, serviceId:', serviceId) // 调试serviceId
  if (!serviceId) {
    console.warn('[WARN] 无效的serviceId') // 警告日志
    return Promise.reject(new Error('无效的serviceId'))
  }
  return axios.get(`${BASE_URL}/getRowFrame/${serviceId}`, { responseType: 'blob' })
    .then(response => {
      console.log('[DEBUG] 成功获取原始帧, 数据大小:', response.data.size) // 响应数据大小
      return response
    })
    .catch(error => {
      console.error('[ERROR] 获取原始帧失败:', error) // 详细错误日志
      throw error
    })
}

// 获取检测帧
export function getProcessedFrame(serviceId) {
  if (!serviceId) {
    console.warn('[WARN] 无效的serviceId')
    return Promise.reject(new Error('无效的serviceId'))
  }
  return axios.get(`${BASE_URL}/getProcessedFrame/${serviceId}`, { 
    responseType: 'blob' 
  })
  .then(response => {
    console.log('[DEBUG] 成功获取处理帧, 数据大小:', response.data.size)
    return response
  })
  .catch(error => {
    console.error('[ERROR] 获取处理帧失败:', error)
    throw error
  })
}

// 获取鸟瞰帧
export function getBirdViewFrame(serviceId) {
  return axios.get(`${BASE_URL}/getBirdViewFrame/${serviceId}`, { responseType: 'blob' })
}

// 释放服务
export function releaseService(serviceId) {
  return axios.get(`${BASE_URL}/release/${serviceId}`)
}

// 获取统计信息
export function getStatistics(serviceId) {
  return axios.post(`${BASE_URL}/getStatistics/${serviceId}`)
}