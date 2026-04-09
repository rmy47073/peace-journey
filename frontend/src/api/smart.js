import axios from 'axios'

const SMART_API_BASE_URL = import.meta.env.DEV ? '/smart' : 'http://localhost:5000/smart'

function ensureServiceId(serviceId) {
  if (!serviceId && serviceId !== 0) {
    return Promise.reject(new Error('无效的 serviceId'))
  }
  return null
}

function fetchFrame(url) {
  return axios.get(url, { responseType: 'blob' })
}

export function startSmartService(data) {
  return axios.post(`${SMART_API_BASE_URL}/start`, data)
}

export function getSmartRowFrame(serviceId) {
  const invalid = ensureServiceId(serviceId)
  if (invalid) return invalid
  return fetchFrame(`${SMART_API_BASE_URL}/getRowFrame/${serviceId}`)
}

export function getSmartProcessedFrame(serviceId) {
  const invalid = ensureServiceId(serviceId)
  if (invalid) return invalid
  return fetchFrame(`${SMART_API_BASE_URL}/getProcessedFrame/${serviceId}`)
}

export function getSmartBirdViewFrame(serviceId) {
  const invalid = ensureServiceId(serviceId)
  if (invalid) return invalid
  return fetchFrame(`${SMART_API_BASE_URL}/getBirdViewFrame/${serviceId}`)
}

export function getSmartStatistics(serviceId) {
  const invalid = ensureServiceId(serviceId)
  if (invalid) return invalid
  return axios.get(`${SMART_API_BASE_URL}/getStatistics/${serviceId}`)
}

export function getSmartAlerts(serviceId, maxCount = 10) {
  const invalid = ensureServiceId(serviceId)
  if (invalid) return invalid
  return axios.get(`${SMART_API_BASE_URL}/getAlerts/${serviceId}`, {
    params: { max_count: maxCount }
  })
}

export function getSmartRules(serviceId) {
  const invalid = ensureServiceId(serviceId)
  if (invalid) return invalid
  return axios.get(`${SMART_API_BASE_URL}/getRules/${serviceId}`)
}

export function releaseSmartService(serviceId) {
  const invalid = ensureServiceId(serviceId)
  if (invalid) return invalid
  return axios.post(`${SMART_API_BASE_URL}/release/${serviceId}`)
}
