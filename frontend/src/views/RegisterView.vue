<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const form = reactive({ nom: '', username: '', password: '', role: 'caissiere', setup_code: '' })
const error = ref('')

const submit = async () => {
  error.value = ''
  try {
    await auth.register(form)
    router.push(auth.user?.role === 'admin' ? '/dashboard' : '/pos')
  } catch (e) {
    error.value = e.response?.data?.message || 'Inscription impossible'
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center p-4">
    <div class="card w-full max-w-md">
      <h1 class="mb-4 text-2xl font-semibold">Inscription</h1>
      <p v-if="error" class="mb-3 text-sm text-red-500">{{ error }}</p>
      <form class="space-y-3" @submit.prevent="submit">
        <input v-model="form.nom" class="input" placeholder="Nom complet" required>
        <input v-model="form.username" class="input" placeholder="Nom d'utilisateur" required>
        <input v-model="form.password" type="password" class="input" placeholder="Mot de passe" required>
        <select v-model="form.role" class="input">
          <option value="caissiere">Caissiere</option>
          <option value="admin">Admin</option>
        </select>
        <input v-model="form.setup_code" class="input" placeholder="Code activation (premier admin)">
        <button class="btn-primary w-full" type="submit">S'inscrire</button>
      </form>
      <RouterLink class="mt-3 inline-block text-sm text-emerald-600" to="/login">Déjà un compte ?</RouterLink>
    </div>
  </div>
</template>
