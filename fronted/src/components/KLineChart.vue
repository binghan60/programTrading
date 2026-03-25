<template>
  <div class="chart-wrap">
    <div class="toolbar">
      <button
        v-for="r in RANGES"
        :key="r.label"
        :class="['range-btn', { active: activeRange === r.label }]"
        @click="selectRange(r)"
      >
        {{ r.label }}
      </button>
    </div>

    <div class="chart-area">
      <div v-if="loading" class="overlay">載入中...</div>
      <div v-else-if="empty" class="overlay">無資料</div>
      <div ref="chartEl" class="chart" />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { createChart, CandlestickSeries, HistogramSeries } from 'lightweight-charts'
import { getKbars } from '@/api/stocks'
import { useMarketStore } from '@/stores/market'

const props = defineProps({ code: { type: String, required: true } })
const market = useMarketStore()

const RANGES = [
  { label: '1M',  months: 1   },
  { label: '3M',  months: 3   },
  { label: '6M',  months: 6   },
  { label: '1Y',  months: 12  },
  { label: '3Y',  months: 36  },
  { label: 'ALL', months: 999 },
]

// 台股配色方案
const COLORS = {
  up:     '#f23645',
  down:   '#089981',
  bg:     '#0f1117',
  text:   '#9098a1',
  grid:   '#1a1d27',
  border: '#2a2d3a',
}

const activeRange = ref('3M')
const loading     = ref(false)
const empty       = ref(false)
const chartEl     = ref(null)

let chart        = null
let candleSeries = null
let volSeries    = null
let loadAbortCtrl = null

// 連續整數索引 → 實際日期，用來消除週末/假日空洞
let dateIndexMap = []
// 目前可視範圍的左邊界 index，用於確保左緣一定顯示年份
let visibleFromIndex = 0

function initChart() {
  chart = createChart(chartEl.value, {
    localization: {
      timeFormatter: (index) => dateIndexMap[Math.round(index)] ?? '',
    },
    layout: {
      background: { color: COLORS.bg },
      textColor:  COLORS.text,
    },
    grid: {
      vertLines: { color: COLORS.grid },
      horzLines: { color: COLORS.grid },
    },
    crosshair: { mode: 1 },
    rightPriceScale: { borderColor: COLORS.border },
    timeScale: {
      borderColor:    COLORS.border,
      timeVisible:    false,
      secondsVisible: false,
      fixRightEdge:   true,
      rightOffset:    10,
      tickMarkFormatter: (index) => {
        const i   = Math.round(index)
        const cur = dateIndexMap[i]
        if (!cur) return ''
        const prev = i > 0 ? dateIndexMap[i - 1] : null
        // 左緣附近（±2）強制顯示年份，避免可視範圍不從 index 0 起始時年份消失
        const isNearLeftEdge = i >= visibleFromIndex - 1 && i <= visibleFromIndex + 2
        if (isNearLeftEdge || !prev || prev.slice(0, 4) !== cur.slice(0, 4)) return cur.slice(0, 4)
        if (prev.slice(5, 7) !== cur.slice(5, 7))          return cur.slice(5, 7) + '/' + cur.slice(2, 4)
        return cur.slice(5, 7) + '/' + cur.slice(8)
      },
    },
    width:  chartEl.value.clientWidth,
    height: chartEl.value.clientHeight,
  })

  candleSeries = chart.addSeries(CandlestickSeries, {
    upColor:         COLORS.up,
    downColor:       COLORS.down,
    borderUpColor:   COLORS.up,
    borderDownColor: COLORS.down,
    wickUpColor:     COLORS.up,
    wickDownColor:   COLORS.down,
  })

  volSeries = chart.addSeries(HistogramSeries, {
    color:        COLORS.up,
    priceFormat:  { type: 'volume' },
    priceScaleId: 'volume',
  })
  chart.priceScale('volume').applyOptions({
    scaleMargins: { top: 0.8, bottom: 0 },
  })

  // 使用者拖曳/縮放時同步更新左邊界，確保年份標籤正確顯示
  chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
    if (range) visibleFromIndex = Math.floor(range.from)
  })
}

async function loadData() {
  const stockCode = props.code
  if (!stockCode || !chart) return

  // 取消上一個進行中的請求
  loadAbortCtrl?.abort()
  loadAbortCtrl = new AbortController()
  const { signal } = loadAbortCtrl

  // 先查快取，有的話直接渲染不打 API
  if (market.kbarCache.has(stockCode)) {
    const cached = market.kbarCache.get(stockCode)
    updateChartData(cached)
    applyRange(activeRange.value)
    return
  }

  loading.value = true
  empty.value = false
  // 立刻清空舊資料，避免切換股票時短暫顯示前一支股票的年份標籤
  dateIndexMap = []
  candleSeries.setData([])
  volSeries.setData([])

  const fmt   = d => d.toISOString().slice(0, 10)
  const start = fmt(new Date(2020, 2, 2))
  const end   = fmt(new Date())

  try {
    const rows = await getKbars(stockCode, start, end, signal)

    if (!rows.length) {
      empty.value = true
      candleSeries.setData([])
      volSeries.setData([])
      return
    }

    market.kbarCache.set(stockCode, rows)
    updateChartData(rows)
    applyRange(activeRange.value)
  } catch (err) {
    // 主動取消不視為錯誤
    if (err.name === 'CanceledError' || err.name === 'AbortError') return
    empty.value = true
  } finally {
    loading.value = false
  }
}

function applyRange(label) {
  const total = dateIndexMap.length
  if (!total || !chart) return

  const range = RANGES.find(r => r.label === label)
  if (range.months >= 999) {
    visibleFromIndex = 0
    chart.timeScale().fitContent()
    return
  }

  const startDate = new Date()
  startDate.setMonth(startDate.getMonth() - range.months)
  const startStr  = startDate.toISOString().slice(0, 10)
  const fromIndex = dateIndexMap.findIndex(d => d >= startStr)
  visibleFromIndex = fromIndex === -1 ? 0 : fromIndex

  chart.timeScale().setVisibleLogicalRange({
    from: visibleFromIndex,
    to:   total - 1 + 10,
  })
}

function updateChartData(rows) {
  dateIndexMap = rows.map(r => r.date)

  candleSeries.setData(rows.map((r, i) => ({
    time:  i,
    open:  r.open,
    high:  r.high,
    low:   r.low,
    close: r.close,
  })))

  volSeries.setData(rows.map((r, i) => ({
    time:  i,
    value: r.volume,
    color: r.close >= r.open ? COLORS.up : COLORS.down,
  })))
}

function selectRange(r) {
  activeRange.value = r.label
  applyRange(r.label)
}

function onResize() {
  if (chart && chartEl.value) {
    chart.applyOptions({
      width:  chartEl.value.clientWidth,
      height: chartEl.value.clientHeight,
    })
  }
}

onMounted(() => {
  initChart()
  loadData()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  loadAbortCtrl?.abort()
  window.removeEventListener('resize', onResize)
  chart?.remove()
})

watch(() => props.code, () => {
  activeRange.value = '3M'
  loadData()
})
</script>

<style scoped>
.chart-wrap {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 8px;
}

.toolbar {
  display: flex;
  gap: 4px;
}

.range-btn {
  background: #1a1d27;
  color: #9098a1;
  border: 1px solid #2a2d3a;
  border-radius: 4px;
  padding: 4px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.range-btn:hover  { background: #252837; color: #fff; }
.range-btn.active { background: #2a4a7a; color: #fff; border-color: #3a6aaa; }

.chart-area {
  position: relative;
  flex: 1;
  min-height: 0;
}

.chart {
  width: 100%;
  height: 100%;
}

.overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 17, 23, 0.85);
  color: #9098a1;
  font-size: 14px;
  z-index: 10;
}
</style>
