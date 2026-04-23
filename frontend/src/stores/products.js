import { defineStore } from 'pinia'
import api from '../lib/api'

export const useProductsStore = defineStore('products', {
  state: () => ({
    products: [],
    categories: [],
  }),
  actions: {
    async refresh() {
      const [productsRes, categoriesRes] = await Promise.all([
        api.get('/api/produits'),
        api.get('/api/categories'),
      ])
      this.products = productsRes.data
      this.categories = categoriesRes.data
    },
    async addProduct(payload) {
      await api.post('/api/produits', payload)
      await this.refresh()
    },
    async deleteProduct(id) {
      await api.delete(`/api/produits/${id}`)
      await this.refresh()
    },
  },
})
