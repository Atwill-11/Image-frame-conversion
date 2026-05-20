import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi, logout as logoutApi, getMe } from '../api/auth'
import { useSessionStore } from './session'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)

  async function login(username, password) {
    const sessionStore = useSessionStore()
    sessionStore.clearSessions()
    const res = await loginApi({ username, password })
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
  }

  async function register(username, password) {
    await registerApi({ username, password })
  }

  async function logout() {
    const sessionStore = useSessionStore()
    try {
      await logoutApi()
    } finally {
      token.value = ''
      user.value = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      sessionStore.clearSessions()
    }
  }

  async function fetchUser() {
    const res = await getMe()
    user.value = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
  }

  return { token, user, isLoggedIn, login, register, logout, fetchUser }
})
