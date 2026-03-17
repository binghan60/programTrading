import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'
import { fetchStrategies } from '@/api/backtest'

function toDateStr(d) { return d.toISOString().slice(0, 10) }

export const useStrategyStore = defineStore('strategy', () => {
  // ── 策略清單 ──────────────────────────────────────────────────
  const strategies = ref([])
  const selectedId = ref('')
  const params     = ref({})   // 策略定義的指標參數

  const current = computed(() => strategies.value.find(s => s.id === selectedId.value))

  function onStrategyChange() {
    if (!current.value) return
    params.value = Object.fromEntries(
      current.value.params.map(p => [p.key, p.default ?? p.min ?? 0])
    )
  }

  // ── 停損停利 + 進階風控 ───────────────────────────────────────
  const rp = reactive({
    sl_pct:               5,
    tp_pct:               10,
    trailing_stop:        false,
    trailing_pct:         5,
    atr_stop:             false,
    atr_period:           14,
    atr_mult_raw:         20,    // 實際倍數 = atr_mult_raw / 10
    position_pct:         20,
    max_positions:        1,
    sizing_method:        'fixed',
    daily_dd_pct:         3,
    max_dd_pct:           15,
    max_consecutive_loss: 4,
  })

  const atrMult = computed(() => (rp.atr_mult_raw / 10).toFixed(1))

  // ── 回測區間 ──────────────────────────────────────────────────
  const startDate = ref(toDateStr(new Date(Date.now() - 365 * 24 * 3600 * 1000)))
  const endDate   = ref(toDateStr(new Date()))

  // ── 合併後的完整 params（送給 API 用） ───────────────────────
  const mergedParams = computed(() => ({
    ...params.value,
    sl_pct:               rp.sl_pct,
    tp_pct:               rp.tp_pct,
    trailing_stop:        rp.trailing_stop,
    trailing_pct:         rp.trailing_pct,
    atr_stop:             rp.atr_stop,
    atr_period:           rp.atr_period,
    atr_mult:             Number(atrMult.value),
    position_pct:         rp.position_pct,
    max_positions:        rp.max_positions,
    sizing_method:        rp.sizing_method,
    daily_dd_pct:         rp.daily_dd_pct,
    max_dd_pct:           rp.max_dd_pct,
    max_consecutive_loss: rp.max_consecutive_loss,
  }))

  // ── 排行執行觸發（sidebar → RankingView 跨元件溝通） ─────────
  const rankRunTrigger = ref(0)
  function triggerRankRun() { rankRunTrigger.value++ }

  // ── 初始化（幂等，只抓一次） ──────────────────────────────────
  let initialized = false
  async function init() {
    if (initialized) return
    initialized = true
    const list = await fetchStrategies()
    strategies.value = list
    selectedId.value = list[0]?.id ?? ''
    onStrategyChange()
  }

  return {
    strategies, selectedId, params, current,
    rp, atrMult,
    startDate, endDate,
    mergedParams,
    rankRunTrigger,
    onStrategyChange, init, triggerRankRun,
  }
})
