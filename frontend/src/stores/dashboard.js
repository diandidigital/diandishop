import { defineStore } from 'pinia'
import api from '../lib/api'

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    stats: null,
  }),
  actions: {
    async refresh() {
      const { data } = await api.get('/api/dashboard')
      this.stats = data
    },
  },
})
