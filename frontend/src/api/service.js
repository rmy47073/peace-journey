import axios from 'axios'



// 开发环境使用代理，生产环境使用完整URL

const BASE_URL = import.meta.env.DEV ? '/api' : 'http://localhost:5000/api'



// 获取视频文件列表

export function getFileList() {

  return axios.get(`${BASE_URL}/fileList`)

}



// 获取单帧图片（本地视频或摄像头）

export function getOneFrame(data) {

  // data: { cap_type: 'file'|'ip_camera', cap_path: 'xxx' }

  return axios.post(`${BASE_URL}/getOneFrame`, data, {

    responseType: 'blob',

    transformResponse: undefined

  })

}



// 启动服务

export function startService(data) {

  // data: { src_points: [{x, y}, ...], cap_type, cap_path }

  return axios.post(`${BASE_URL}/start`, data)

}



// 获取原始帧

export function getRowFrame(serviceId) {

  console.log('[调试] 调用获取原始帧接口, 服务ID:', serviceId)

  if (!serviceId) {

    console.warn('[警告] 服务ID无效')

    return Promise.reject(new Error('服务ID无效，请先启动服务'))

  }

  return axios.get(`${BASE_URL}/getRowFrame/${serviceId}`, {

    responseType: 'blob',

    transformResponse: undefined

  })

  .then(response => {

    console.log('[调试] 成功获取原始帧, 数据大小:', response.data.size)

    return response

  })

  .catch(error => {

    console.error('[错误] 获取原始帧失败:', error)

    throw error

  })

}



// 获取检测帧

export function getProcessedFrame(serviceId) {

  if (!serviceId) {

    console.warn('[警告] 服务ID无效')

    return Promise.reject(new Error('服务ID无效，请先启动服务'))

  }

  return axios.get(`${BASE_URL}/getProcessedFrame/${serviceId}`, {

    responseType: 'blob',

    transformResponse: undefined

  })

  .then(response => {

    console.log('[调试] 成功获取检测帧, 数据大小:', response.data.size)

    return response

  })

  .catch(error => {

    console.error('[错误] 获取检测帧失败:', error)

    throw error

  })

}



// 获取鸟瞰帧

export function getBirdViewFrame(serviceId) {

  return axios.get(`${BASE_URL}/getBirdViewFrame/${serviceId}`, {

    responseType: 'blob',

    transformResponse: undefined

  })

}



// 释放服务

export function releaseService(serviceId) {

  return axios.get(`${BASE_URL}/release/${serviceId}`)

}



// 获取统计信息

export function getStatistics(serviceId) {

  return axios.post(`${BASE_URL}/getStatistics/${serviceId}`)

}

