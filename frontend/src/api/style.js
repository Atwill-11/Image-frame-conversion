import request from './request'

export function styleConvert(formData) {
  return request.post('/api/style/convert', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 180000,
  })
}

export function getHistory(sessionId) {
  return request.get(`/api/style/history/${sessionId}`)
}

export function deleteHistory(recordId) {
  return request.delete(`/api/style/history/${recordId}`)
}
