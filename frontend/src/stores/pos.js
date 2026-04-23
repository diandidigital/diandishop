import { defineStore } from 'pinia'
import api from '../lib/api'

export const usePosStore = defineStore('pos', {
  state: () => ({
    cart: [],
  }),
  getters: {
    total: (state) => state.cart.reduce((acc, item) => acc + item.prix * item.qte, 0),
  },
  actions: {
    add(product) {
      const existing = this.cart.find((item) => item.id === product.id)
      if (existing) existing.qte += 1
      else this.cart.push({ id: product.id, nom: product.nom, prix: product.prix, qte: 1 })
    },
    clear() {
      this.cart = []
    },
    async checkout() {
      if (!this.cart.length) return
      await api.post('/api/ventes', {
        total: this.total,
        paiement: 'especes',
        monnaie: 0,
        items: this.cart.map((item) => ({
          produit_id: item.id,
          nom_produit: item.nom,
          prix_unitaire: item.prix,
          quantite: item.qte,
          sous_total: item.prix * item.qte,
        })),
      })
      this.clear()
    },
  },
})
