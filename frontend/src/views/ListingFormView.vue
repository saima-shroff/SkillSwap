<script setup>
import { computed, onMounted, ref } from 'vue'
import { ArrowLeft, Check, Sparkles } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'
import api, { getErrorMessage } from '../services/api'

const route = useRoute()
const router = useRouter()
const editing = computed(() => Boolean(route.params.id))
const form = ref({ listing_type: 'Offer', skill_name: '', category: '', proficiency_level: 'Intermediate', description: '' })
const error = ref('')
const busy = ref(false)
const resubmit = ref(false)

onMounted(async () => {
  if (!editing.value) return
  try {
    const { data } = await api.get(`/listings/${route.params.id}`)
    const item = data.listing
    form.value = {
      listing_type: item.listing_type,
      skill_id: item.skill.id,
      skill_name: item.skill.name,
      category: item.skill.category,
      proficiency_level: item.proficiency_level,
      description: item.description,
      moderation_status: item.moderation_status,
    }
  } catch (e) {
    error.value = getErrorMessage(e)
  }
})

async function submit() {
  busy.value = true
  error.value = ''
  try {
    const payload = { ...form.value }
    if (editing.value && resubmit.value) payload.resubmit = true
    await (editing.value
      ? api.put(`/listings/${route.params.id}`, payload)
      : api.post('/listings', payload))
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
      <div class="eyebrow"><Sparkles :size="13" /> Share a little knowledge</div>
      <h1>{{ editing ? 'Refine your listing.' : 'Put your skills out there.' }}</h1>
      <p class="muted small">Every great exchange starts with an honest conversation.</p>
      <div v-if="error" class="error-box" style="margin-top:18px">{{ error }}</div>
      <form class="form-stack" @submit.prevent="submit">
        <div class="field"><label>I'm here to…</label><select v-model="form.listing_type"><option value="Offer">Offer a skill</option><option value="Want">Learn a skill</option></select></div>
        <div class="field"><label for="skill">Skill name</label><input id="skill" v-model.trim="form.skill_name" required maxlength="120" placeholder="e.g. Product photography" /></div>
        <div class="field"><label for="category">Category</label><input id="category" v-model.trim="form.category" maxlength="80" placeholder="e.g. Design, Technology, Languages" /></div>
        <div class="field"><label>Proficiency level</label><select v-model="form.proficiency_level"><option>Beginner</option><option>Intermediate</option><option>Advanced</option><option>Expert</option></select></div>
        <div class="field"><label for="description">A little more about it</label><textarea id="description" v-model.trim="form.description" maxlength="1200" placeholder="What would you love to share or learn?"></textarea></div>
        <div v-if="form.listing_type === 'Offer'" class="notice">Offers go through a quick review before appearing in Explore. We’ll keep your listing hidden until it’s approved.</div>
        <div v-else class="notice">Want listings appear in Explore right away, so the community can find you.</div>
        <label v-if="editing && form.moderation_status === 'rejected' && form.listing_type === 'Offer'" class="resubmit-control">
          <input v-model="resubmit" type="checkbox" />
          <span><strong>Resubmit for review</strong><small class="muted">This Offer was declined and is still hidden. Check here to send the updated listing back to the Admin queue.</small></span>
        </label>
        <button class="button button-lime" type="submit" :disabled="busy">{{ busy ? 'Saving…' : editing ? 'Save changes' : 'Publish listing' }} <Check :size="16" /></button>
        <RouterLink class="muted small" to="/dashboard" style="text-align:center"><ArrowLeft :size="14" style="vertical-align:middle" /> Back to workspace</RouterLink>
      </form>
    </section>
  </div>
</template>

<style scoped>
.resubmit-control{display:flex;align-items:flex-start;gap:10px;padding:13px;border:1px solid #ffd38c33;background:#ffd38c0a;border-radius:10px;font-size:12px}.resubmit-control input{margin:2px 0 0;accent-color:#c4f680}.resubmit-control strong,.resubmit-control small{display:block}.resubmit-control small{margin-top:5px;line-height:1.5}
</style>
