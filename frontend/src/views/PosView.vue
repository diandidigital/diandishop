<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import { useAuthStore } from '../stores/auth'
import { useProductsStore } from '../stores/products'
import { usePosStore } from '../stores/pos'

const dark = ref(false)
const auth = useAuthStore()
const products = useProductsStore()
const pos = usePosStore()
const router = useRouter()

onMounted(async () => {
  await products.refresh()
})

const toggleDark = () => {
  dark.value = !dark.value
  document.documentElement.classList.toggle('dark', dark.value)
}

const logout = async () => {
  await auth.logout()
  router.push('/login')
}

const total = computed(() => pos.total)
</script>

<template>
  <AppLayout @toggle-dark="toggleDark" @logout="logout">
    <h2 class="mb-4 text-2xl font-semibold">Point de vente</h2>
    <div class="grid gap-4 lg:grid-cols-3">
      <div class="lg:col-span-2 grid gap-3 sm:grid-cols-2">
        <button
          v-for="product in products.products"
          :key="product.id"
          class="card text-left"
          @click="pos.add(product)"
        >
          <p class="font-semibold">{{ product.nom }}</p>
          <p class="text-sm">Stock: {{ product.stock }}</p>
          <p class="text-emerald-600">{{ product.prix }} FCFA</p>
        </button>
      </div>
      <div class="card">
        <h3 class="mb-2 text-lg font-semibold">Panier</h3>
        <ul class="mb-3 space-y-1 text-sm">
          <li v-for="item in pos.cart" :key="item.id">{{ item.nom }} × {{ item.qte }}</li>
        </ul>
        <p class="mb-3 font-semibold">Total: {{ total }} FCFA</p>
        <div class="flex gap-2">
          <button class="btn-muted" @click="pos.clear">Vider</button>
          <button class="btn-primary" @click="pos.checkout">Encaisser</button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
