<script setup>
import { computed, onMounted, ref } from 'vue'
import { ArrowRight, ArrowUpRight, BadgeCheck, BookOpen, Edit3, Plus, Star, Trash2, UsersRound } from '@lucide/vue'
import api, { getErrorMessage, getStoredUser } from '../services/api'

const user = ref(getStoredUser())
const profile = ref(null)
const listings = ref([])
const loading = ref(true)
const error = ref('')
const profileOpen = ref(false)
const profileForm = ref({ name: '', bio: '', location: '' })
const saving = ref(false)

const myListings = computed(() => listings.value.filter((item) => item.user_id === user.value?.id))
const averageRating = computed(() => profile.value?.stats.average_rating ? `${profile.value.stats.average_rating} / 5` : '—')

async function load() {
  loading.value = true
  try {
    const [profileResponse, listingResponse] = await Promise.all([api.get('/profile'), api.get('/listings')])
    profile.value = profileResponse.data
    user.value = profile.value.user
    localStorage.setItem('skillswap_user', JSON.stringify(user.value))
    profileForm.value = { name: user.value.name, bio: user.value.bio, location: user.value.location }
    listings.value = listingResponse.data.listings
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  saving.value = true
  error.value = ''
  try {
    const { data } = await api.put('/profile', profileForm.value)
    user.value = data.user
    localStorage.setItem('skillswap_user', JSON.stringify(data.user))
    profileOpen.value = false
    await load()
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    saving.value = false
  }
}

async function removeListing(item) {
  if (!window.confirm(`Delete your ${item.skill.name} listing?`)) return
  try {
    await api.delete(`/listings/${item.id}`)
    listings.value = listings.value.filter((listing) => listing.id !== item.id)
  } catch (e) {
    error.value = getErrorMessage(e)
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-title">
      <div><div class="eyebrow">Your personal exchange</div><h1>Hey, {{ user?.name?.split(' ')[0] || 'friend' }}.</h1><p class="muted">A little progress, a lot of possibility.</p></div>
      <div class="action-row"><button class="button button-outline" @click="profileOpen = !profileOpen"><Edit3 :size="15" /> Edit profile</button><RouterLink class="button button-lime" to="/listings/new"><Plus :size="16" /> New listing</RouterLink></div>
    </div>
    <div v-if="error" class="error-box" style="margin-bottom:16px">{{ error }}</div>
    <div v-if="profileOpen" class="card profile-editor">
      <form class="profile-form" @submit.prevent="saveProfile">
        <div class="field"><label>Name</label><input v-model.trim="profileForm.name" required minlength="2" maxlength="100" /></div>
        <div class="field"><label>Location</label><input v-model.trim="profileForm.location" maxlength="120" placeholder="City, Country" /></div>
        <div class="field profile-bio"><label>About you</label><input v-model.trim="profileForm.bio" maxlength="500" placeholder="A little about what you enjoy learning…" /></div>
        <button class="button button-lime" :disabled="saving">{{ saving ? 'Saving…' : 'Save profile' }}</button>
      </form>
    </div>
    <div v-if="loading" class="empty-state"><span class="muted">Loading your workspace…</span></div>
    <template v-else-if="profile">
      <div class="stat-grid">
        <div class="card stat-card"><span><BookOpen :size="14" style="vertical-align:middle" /> Your listings</span><strong>{{ profile.stats.listings }}</strong></div>
        <div class="card stat-card"><span><UsersRound :size="14" style="vertical-align:middle" /> Active exchanges</span><strong>{{ profile.stats.active_exchanges }}</strong></div>
        <div class="card stat-card"><span><BadgeCheck :size="14" style="vertical-align:middle" /> Completed</span><strong>{{ profile.stats.completed_exchanges }}</strong></div>
        <div class="card stat-card"><span><Star :size="14" style="vertical-align:middle" /> Reputation</span><strong>{{ averageRating }} <small style="font:500 11px 'DM Sans';color:#8e91a0">({{ profile.stats.review_count }})</small></strong></div>
      </div>
      <section style="margin-top:43px">
        <div class="section-heading"><div><div class="eyebrow">Your shared knowledge</div><h2>Your listings</h2></div><RouterLink class="button button-outline button-small" to="/explore">Explore skills <ArrowRight :size="14" /></RouterLink></div>
        <div v-if="!myListings.length" class="card empty-state"><BookOpen :size="26" /><h3>Your story starts with a skill</h3><p>Offer what you know or tell us what you want to learn.</p><RouterLink class="button button-lime button-small" to="/listings/new">Create your first listing</RouterLink></div>
        <div v-else class="grid listing-grid">
          <article v-for="item in myListings" :key="item.id" class="card listing-card">
            <div style="display:flex;justify-content:space-between;align-items:center"><span :class="['badge', item.listing_type === 'Want' ? 'badge-violet' : '']">{{ item.listing_type === 'Offer' ? 'CAN TEACH' : 'WANTS TO LEARN' }}</span><span :class="['badge', item.moderation_status === 'approved' ? '' : item.moderation_status === 'rejected' ? 'badge-red' : 'badge-amber']">{{ item.moderation_status }}</span></div>
            <h3>{{ item.skill.name }}</h3><p>{{ item.description || 'Add a description to help others find you.' }}</p>
            <div class="listing-footer"><small class="muted">{{ item.proficiency_level }} · {{ item.skill.category }}</small><div class="action-row"><RouterLink class="icon-button" :to="`/listings/${item.id}/edit`" aria-label="Edit listing"><Edit3 :size="15" /></RouterLink><button class="icon-button" aria-label="Delete listing" @click="removeListing(item)"><Trash2 :size="15" /></button></div></div>
          </article>
        </div>
      </section>
      <div class="dashboard-lower">
        <div class="card welcome-card"><div class="eyebrow">Keep the momentum</div><h3>Every exchange starts with a conversation.</h3><p class="muted small">You have <strong style="color:white">{{ profile.stats.pending_requests }}</strong> pending requests waiting in your hub.</p><RouterLink class="button button-lime button-small" to="/requests">Open Request Hub <ArrowUpRight :size="14" /></RouterLink></div>
        <div class="card welcome-card"><div class="eyebrow">Your impact</div><h3>Knowledge is a two-way street.</h3><p class="muted small">{{ profile.stats.offers }} skill{{ profile.stats.offers === 1 ? '' : 's' }} offered · {{ profile.stats.wants }} skill{{ profile.stats.wants === 1 ? '' : 's' }} wanted</p><RouterLink class="text-link" to="/explore">Meet your community <ArrowRight :size="14" /></RouterLink></div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.profile-editor { padding: 18px; margin-bottom: 18px; }.profile-form { display: grid; grid-template-columns: 1fr 1fr 1.5fr auto; align-items: end; gap: 12px; }.profile-form .field { gap: 6px; }.dashboard-lower { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 30px; }.welcome-card { padding: 23px; }.welcome-card h3 { margin: 14px 0 7px; font-size: 18px; }.text-link { color: var(--lime); font-size: 12px; font-weight: 700; }
@media(max-width:680px) { .profile-form, .dashboard-lower { grid-template-columns: 1fr; } }
</style>
