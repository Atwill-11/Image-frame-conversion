import request from './request'

export function getPresetStyles() {
  return request.get('/api/styles/presets')
}

export function getCustomStyles() {
  return request.get('/api/styles/custom')
}

export function createCustomStyle(formData) {
  return request.post('/api/styles/custom', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function deleteCustomStyle(styleId) {
  return request.delete(`/api/styles/custom/${styleId}`)
}
