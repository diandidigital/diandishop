<template>
  <div class="min-h-screen md:flex">
    <aside class="w-full bg-slate-800 p-4 text-white md:w-64">
      <div class="mb-6 flex items-center justify-between">
        <h1 class="text-lg font-semibold">🛒 DiandiShop</h1>
        <button class="btn-muted" @click="$emit('toggle-dark')">🌓</button>
      </div>
      <nav class="space-y-2">
        <RouterLink class="block rounded px-3 py-2 hover:bg-slate-700" to="/dashboard">Dashboard</RouterLink>
        <RouterLink class="block rounded px-3 py-2 hover:bg-slate-700" to="/pos">Caisse</RouterLink>
        <RouterLink class="block rounded px-3 py-2 hover:bg-slate-700" to="/produits">Produits</RouterLink>
        <RouterLink class="block rounded px-3 py-2 hover:bg-slate-700" to="/stock">Stock</RouterLink>
      </nav>
      <button class="btn mt-6 bg-red-500 text-white hover:bg-red-600" @click="$emit('logout')">Se deconnecter</button>
    </aside>
    <main class="flex-1 p-4 md:p-8">
      <slot />
    </main>
  </div>
</template>
