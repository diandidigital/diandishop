import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import DashboardView from '../views/DashboardView.vue'
import PosView from '../views/PosView.vue'
import ProductsView from '../views/ProductsView.vue'
import StockView from '../views/StockView.vue'

const routes = [
  { path: '/login', component: LoginView, meta: { guest: true } },
  { path: '/register', component: RegisterView, meta: { guest: true } },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: DashboardView, meta: { role: 'admin' } },
  { path: '/pos', component: PosView, meta: { role: ['admin', 'caissiere'] } },
  { path: '/produits', component: ProductsView, meta: { role: 'admin' } },
  { path: '/stock', component: StockView, meta: { role: 'admin' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.user) {
    await auth.fetchMe()
  }

  if (to.meta.guest && auth.isAuthenticated) {
    return auth.user?.role === 'admin' ? '/dashboard' : '/pos'
  }

  if (!to.meta.guest && !auth.isAuthenticated) {
    return '/login'
  }

  const allowed = to.meta.role
  if (allowed) {
    const roles = Array.isArray(allowed) ? allowed : [allowed]
    if (!roles.includes(auth.user?.role)) return '/pos'
  }

  return true
})

export default router
