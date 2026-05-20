import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSessions, createSession, deleteSession, updateSession } from '../api/session'

export const useSessionStore = defineStore('session', () => {
  const sessions = ref([])
  const currentSessionId = ref(null)

  async function fetchSessions() {
    const res = await getSessions()
    sessions.value = res.data.sessions
    if (!currentSessionId.value && sessions.value.length > 0) {
      currentSessionId.value = sessions.value[0].id
    }
  }

  async function addSession(name = '新会话') {
    const res = await createSession({ name })
    sessions.value.unshift(res.data)
    currentSessionId.value = res.data.id
  }

  async function removeSession(id) {
    await deleteSession(id)
    sessions.value = sessions.value.filter((s) => s.id !== id)
    if (currentSessionId.value === id) {
      currentSessionId.value = sessions.value.length > 0 ? sessions.value[0].id : null
    }
  }

  async function renameSession(id, name) {
    const res = await updateSession(id, { name })
    const idx = sessions.value.findIndex((s) => s.id === id)
    if (idx !== -1) {
      sessions.value[idx] = res.data
    }
  }

  function setCurrentSession(id) {
    currentSessionId.value = id
  }

  return { sessions, currentSessionId, fetchSessions, addSession, removeSession, renameSession, setCurrentSession }
})
