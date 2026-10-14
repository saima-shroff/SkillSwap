<script setup>
import { computed, onMounted, ref } from 'vue'
import { ArrowUpRight, Compass, Search, Sparkles, UserRound } from '@lucide/vue'
import api, { getErrorMessage, getStoredUser } from '../services/api'

const listings = ref([])
const loading = ref(true)
const error = ref('')
const search = ref('')
const type = ref('')
const category = ref('')
const currentUser = ref(getStoredUser())
const requestListing = ref(null)
const ownOffers = ref([])
const selectedOffer = ref('')
const sending = ref(false)
const notice = ref('')

const categories = computed(() => [...new Set(listings.value.map((item) => item.skill.category))].sort())
const filteredListings = computed(() => listings.value.filter((item) => {
  const text = `${item.skill.name} ${item.skill.category} ${item.description} ${item.owner.name}`.toLowerCase()
  return (!search.value || text.includes(search.value.toLowerCase()))
    && (!type.value || item.listing_type === type.value)
    && (!category.value || item.skill.category === category.value)
    && item.user_id !== currentUser.value?.id
}))

async function loadListings() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/listings')
    listings.value = data.listings
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    loading.value = false
  }
}

async function openRequest(item) {
  notice.value = ''
  if (!localStorage.getItem('skillswap_token')) {
    window.location.href = '/login'
    return
  }
  try {
    const { data } = await api.get('/listings')
    ownOffers.value = data.listings.filter((listing) => listing.user_id === currentUser.value?.id && listing.listing_type === 'Offer')
    if (!ownOffers.value.length) {
      notice.value = 'Add an Offer listing to start an exchange.'
      return
    }
    requestListing.value = item
    selectedOffer.value = String(ownOffers.value[0].id)
  } catch (e) {
    notice.value = getErrorMessage(e)
  }
}

async function sendRequest() {
  sending.value = true
  try {
    await api.post('/requests', { offered_listing_id: Number(selectedOffer.value), requested_listing_id: requestListing.value.id })
    notice.value = 'Exchange request sent. You can follow it in your Request Hub.'
    requestListing.value = null
  } catch (e) {
    notice.value = getErrorMessage(e)
  } finally {
    sending.value = false
  }
}

onMounted(loadListings)
</script>

<template>
  <div class="page">
    <div class="page-title">
      <div><div class="eyebrow"><Compass :size="13" /> Explore the exchange</div><h1>Find your next teacher.</h1><p class="muted">A world of practical knowledge, shared person to person.</p></div>
      <RouterLink v-if="currentUser" class="button button-lime" to="/listings/new">Share a skill <ArrowUpRight :size="15" /></RouterLink>
    </div>
    <div v-if="notice" class="notice" style="margin-bottom:17px;display:flex;justify-content:space-between;align-items:center">
      <span>{{ notice }}</span><RouterLink v-if="notice.includes('Add an Offer')" to="/listings/new" class="button button-small button-lime">Create Offer</RouterLink>
    </div>
    <div class="toolbar">
      <div style="position:relative;flex:1"><Search :size="16" style="position:absolute;left:13px;top:13px;color:#7f8293" /><input v-model="search" class="search-input" style="padding-left:39px" placeholder="Search skills, people, or topics…" /></div>
      <select v-model="type" class="search-input"><option value="">All listings</option><option value="Offer">Skills offered</option><option value="Want">Skills wanted</option></select>
      <select v-model="category" class="search-input"><option value="">All categories</option><option v-for="item in categories" :key="item">{{ item }}</option></select>
    </div>
    <div v-if="error" class="error-box">{{ error }} <button class="button button-small" @click="loadListings">Retry</button></div>
    <div v-else-if="loading" class="empty-state"><Sparkles :size="25" /><p>Finding good people…</p></div>
    <div v-else-if="!filteredListings.length" class="card empty-state"><UserRound :size="28" /><h3>No matches just yet</h3><p>Try a different search, or be the first to share this skill.</p><RouterLink class="button button-lime button-small" to="/listings/new">Create a listing</RouterLink></div>
    <div v-else class="grid listing-grid">
      <article v-for="item in filteredListings" :key="item.id" class="card listing-card">
        <span :class="['badge', item.listing_type === 'Offer' ? '' : 'badge-violet']">{{ item.listing_type === 'Offer' ? 'CAN TEACH' : 'WANTS TO LEARN' }}</span>
        <h3>{{ item.skill.name }}</h3>
        <p>{{ item.description || 'Open to a friendly skill exchange.' }}</p>
        <div class="listing-footer">
          <div class="person"><span class="avatar">{{ item.owner.name.slice(0, 1).toUpperCase() }}</span><span>{{ item.owner.name }}<small class="muted" style="display:block;font-weight:400">{{ item.owner.location || item.skill.category }}</small></span></div>
          <button class="button button-small button-outline" @click="openRequest(item)">Connect <ArrowUpRight :size="13" /></button>
        </div>
      </article>
    </div>
    <div v-if="requestListing" class="modal-backdrop" @click.self="requestListing = null">
      <section class="card form-card request-modal">
        <div class="eyebrow">Start an exchange</div><h2>Offer something in return.</h2>
        <p class="muted small">Choose one of your skills to share for {{ requestListing.skill.name }}.</p>
        <div class="field" style="margin:20px 0"><label>Your Offer</label><select v-model="selectedOffer"><option v-for="offer in ownOffers" :key="offer.id" :value="String(offer.id)">{{ offer.skill.name }} · {{ offer.proficiency_level }}</option></select></div>
        <div class="action-row"><button class="button button-lime" :disabled="sending" @click="sendRequest">{{ sending ? 'Sending…' : 'Send request' }} <ArrowUpRight :size="14" /></button><button class="button button-outline" @click="requestListing = null">Cancel</button></div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop { position: fixed; inset: 0; z-index: 8; background: #08090eaa; display: grid; place-items: center; padding: 20px; backdrop-filter: blur(6px); }
.request-modal { margin: 0; }
</style>
