import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', component: () => import('../views/LandingView.vue') },
  { path: '/login', component: () => import('../views/LoginView.vue'), meta: { guest: true } },
  { path: '/register', component: () => import('../views/RegisterView.vue'), meta: { guest: true } },
  { path: '/dashboard', component: () => import('../views/DashboardView.vue'), meta: { auth: true } },
  { path: '/explore', component: () => import('../views/ExploreView.vue') },
  { path: '/requests', component: () => import('../views/RequestsView.vue'), meta: { auth: true } },
  { path: '/listings/new', component: () => import('../views/ListingFormView.vue'), meta: { auth: true } },
  { path: '/listings/:id/edit', component: () => import('../views/ListingFormView.vue'), meta: { auth: true } },
  { path: '/admin', component: () => import('../views/AdminView.vue'), meta: { auth: true, admin: true } },
]

const router = createRouter({ history: createWebHistory(), routes, scrollBehavior: () => ({ top: 0 }) })

router.beforeEach((to) => {
  const token = localStorage.getItem('skillswap_token')
  let user = null
  try {
    user = JSON.parse(localStorage.getItem('skillswap_user') || 'null')
  } catch {
    localStorage.removeItem('skillswap_user')
  }
  if ((to.meta.auth || to.meta.admin) && !token) return '/login'
  if (to.meta.admin && !user?.roles?.includes('Admin')) return '/dashboard'
  if (to.meta.guest && token) return '/dashboard'
  return true
})

export default router
