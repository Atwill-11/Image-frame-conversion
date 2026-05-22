import request from './request'

export function register(data) {
  return request.post('/api/auth/register', data)
}

export function login(data) {
  return request.post('/api/auth/login', data)
}

export function logout() {
  return request.post('/api/auth/logout')
}

export function getMe() {
  return request.get('/api/auth/me')
}

export function refreshToken() {
  return request.post('/api/auth/refresh-token')
}
