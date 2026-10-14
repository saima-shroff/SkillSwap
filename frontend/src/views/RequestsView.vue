<script setup>
import { computed, onMounted, ref } from 'vue'
import { ArrowRightLeft, Check, Clock3, MessageSquareText, Star, X } from '@lucide/vue'
import api, { getErrorMessage, getStoredUser } from '../services/api'

const requests = ref([])
const reviews = ref([])
const loading = ref(true)
const error = ref('')
const activeFilter = ref('All')
const reviewTarget = ref(null)
const reviewForm = ref({ rating: 5, comment: '' })
const busy = ref(false)
const user = getStoredUser()
const filters = ['All', 'Pending', 'Accepted', 'Completed', 'Declined', 'Cancelled']
const filtered = computed(() => activeFilter.value === 'All' ? requests.value : requests.value.filter((item) => item.status === activeFilter.value))

async function load() {
  loading.value = true
  try {
    const [requestResponse, reviewResponse] = await Promise.all([api.get('/requests'), api.get('/reviews')])
    requests.value = requestResponse.data.requests
    reviews.value = reviewResponse.data.reviews
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    loading.value = false
  }
}

function hasReviewed(id) {
  return reviews.value.some((item) => item.exchange_id === id && item.reviewer.id === user?.id)
}

async function act(item, action) {
  error.value = ''
  try {
    const { data } = await api.put(`/requests/${item.id}`, { action })
    requests.value = requests.value.map((entry) => entry.id === item.id ? data.request : entry)
  } catch (e) {
    error.value = getErrorMessage(e)
  }
}

async function submitReview() {
  busy.value = true
  error.value = ''
  try {
    const { data } = await api.post('/reviews', { exchange_id: reviewTarget.value.id, ...reviewForm.value })
    reviews.value.unshift(data.review)
    reviewTarget.value = null
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-title"><div><div class="eyebrow"><ArrowRightLeft :size="13" /> Your exchange space</div><h1>Request Hub.</h1><p class="muted">Good exchanges happen one conversation at a time.</p></div></div>
    <div v-if="error" class="error-box" style="margin-bottom:16px">{{ error }}</div>
    <div class="admin-tabs request-tabs"><button v-for="filter in filters" :key="filter" :class="['admin-tab', { active: activeFilter === filter }]" @click="activeFilter = filter">{{ filter }} <span v-if="filter === 'Pending' && requests.filter((item) => item.status === 'Pending' && item.receiver_id === user?.id).length">· {{ requests.filter((item) => item.status === 'Pending' && item.receiver_id === user?.id).length }}</span></button></div>
    <div v-if="loading" class="empty-state">Loading your exchanges…</div>
    <div v-else-if="!filtered.length" class="card empty-state"><MessageSquareText :size="27" /><h3>It's quiet here — for now</h3><p>Explore the community and start a new exchange.</p><RouterLink class="button button-lime button-small" to="/explore">Explore skills <ArrowRightLeft :size="14" /></RouterLink></div>
    <article v-for="item in filtered" :key="item.id" class="card request-card">
      <div>
        <div class="request-meta"><span :class="['badge', item.status === 'Completed' ? '' : item.status === 'Declined' || item.status === 'Cancelled' ? 'badge-red' : item.status === 'Pending' ? 'badge-amber' : 'badge-violet']"><Clock3 v-if="item.status === 'Pending'" :size="12" />{{ item.status }}</span><span class="muted small">{{ new Date(item.created_at).toLocaleDateString() }}</span></div>
        <div class="request-exchange"><span>{{ item.sender_id === user?.id ? 'You' : item.sender.name }}</span><ArrowRightLeft :size="16" /><span>{{ item.receiver_id === user?.id ? 'You' : item.receiver.name }}</span></div>
        <div class="muted small">Offering <strong>{{ item.offered_listing.skill.name }}</strong> for <strong>{{ item.requested_listing.skill.name }}</strong></div>
        <div v-if="item.status === 'Accepted'" class="muted small" style="margin-top:9px">Completion confirmations: {{ Number(item.sender_completed) + Number(item.receiver_completed) }} / 2</div>
      </div>
      <div class="request-actions">
        <template v-if="item.status === 'Pending' && item.receiver_id === user?.id">
          <button class="button button-small button-lime" @click="act(item, 'accept')"><Check :size="14" /> Accept</button>
          <button class="button button-small button-danger" @click="act(item, 'decline')"><X :size="14" /> Decline</button>
        </template>
        <button v-else-if="item.status === 'Pending' && item.sender_id === user?.id" class="button button-small button-outline" @click="act(item, 'cancel')">Cancel request</button>
        <button v-else-if="item.status === 'Accepted' && !(item.sender_id === user?.id ? item.sender_completed : item.receiver_completed)" class="button button-small button-lime" @click="act(item, 'complete')"><Check :size="14" /> Confirm complete</button>
        <button v-else-if="item.status === 'Completed' && !hasReviewed(item.id)" class="button button-small button-outline" @click="reviewTarget = item; reviewForm = { rating: 5, comment: '' }"><Star :size="14" /> Leave a review</button>
        <span v-else-if="item.status === 'Completed'" class="muted small">Thanks for growing together ✨</span>
      </div>
    </article>
    <div v-if="reviewTarget" class="modal-backdrop" @click.self="reviewTarget = null">
      <section class="card form-card review-modal">
        <button class="icon-button close-modal" aria-label="Close" @click="reviewTarget = null"><X :size="18" /></button>
        <div class="eyebrow"><Star :size="13" /> Share the good</div><h2>How was your exchange?</h2>
        <div class="field" style="margin:18px 0"><label>Rating</label><select v-model.number="reviewForm.rating"><option :value="5">5 — Wonderful</option><option :value="4">4 — Great</option><option :value="3">3 — Good</option><option :value="2">2 — Could be better</option><option :value="1">1 — Not for me</option></select></div>
        <div class="field"><label>A few words (optional)</label><textarea v-model.trim="reviewForm.comment" maxlength="800" placeholder="What made the exchange meaningful?"></textarea></div>
        <button class="button button-lime" style="margin-top:18px" :disabled="busy" @click="submitReview">{{ busy ? 'Sharing…' : 'Share review' }} <Star :size="14" /></button>
      </section>
    </div>
  </div>
</template>

<style scoped>
.request-actions { display:flex;align-items:center;justify-content:end;gap:7px;flex-wrap:wrap; }.review-modal { position:relative; }.close-modal { position:absolute;right:16px;top:16px; }
@media(max-width:680px){.request-actions{justify-content:start}}
</style>
