import { defineStore } from 'pinia'
import api from '../lib/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    loading: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.user),
  },
  actions: {
    async fetchMe() {
      try {
        const { data } = await api.get('/api/auth/me')
        this.user = data.user || null
      } catch {
        this.user = null
      }
    },
    async login(payload) {
      await api.post('/api/auth/login', payload)
      await this.fetchMe()
    },
    async register(payload) {
      await api.post('/api/auth/register', payload)
      await this.fetchMe()
    },
    async logout() {
      await api.post('/api/auth/logout')
      this.user = null
    },
  },
})
