<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import { useAuthStore } from '../stores/auth'
import { useDashboardStore } from '../stores/dashboard'

const dark = ref(false)
const auth = useAuthStore()
const store = useDashboardStore()
const router = useRouter()

onMounted(async () => {
  await store.refresh()
})

const toggleDark = () => {
  dark.value = !dark.value
  document.documentElement.classList.toggle('dark', dark.value)
}

const logout = async () => {
  await auth.logout()
  router.push('/login')
}

const stats = computed(() => store.stats || { nb_ventes: 0, total_jour: 0, nb_produits: 0, alertes_stock: 0 })
</script>

<template>
  <AppLayout @toggle-dark="toggleDark" @logout="logout">
    <h2 class="mb-4 text-2xl font-semibold">Dashboard</h2>
    <div class="grid gap-4 md:grid-cols-4">
      <div class="card"><p class="text-sm">Ventes du jour</p><p class="text-2xl font-bold">{{ stats.nb_ventes }}</p></div>
      <div class="card"><p class="text-sm">CA du jour</p><p class="text-2xl font-bold">{{ stats.total_jour }}</p></div>
      <div class="card"><p class="text-sm">Produits actifs</p><p class="text-2xl font-bold">{{ stats.nb_produits }}</p></div>
      <div class="card"><p class="text-sm">Alertes stock</p><p class="text-2xl font-bold">{{ stats.alertes_stock }}</p></div>
    </div>
  </AppLayout>
</template>
