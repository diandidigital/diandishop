<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import { useAuthStore } from '../stores/auth'
import { useProductsStore } from '../stores/products'

const dark = ref(false)
const auth = useAuthStore()
const products = useProductsStore()
const router = useRouter()
const form = reactive({ nom: '', prix: 0, stock: 0, stock_alerte: 5, categorie_id: null })

onMounted(async () => {
  await products.refresh()
})

const addProduct = async () => {
  await products.addProduct(form)
  form.nom = ''
  form.prix = 0
  form.stock = 0
  form.stock_alerte = 5
  form.categorie_id = null
}

const toggleDark = () => {
  dark.value = !dark.value
  document.documentElement.classList.toggle('dark', dark.value)
}

const logout = async () => {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <AppLayout @toggle-dark="toggleDark" @logout="logout">
    <h2 class="mb-4 text-2xl font-semibold">Gestion produits</h2>
    <div class="card mb-4 grid gap-2 md:grid-cols-5">
      <input v-model="form.nom" class="input" placeholder="Nom">
      <input v-model.number="form.prix" class="input" type="number" placeholder="Prix">
      <input v-model.number="form.stock" class="input" type="number" placeholder="Stock">
      <select v-model.number="form.categorie_id" class="input">
        <option :value="null">Categorie</option>
        <option v-for="cat in products.categories" :key="cat.id" :value="cat.id">{{ cat.nom }}</option>
      </select>
      <button class="btn-primary" @click="addProduct">Ajouter</button>
    </div>
    <div class="card overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-left"><th>Nom</th><th>Prix</th><th>Stock</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="product in products.products" :key="product.id" class="border-t border-slate-200 dark:border-slate-700">
            <td>{{ product.nom }}</td>
            <td>{{ product.prix }}</td>
            <td>{{ product.stock }}</td>
            <td><button class="btn-muted" @click="products.deleteProduct(product.id)">Supprimer</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </AppLayout>
</template>
