<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const form = reactive({ username: '', password: '' })
const error = ref('')

const submit = async () => {
  error.value = ''
  try {
    await auth.login(form)
    router.push(auth.user?.role === 'admin' ? '/dashboard' : '/pos')
  } catch (e) {
    error.value = e.response?.data?.message || 'Connexion impossible'
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center p-4">
    <div class="card w-full max-w-md">
      <h1 class="mb-4 text-2xl font-semibold">Connexion</h1>
      <p v-if="error" class="mb-3 text-sm text-red-500">{{ error }}</p>
      <form class="space-y-3" @submit.prevent="submit">
        <input v-model="form.username" class="input" placeholder="Nom d'utilisateur" required>
        <input v-model="form.password" type="password" class="input" placeholder="Mot de passe" required>
        <button class="btn-primary w-full" type="submit">Se connecter</button>
      </form>
      <RouterLink class="mt-3 inline-block text-sm text-emerald-600" to="/register">Creer un compte</RouterLink>
    </div>
  </div>
</template>
