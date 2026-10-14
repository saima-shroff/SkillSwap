<script setup>
import { computed, onMounted, ref } from 'vue'
import { Activity, ArrowUpRight, BadgeCheck, Check, ShieldCheck, UsersRound, X } from '@lucide/vue'
import api, { getErrorMessage } from '../services/api'

const tab = ref('overview')
const stats = ref(null)
const users = ref([])
const pending = ref([])
const loading = ref(true)
const error = ref('')
const filter = ref('')
const filteredUsers = computed(() => users.value.filter((user) => `${user.name} ${user.email}`.toLowerCase().includes(filter.value.toLowerCase())))

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [statsResult, usersResult, pendingResult] = await Promise.all([
      api.get('/admin/stats'), api.get('/admin/users'), api.get('/admin/listings/pending'),
    ])
    stats.value = statsResult.data
    users.value = usersResult.data.users
    pending.value = pendingResult.data.listings
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    loading.value = false
  }
}

async function setStatus(user) {
  error.value = ''
  try {
    const { data } = await api.put(`/admin/users/${user.id}/status`, { active: !user.active })
    users.value = users.value.map((item) => item.id === user.id ? { ...item, active: data.user.active } : item)
  } catch (e) {
    error.value = getErrorMessage(e)
  }
}

async function moderate(listing, approved) {
  error.value = ''
  try {
    await api.put(`/admin/listings/${listing.id}/approve`, { approved })
    pending.value = pending.value.filter((item) => item.id !== listing.id)
    if (stats.value) {
      stats.value.pending_offers = Math.max(0, stats.value.pending_offers - 1)
      if (approved) stats.value.active_offers += 1
    }
  } catch (e) {
    error.value = getErrorMessage(e)
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-title"><div><div class="eyebrow"><ShieldCheck :size="13" /> Platform operations</div><h1>Admin Control Center.</h1><p class="muted">A clear view of the community you're helping grow.</p></div><button class="button button-outline" @click="load"><Activity :size="15" /> Refresh</button></div>
    <div v-if="error" class="error-box" style="margin-bottom:17px">{{ error }}</div>
    <div v-if="loading" class="empty-state">Loading platform insights…</div>
    <template v-else>
      <div class="stat-grid">
        <div class="card stat-card"><span><UsersRound :size="14" style="vertical-align:middle" /> Total members</span><strong>{{ stats.total_users }}</strong><small class="muted">{{ stats.active_users }} active</small></div>
        <div class="card stat-card"><span><BadgeCheck :size="14" style="vertical-align:middle" /> Active offers</span><strong>{{ stats.active_offers }}</strong></div>
        <div class="card stat-card"><span><Activity :size="14" style="vertical-align:middle" /> Completed exchanges</span><strong>{{ stats.completed_exchanges }}</strong></div>
        <div class="card stat-card"><span><ShieldCheck :size="14" style="vertical-align:middle" /> Awaiting review</span><strong>{{ stats.pending_offers }}</strong></div>
      </div>
      <div class="admin-tabs" style="margin-top:37px">
        <button v-for="item in [['overview','Overview'],['users','Members'],['moderation','Moderation']]" :key="item[0]" :class="['admin-tab', { active: tab === item[0] }]" @click="tab = item[0]">{{ item[1] }}<span v-if="item[0] === 'moderation' && pending.length"> · {{ pending.length }}</span></button>
      </div>
      <section v-if="tab === 'overview'" class="admin-overview">
        <div class="card admin-welcome"><div class="eyebrow">Community health</div><h2>Small exchanges, meaningful impact.</h2><p class="muted">Your platform is helping people share practical skills, meet peers, and learn by doing.</p><div class="overview-metrics"><div><strong>{{ stats.reviews }}</strong><span>community reviews</span></div><div><strong>{{ stats.pending_offers }}</strong><span>offers to review</span></div><div><strong>{{ Math.round((stats.active_users / Math.max(stats.total_users, 1)) * 100) }}%</strong><span>members active</span></div></div></div>
        <div class="card quick-links"><div class="eyebrow">Quick actions</div><button class="quick-link" @click="tab = 'moderation'">Review pending offers <ArrowUpRight :size="15" /></button><button class="quick-link" @click="tab = 'users'">Manage member accounts <ArrowUpRight :size="15" /></button></div>
      </section>
      <section v-else-if="tab === 'users'" class="card table-card">
        <div class="section-heading"><div><div class="eyebrow">Member directory</div><h2>Members <span class="muted">({{ users.length }})</span></h2></div><input v-model="filter" class="search-input user-search" placeholder="Search name or email…" /></div>
        <div class="table-wrap"><table class="data-table"><thead><tr><th>Member</th><th>Joined</th><th>Role</th><th>Status</th><th>Action</th></tr></thead><tbody>
          <tr v-for="user in filteredUsers" :key="user.id"><td><strong>{{ user.name }}</strong><small class="muted" style="display:block;margin-top:4px">{{ user.email }}</small></td><td>{{ new Date(user.created_at).toLocaleDateString() }}</td><td>{{ user.roles.join(', ') }}</td><td><span :class="['badge', user.active ? '' : 'badge-red']">{{ user.active ? 'Active' : 'Suspended' }}</span></td><td><button :class="['button','button-small',user.active ? 'button-danger' : 'button-lime']" @click="setStatus(user)">{{ user.active ? 'Suspend' : 'Reactivate' }}</button></td></tr>
        </tbody></table></div>
        <div v-if="!filteredUsers.length" class="empty-state">No members match this search.</div>
      </section>
      <section v-else class="card table-card">
        <div class="section-heading"><div><div class="eyebrow">Offer review</div><h2>Moderation queue <span class="muted">({{ pending.length }})</span></h2></div></div>
        <div v-if="!pending.length" class="empty-state"><Check :size="26" /><h3>You're all caught up</h3><p>New skill offers will show here while they wait for review.</p></div>
        <div v-else class="table-wrap"><table class="data-table"><thead><tr><th>Skill</th><th>Member</th><th>Category</th><th>Proficiency</th><th>Submitted</th><th>Review</th></tr></thead><tbody>
          <tr v-for="listing in pending" :key="listing.id"><td><strong>{{ listing.skill.name }}</strong><small class="muted" style="display:block;margin-top:4px;max-width:250px;white-space:normal">{{ listing.description || 'No description provided.' }}</small></td><td>{{ listing.owner.name }}</td><td>{{ listing.skill.category }}</td><td>{{ listing.proficiency_level }}</td><td>{{ new Date(listing.created_at).toLocaleDateString() }}</td><td><div class="action-row"><button class="button button-small button-lime" aria-label="Approve listing" @click="moderate(listing, true)"><Check :size="14" /> Approve</button><button class="button button-small button-danger" aria-label="Reject listing" @click="moderate(listing, false)"><X :size="14" /> Reject</button></div></td></tr>
        </tbody></table></div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.admin-overview{display:grid;grid-template-columns:1.5fr .8fr;gap:16px}.admin-welcome,.quick-links,.table-card{padding:23px}.admin-welcome h2{font-size:26px;margin:14px 0 8px}.admin-welcome>p{max-width:480px;line-height:1.7;font-size:13px}.overview-metrics{display:flex;gap:44px;margin-top:26px}.overview-metrics strong{display:block;font:700 23px 'Manrope';margin-bottom:4px}.overview-metrics span{font-size:10px;color:var(--muted)}.quick-links{display:flex;flex-direction:column;gap:8px}.quick-links .eyebrow{margin-bottom:8px}.quick-link{display:flex;justify-content:space-between;align-items:center;padding:13px 0;color:#d5d6df;background:transparent;border:0;border-bottom:1px solid var(--line);font-size:12px;cursor:pointer}.quick-link:hover{color:var(--lime)}.table-card .section-heading{align-items:center}.user-search{max-width:230px}
@media(max-width:680px){.admin-overview{grid-template-columns:1fr}.overview-metrics{gap:18px;flex-wrap:wrap}.user-search{max-width:none}}
</style>
