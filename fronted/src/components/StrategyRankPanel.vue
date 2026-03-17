<template>
  <div class="rank-root tech-root">
    <div class="rank-main-tech">

      <div v-if="!results.length" class="empty-tech">
        <div class="spinner-tech"></div>
        <div class="loading-txt">初始化數據流...</div>
      </div>

      <template v-else>
        <!-- 摘要列 -->
        <div v-if="doneCount > 0" class="summary-grid-tech">
          <div class="sum-card-tech">
            <div class="sum-lbl">分析總數</div>
            <div class="sum-val">{{ doneCount }} <span class="sum-unit">檔</span></div>
          </div>
          <div class="sum-card-tech highlight" v-if="bestStock">
            <div class="sum-lbl">績效冠軍</div>
            <div class="sum-val">
              {{ bestStock.code }}
              <MetricValue :value="bestStock.metrics.total_return" suffix="%" showSign class="sum-sub" />
            </div>
          </div>
          <div class="sum-card-tech" v-if="avgReturn != null">
            <div class="sum-lbl">平均總報酬</div>
            <div class="sum-val">
              <MetricValue :value="avgReturn" suffix="%" showSign />
            </div>
          </div>
          <div class="sum-card-tech" v-if="winRateAvg != null">
            <div class="sum-lbl">平均勝率</div>
            <div class="sum-val">
              <MetricValue :value="winRateAvg" suffix="%" :precision="1" />
            </div>
          </div>
          <div class="sum-card-tech">
            <div class="sum-lbl">正報酬比例</div>
            <div class="sum-val pos">{{ positiveCount }}<span class="sum-unit">/</span>{{ doneCount }}</div>
          </div>
        </div>

        <!-- 進度列（執行中才顯示） -->
        <div v-if="running" class="progress-bar-wrap">
          <div class="progress-bar" :style="{ width: progressPct + '%' }" />
          <span class="progress-txt">
            {{ completedCount }} / {{ results.length }}
            <template v-if="eta != null">· 剩餘約 {{ eta }} 秒</template>
          </span>
        </div>

        <!-- 表格 -->
        <div class="table-wrap-tech">
          <table class="rt-tech">
            <thead>
              <tr>
                <th class="th-rank">排名</th>
                <th>代號</th>
                <th>名稱</th>
                <th>狀態</th>
                <th class="sortable" @click="setSort('total_return')">總報酬 % {{ si('total_return') }}</th>
                <th class="sortable" @click="setSort('annual_return')">年化 % {{ si('annual_return') }}</th>
                <th class="sortable" @click="setSort('max_drawdown')">最大回撤 {{ si('max_drawdown') }}</th>
                <th class="sortable" @click="setSort('win_rate')">勝率 % {{ si('win_rate') }}</th>
                <th class="sortable" @click="setSort('total_trades')">次數 {{ si('total_trades') }}</th>
                <th class="sortable" @click="setSort('sharpe_ratio')">夏普 {{ si('sharpe_ratio') }}</th>
                <th class="sortable" @click="setSort('profit_factor')">獲利因子 {{ si('profit_factor') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in sortedResults" :key="r.code" :class="['rt-row-tech', r.status, { top3: r.status === 'done' && i < 3 }]">
                <td class="td-rank">
                  <span v-if="r.status === 'done'" :class="['rb-tech', `r${i+1}`]">{{ i + 1 }}</span>
                  <span v-else class="muted">—</span>
                </td>
                <td class="td-code-tech clickable" @click="$emit('select-stock', r)">{{ r.code }}</td>
                <td class="td-name-tech clickable" @click="$emit('select-stock', r)">{{ r.name }}</td>
                <td>
                  <span :class="['sb-tech', r.status]">
                    <span v-if="r.status === 'running'" class="spin">◌</span>
                    {{ STATUS[r.status] }}
                  </span>
                </td>
                <td class="num-cell-tech">
                  <template v-if="r.metrics">
                    <MetricValue :value="r.metrics.total_return" suffix="%" showSign class="val-txt" />
                    <div class="mini-bar-wrap"><div class="mini-bar" :style="barStyle(r.metrics.total_return)" /></div>
                  </template>
                  <span v-else class="muted">—</span>
                </td>
                <td class="num-cell-tech"><MetricValue :value="r.metrics?.annual_return" suffix="%" showSign /></td>
                <td class="num-cell-tech"><MetricValue :value="r.metrics?.max_drawdown" suffix="%" inverse /></td>
                <td class="num-cell-tech"><MetricValue :value="r.metrics?.win_rate" suffix="%" :precision="1" /></td>
                <td class="num-cell-tech tc">{{ r.metrics ? r.metrics.total_trades : '—' }}</td>
                <td class="num-cell-tech"><MetricValue :value="r.metrics?.sharpe_ratio" /></td>
                <td class="num-cell-tech"><MetricValue :value="r.metrics?.profit_factor" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { runBacktest as apiRun } from '@/api/backtest'
import { searchStocks } from '@/api/stocks'
import { useStrategyStore } from '@/stores/strategy'
import MetricValue from '@/components/MetricValue.vue'

const CONCURRENCY = 5

const store = useStrategyStore()
const STATUS = { pending: '等待中', running: '執行中', done: '分析完成', error: '失敗' }
const results = ref([])
const running = ref(false)
const startTime = ref(null)
let cancelFlag = false

// ETA 計算用：每秒更新一次 ticker 觸發 computed 重算
const ticker = ref(0)
let tickInterval = null

const doneCount      = computed(() => results.value.filter(r => r.status === 'done').length)
const errCount       = computed(() => results.value.filter(r => r.status === 'error').length)
const completedCount = computed(() => doneCount.value + errCount.value)
const progressPct    = computed(() => results.value.length ? Math.round(completedCount.value / results.value.length * 100) : 0)
const doneItems      = computed(() => results.value.filter(r => r.status === 'done' && r.metrics))
const bestStock      = computed(() => doneItems.value.reduce((b, r) => r.metrics.total_return > (b?.metrics?.total_return ?? -Infinity) ? r : b, null))
const avgReturn      = computed(() => doneItems.value.length ? (doneItems.value.reduce((s, r) => s + r.metrics.total_return, 0) / doneItems.value.length) : null)
const winRateAvg     = computed(() => doneItems.value.length ? (doneItems.value.reduce((s, r) => s + r.metrics.win_rate, 0) / doneItems.value.length) : null)
const positiveCount  = computed(() => doneItems.value.filter(r => r.metrics.total_return > 0).length)

const eta = computed(() => {
  ticker.value // 觸發響應式依賴
  if (!startTime.value || !completedCount.value || !running.value) return null
  const elapsed = Date.now() - startTime.value
  const rate = completedCount.value / elapsed // items/ms
  const remaining = results.value.length - completedCount.value
  const secs = Math.round(remaining / rate / 1000)
  return secs > 0 ? secs : null
})

const sortKey = ref('total_return')
const sortAsc = ref(false)
function setSort(k) { if (sortKey.value === k) sortAsc.value = !sortAsc.value; else { sortKey.value = k; sortAsc.value = false } }
function si(k) { if (sortKey.value !== k) return '⇅'; return sortAsc.value ? '↑' : '↓' }
const sortedResults = computed(() => [...results.value].sort((a, b) => {
  const aDone = a.status === 'done', bDone = b.status === 'done'
  if (aDone && !bDone) return -1; if (!aDone && bDone) return 1
  const av = a.metrics?.[sortKey.value] ?? null; const bv = b.metrics?.[sortKey.value] ?? null
  if (av === null) return 1; if (bv === null) return -1
  return sortAsc.value ? av - bv : bv - av
}))

async function runAll() {
  if (!store.selectedId || running.value) return
  cancelFlag = false
  running.value = true
  startTime.value = Date.now()
  results.value = results.value.map(r => ({ ...r, status: 'pending', metrics: null }))

  let idx = 0
  const total = results.value.length

  async function worker() {
    while (!cancelFlag) {
      const i = idx++
      if (i >= total) break

      results.value.splice(i, 1, { ...results.value[i], status: 'running' })
      try {
        const payload = {
          code:        results.value[i].code,
          start:       store.startDate,
          end:         store.endDate,
          strategy_id: store.selectedId,
          params:      store.mergedParams,
        }
        const data = await apiRun(payload)
        results.value.splice(i, 1, {
          ...results.value[i],
          status:  data.error ? 'error' : 'done',
          metrics: data.error ? null : data.metrics,
        })
      } catch {
        results.value.splice(i, 1, { ...results.value[i], status: 'error', metrics: null })
      }
    }
  }

  await Promise.all(Array.from({ length: CONCURRENCY }, worker))
  running.value = false
  startTime.value = null
}

function doCancel() { cancelFlag = true; running.value = false }

function barStyle(ret) {
  const w = Math.min(Math.abs(ret), 50) / 50 * 50
  const c = ret >= 0 ? 'var(--stock-up)' : 'var(--stock-down)'
  return ret >= 0
    ? { left: '50%', width: w + '%', background: c, boxShadow: `0 0 8px ${c}` }
    : { right: '50%', width: w + '%', background: c, boxShadow: `0 0 8px ${c}` }
}

onMounted(async () => {
  tickInterval = setInterval(() => { if (running.value) ticker.value++ }, 1000)
  await store.init()
  const stocks = await searchStocks('')
  results.value = stocks.map(s => ({ ...s, status: 'pending', metrics: null }))
})

defineExpose({ runAll })
defineEmits(['select-stock'])
onBeforeUnmount(() => {
  clearInterval(tickInterval)
  doCancel()
})
</script>

<style scoped>
.rank-root { display: flex; height: 100%; background: var(--bg-main); overflow: hidden; }
.rank-main-tech { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.summary-grid-tech { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1px; background: var(--border-color); border-bottom: 1px solid var(--border-color); }
.sum-card-tech { background: var(--bg-nav); padding: 20px; text-align: center; }
.sum-card-tech.highlight { background: rgba(100, 181, 246, 0.03); }
.sum-lbl { font-size: 11px; font-weight: 800; color: var(--text-mut); margin-bottom: 8px; letter-spacing: 0.05em; }
.sum-val { font-size: 22px; font-weight: 900; color: #fff; font-family: 'JetBrains Mono', monospace; }
.sum-unit { font-size: 12px; color: var(--text-mut); margin-left: 6px; font-weight: 500; }
.sum-sub { font-size: 14px; margin-left: 8px; }

.progress-bar-wrap { position: relative; height: 28px; background: var(--bg-surface); border-bottom: 1px solid var(--border-color); flex-shrink: 0; }
.progress-bar { height: 100%; background: rgba(100, 181, 246, 0.15); border-right: 2px solid var(--accent-cyan); transition: width 0.4s ease; }
.progress-txt { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: var(--accent-cyan); letter-spacing: 0.08em; font-family: 'JetBrains Mono', monospace; }

.table-wrap-tech { flex: 1; overflow: auto; scrollbar-width: thin; scrollbar-color: var(--border-color) transparent; }
.rt-tech { width: 100%; border-collapse: collapse; font-size: 14px; }
.rt-tech thead th { position: sticky; top: 0; background: #0d1117; color: var(--text-mut); padding: 14px 18px; text-align: left; font-weight: 800; letter-spacing: 0.05em; border-bottom: 1px solid var(--border-color); z-index: 2; }
.rt-tech th.sortable { cursor: pointer; }
.rt-tech th.sortable:hover { color: var(--accent-cyan); }
.rt-row-tech td { padding: 14px 18px; border-bottom: 1px solid rgba(255, 255, 255, 0.02); color: var(--text-pri); }
.rt-row-tech:hover td { background: rgba(255, 255, 255, 0.02); }
.rb-tech { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 6px; font-weight: 900; font-family: 'JetBrains Mono', monospace; font-size: 13px; }
.rb-tech.r1 { background: var(--accent-cyan); color: #000; box-shadow: 0 0 10px rgba(100, 181, 246, 0.4); }
.rb-tech.r2 { border: 1px solid var(--accent-cyan); color: var(--accent-cyan); }
.rb-tech.r3 { border: 1px solid var(--accent-blue); color: var(--accent-blue); }
.td-code-tech { font-weight: 800; color: var(--accent-cyan); font-family: 'JetBrains Mono', monospace; font-size: 16px; }
.td-name-tech { color: var(--text-pri); font-weight: 500; font-size: 15px; }
.clickable { cursor: pointer; }
.clickable:hover { text-decoration: underline; }
.sb-tech { font-size: 11px; font-weight: 800; padding: 3px 10px; border-radius: 4px; letter-spacing: 0.05em; }
.sb-tech.pending { color: var(--text-mut); border: 1px solid var(--text-mut); }
.sb-tech.running { color: var(--accent-cyan); border: 1px solid var(--accent-cyan); }
.sb-tech.done    { color: var(--stock-up); border: 1px solid var(--stock-up); }
.sb-tech.error   { color: var(--stock-down); border: 1px solid var(--stock-down); }
.num-cell-tech { font-family: 'JetBrains Mono', monospace; font-weight: 600; text-align: right; font-size: 15px; }
.val-txt { display: block; margin-bottom: 4px; }
.mini-bar-wrap { height: 3px; background: rgba(255, 255, 255, 0.05); border-radius: 2px; position: relative; margin-top: 6px; }
.mini-bar { position: absolute; top: 0; height: 100%; border-radius: 2px; }
.empty-tech { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 24px; }
.spinner-tech { width: 48px; height: 48px; border: 3px solid rgba(100, 181, 246, 0.1); border-top-color: var(--accent-cyan); border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading-txt { font-size: 13px; font-weight: 800; color: var(--accent-cyan); letter-spacing: 0.2em; }
</style>
