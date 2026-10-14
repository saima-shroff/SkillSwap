<script setup>
import { ref } from 'vue'
import { ArrowRight, Sparkles } from '@lucide/vue'
import { useRouter } from 'vue-router'
import api, { getErrorMessage } from '../services/api'

const router = useRouter()
const form = ref({ name: '', email: '', password: '' })
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await api.post('/auth/register', form.value)
    const { data } = await api.post('/auth/login', { email: form.value.email, password: form.value.password })
    localStorage.setItem('skillswap_token', data.token)
    localStorage.setItem('skillswap_user', JSON.stringify(data.user))
    router.push('/dashboard')
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
      <div class="eyebrow"><Sparkles :size="13" /> Your next chapter</div>
      <h1>Come as you are. Leave with more.</h1>
      <p class="muted small">Make a profile, share what you know, and find someone who knows what you want to learn.</p>
      <form class="form-stack" @submit.prevent="submit">
        <div v-if="error" class="form-error">{{ error }}</div>
        <div class="field"><label for="name">Your name</label><input id="name" v-model.trim="form.name" required minlength="2" maxlength="100" autocomplete="name" placeholder="How should we call you?" /></div>
        <div class="field"><label for="email">Email address</label><input id="email" v-model.trim="form.email" type="email" required maxlength="255" autocomplete="email" placeholder="you@example.com" /></div>
        <div class="field"><label for="password">Password <span class="muted">(12+ characters)</span></label><input id="password" v-model="form.password" type="password" required minlength="12" autocomplete="new-password" /></div>
        <button class="button button-lime" type="submit" :disabled="busy">{{ busy ? 'Creating your account…' : 'Create free account' }} <ArrowRight :size="16" /></button>
      </form>
      <p class="muted small" style="margin:22px 0 0">Already a member? <RouterLink to="/login" style="color:var(--lime)">Log in</RouterLink></p>
    </section>
  </div>
</template>
