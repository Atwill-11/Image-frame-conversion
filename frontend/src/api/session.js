import request from './request'

export function createSession(data) {
  return request.post('/api/sessions/', data)
}

export function getSessions() {
  return request.get('/api/sessions/')
}

export function getSession(id) {
  return request.get(`/api/sessions/${id}`)
}

export function updateSession(id, data) {
  return request.put(`/api/sessions/${id}`, data)
}

export function deleteSession(id) {
  return request.delete(`/api/sessions/${id}`)
}
