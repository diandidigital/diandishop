<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import { useAuthStore } from '../stores/auth'
import { useProductsStore } from '../stores/products'

const dark = ref(false)
const auth = useAuthStore()
const products = useProductsStore()
const router = useRouter()

onMounted(async () => {
  await products.refresh()
})

const stockAlerts = computed(() => products.products.filter((p) => p.stock <= p.stock_alerte))

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
    <h2 class="mb-4 text-2xl font-semibold">Gestion stock</h2>
    <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <div v-for="product in stockAlerts" :key="product.id" class="card border-l-4 border-amber-500">
        <p class="font-semibold">{{ product.nom }}</p>
        <p class="text-sm">Stock: {{ product.stock }} / Alerte: {{ product.stock_alerte }}</p>
      </div>
    </div>
  </AppLayout>
</template>
