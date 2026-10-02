<template>
  <div>
    <h1 class="brand">本周看板</h1>
    <p class="muted">周卡片网格 · round-robin 落位后可去「对调」申请交换</p>

    <div v-if="latest" class="regen-banner">
      <span class="chip coral">最近重生成 #{{ latest.id }}</span>
      <strong>{{ latest.reason }}</strong>
      <span class="muted">{{ latest.created_at }}</span>
    </div>

    <div style="display:flex;gap:8px;margin:12px 0">
      <button @click="generate(false)">生成周表</button>
      <button class="ghost" @click="load">刷新</button>
    </div>
    <div class="week-card" style="margin-bottom:12px">
      <label>强制重生成原因（ready 后再排必须填写）
        <input v-model="reason" placeholder="例如：排班冲突需重排" />
      </label>
      <button @click="generate(true)">强制重生成并覆写格位</button>
    </div>
    <p v-if="err" class="err">{{ friendly(err) }}</p>

    <div class="week-grid">
      <article v-for="d in days" :key="d" class="week-card">
        <header>Day {{ d }}</header>
        <div v-for="a in byDay(d)" :key="a.id">
          <span class="chip">{{ a.task_title }}</span>
          <span class="chip coral">{{ a.member_name }}</span>
        </div>
        <p v-if="!byDay(d).length" class="muted">空</p>
      </article>
    </div>

    <h2 class="brand" style="font-size:16px;margin-top:20px">重生成履历</h2>
    <ul class="list">
      <li v-for="h in history" :key="h.id">
        <span class="chip coral">#{{ h.id }}</span>
        <strong>{{ h.reason }}</strong>
        <span class="muted" style="margin-left:8px">{{ h.created_at }}</span>
      </li>
      <li v-if="!history.length" class="muted">暂无重生成履历（首次生成无需原因）</li>
    </ul>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
const assigns = ref([])
const history = ref([])
const latest = ref(null)
const days = [0,1,2,3,4,5,6]
const err = ref('')
const reason = ref('')
const weekId = 1
function byDay(d) { return assigns.value.filter(a => a.day === d) }
function friendly(m) {
  return ({
    regen_requires_force: '本周表已生成（ready）：普通再生成被拒绝，格表未改动；如需重排请填写原因后强制重生成。',
    regen_reason_required: '强制重生成必须填写非空原因。',
  })[m] || m
}
async function load() {
  err.value = ''
  try {
    const b = await api('/weeks/' + weekId + '/board')
    assigns.value = b.assignments || []
    latest.value = b.latest_regen
    history.value = await api('/weeks/' + weekId + '/regenerations')
  } catch (e) { err.value = e.message }
}
async function generate(force) {
  err.value = ''
  try {
    await api('/weeks/' + weekId + '/generate', {
      method: 'POST',
      body: JSON.stringify(force ? { force: true, reason: reason.value } : {}),
    })
    reason.value = ''
    await load()
  } catch (e) { err.value = e.message }
}
onMounted(load)
</script>
<style scoped>
.regen-banner {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  background: #fff3f1; border: 1px solid #f3c2ba; border-radius: 12px;
  padding: 8px 12px; margin: 8px 0;
}
</style>
