<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowUpRight, Bell, Compass, LayoutDashboard, LogOut, Menu, ShieldCheck, Sparkles, X } from '@lucide/vue'
import { getStoredUser } from './services/api'

const route = useRoute()
const router = useRouter()
const menuOpen = ref(false)
const user = ref(getStoredUser())
const loggedIn = computed(() => Boolean(localStorage.getItem('skillswap_token')))
const isAdmin = computed(() => user.value?.roles?.includes('Admin'))
const currentYear = new Date().getFullYear()

watch(() => route.fullPath, () => {
  menuOpen.value = false
  user.value = getStoredUser()
})

function logout() {
  localStorage.removeItem('skillswap_token')
  localStorage.removeItem('skillswap_user')
  user.value = null
  router.push('/')
}
</script>

<template>
  <div class="app-shell">
    <div class="ambient ambient-one"></div>
    <div class="ambient ambient-two"></div>
    <header class="topbar">
      <RouterLink class="brand" to="/">
        <span class="brand-mark"><Sparkles :size="17" /></span>
        <span>skill<span class="brand-light">swap</span></span>
      </RouterLink>
      <button class="mobile-menu icon-button" aria-label="Toggle navigation" @click="menuOpen = !menuOpen">
        <X v-if="menuOpen" :size="20" /><Menu v-else :size="20" />
      </button>
      <nav :class="['nav-links', { 'nav-open': menuOpen }]">
        <RouterLink to="/explore"><Compass :size="16" /> Explore</RouterLink>
        <template v-if="loggedIn">
          <RouterLink to="/dashboard"><LayoutDashboard :size="16" /> Workspace</RouterLink>
          <RouterLink to="/requests"><Bell :size="16" /> Exchanges</RouterLink>
          <RouterLink v-if="isAdmin" to="/admin"><ShieldCheck :size="16" /> Admin</RouterLink>
          <div class="nav-user">
            <span class="avatar">{{ user?.name?.slice(0, 1)?.toUpperCase() || 'S' }}</span>
            <span>{{ user?.name || 'Member' }}</span>
            <button class="icon-button logout-button" aria-label="Log out" @click="logout"><LogOut :size="16" /></button>
          </div>
        </template>
        <template v-else>
          <RouterLink to="/login">Log in</RouterLink>
          <RouterLink class="button button-small button-lime" to="/register">Join the exchange <ArrowUpRight :size="15" /></RouterLink>
        </template>
      </nav>
    </header>
    <main>
      <RouterView />
    </main>
    <footer class="footer">
      <RouterLink class="brand footer-brand" to="/"><span class="brand-mark"><Sparkles :size="14" /></span> skill<span class="brand-light">swap</span></RouterLink>
      <span>Knowledge is better when it moves.</span>
      <span>© {{ currentYear }} SkillSwap</span>
    </footer>
  </div>
</template>
