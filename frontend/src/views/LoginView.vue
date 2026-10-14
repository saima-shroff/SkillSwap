<script setup>
import { ref } from 'vue'
import { ArrowRight, Sparkles } from '@lucide/vue'
import { useRouter } from 'vue-router'
import api, { getErrorMessage } from '../services/api'

const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    const { data } = await api.post('/auth/login', { email: email.value, password: password.value })
    localStorage.setItem('skillswap_token', data.token)
    localStorage.setItem('skillswap_user', JSON.stringify(data.user))
    router.push(data.user.roles.includes('Admin') ? '/admin' : '/dashboard')
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="page">
    <section class="card form-card">
      <div class="eyebrow"><Sparkles :size="13" /> Welcome back</div>
      <h1>Pick up where you left off.</h1>
      <p class="muted small">Your next great exchange is a hello away.</p>
      <form class="form-stack" @submit.prevent="submit">
        <div v-if="error" class="form-error">{{ error }}</div>
        <div class="field"><label for="email">Email address</label><input id="email" v-model.trim="email" type="email" autocomplete="email" required maxlength="255" placeholder="you@example.com" /></div>
        <div class="field"><label for="password">Password</label><input id="password" v-model="password" type="password" autocomplete="current-password" required maxlength="256" /></div>
        <button class="button button-lime" type="submit" :disabled="busy">{{ busy ? 'Signing in…' : 'Log in' }} <ArrowRight :size="16" /></button>
      </form>
      <p class="muted small" style="margin:22px 0 0">New to the circle? <RouterLink to="/register" style="color:var(--lime)">Create an account</RouterLink></p>
    </section>
  </div>
</template>
