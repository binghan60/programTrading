<template>
  <div class="bt-root tech-root">

    <!-- ── 左側設定欄 ── -->
    <aside v-show="btSidebarOpen" class="bt-sidebar">
      <StrategyParamsSidebar :show-save="true" @run="runBacktest" />

      <button class="btn-run-bt" :disabled="loading || !store.selectedId" @click="runBacktest">
        <svg v-if="!loading" class="btn-svg" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        <span v-else class="spin-small">◌</span>
        {{ loading ? '回測執行中...' : '執行策略回測' }}
      </button>
    </aside>

    <!-- ── 右側結果區 ── -->
    <div class="bt-main">

      <!-- 手機版：設定面板開關按鈕 -->
      <div class="mobile-sidebar-toggle">
        <button class="toggle-btn" @click="btSidebarOpen = !btSidebarOpen">
          <svg class="btn-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M9 9h6M9 13h4"/>
          </svg>
          {{ btSidebarOpen ? '收起設定' : '展開設定' }}
        </button>
      </div>

      <div v-if="!result && !loading" class="empty-hint-tech">
        <div class="empty-gfx-small"></div>
        <p>請設定策略參數後按「執行回測」</p>
      </div>

      <template v-if="result">

        <!-- 核心績效指標 -->
        <div class="metrics-grid">
          <div class="m-card">
            <div class="m-lbl">總報酬率</div>
            <div class="m-val">
              <MetricValue :value="result.metrics.total_return" suffix="%" showSign />
            </div>
          </div>
          <div class="m-card">
            <div class="m-lbl">最大回撤 (MDD)</div>
            <div class="m-val">
              <MetricValue :value="result.metrics.max_drawdown" suffix="%" inverse />
            </div>
          </div>
          <div class="m-card">
            <div class="m-lbl">勝率</div>
            <div class="m-val">
              <MetricValue :value="result.metrics.win_rate" suffix="%" :precision="1" />
            </div>
          </div>
          <div class="m-card">
            <div class="m-lbl">交易次數</div>
            <div class="m-val">{{ result.metrics.total_trades }} <span class="m-unit">次</span></div>
          </div>
          <div class="m-card">
            <div class="m-lbl">最終淨值</div>
            <div class="m-val highlight">{{ fmtNum(result.metrics.final_value) }}</div>
          </div>
        </div>

        <!-- 進階指標列 -->
        <div v-if="hasAdvanced" class="adv-metrics-bar">
          <div class="am-item">
            <span class="am-lbl">夏普比率</span>
            <MetricValue :value="result.metrics.sharpe_ratio" />
          </div>
          <div class="am-item">
            <span class="am-lbl">獲利因子</span>
            <MetricValue :value="result.metrics.profit_factor" />
          </div>
          <div class="am-item">
            <span class="am-lbl">年化報酬</span>
            <MetricValue :value="result.metrics.annual_return" suffix="%" showSign />
          </div>
          <div class="am-item">
            <span class="am-lbl">盈虧比</span>
            <span class="am-val">{{ result.metrics.rr_ratio?.toFixed(2) ?? '—' }}</span>
          </div>
        </div>

        <!-- 圖表區 -->
        <div class="charts-container">
          <div class="chart-section">
            <div class="section-hd">K線走勢與訊號</div>
            <div ref="candleEl" class="canvas-box" />
          </div>

          <div class="chart-section">
            <div class="section-hd">淨值曲線 (Equity Curve)</div>
            <div ref="equityEl" class="canvas-box-sm" />
          </div>
        </div>

        <!-- 交易明細 -->
        <div class="trades-section">
          <div class="section-hd">歷史交易明細（{{ result.trades.length }} 筆記錄）</div>
          <div class="trades-table-wrap">
            <table class="t-table">
              <thead>
                <tr>
                  <th>成交日期</th>
                  <th>操作</th>
                  <th>成交價格</th>
                  <th>數量 (張)</th>
                  <th>成交金額</th>
                  <th>毛利</th>
                  <th>報酬率</th>
                  <th>訊號來源</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="t in result.trades" :key="t.date + t.action" :class="t.action === 'BUY' ? 'buy-row' : 'sell-row'">
                  <td class="t-date">{{ t.date }}</td>
                  <td>
                    <span :class="['action-badge', t.action.toLowerCase()]">
                      {{ t.action === 'BUY' ? '買入' : '賣出' }}
                    </span>
                  </td>
                  <td class="t-num">{{ t.price.toFixed(2) }}</td>
                  <td class="t-num">{{ (t.shares / 1000).toFixed(t.shares % 1000 === 0 ? 0 : 1) }}</td>
                  <td class="t-num">{{ fmtNum(t.value) }}</td>
                  <td class="t-num">
                    <MetricValue :value="t.profit" />
                  </td>
                  <td class="t-num">
                    <MetricValue :value="t.profit_pct" suffix="%" showSign />
                  </td>
                  <td class="t-reason">{{ t.reason }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount, onMounted } from 'vue'
import { createChart, CandlestickSeries, HistogramSeries, LineSeries, createSeriesMarkers } from 'lightweight-charts'
import { runBacktest as apiRun } from '@/api/backtest'
import { useStrategyStore } from '@/stores/strategy'
import StrategyParamsSidebar from '@/components/StrategyParamsSidebar.vue'
import MetricValue from '@/components/MetricValue.vue'

const props = defineProps({ code: { type: String, required: true } })

const store   = useStrategyStore()
const loading = ref(false)
const result  = ref(null)

// 手機版：側欄預設收起
const btSidebarOpen = ref(true)
function syncBtSidebar() { btSidebarOpen.value = window.innerWidth >= 768 }

// 台股配色
const COLORS = {
  up:   '#f23645',
  down: '#089981',
}

// API 請求管理
let abortController = null

const hasAdvanced = computed(() => {
  const m = result.value?.metrics
  return m && (m.sharpe_ratio != null || m.profit_factor != null || m.annual_return != null)
})

onMounted(() => { store.init(); syncBtSidebar(); window.addEventListener('resize', syncBtSidebar) })

async function runBacktest() {
  if (!props.code || !store.selectedId || loading.value) return
  
  loading.value = true
  result.value  = null
  destroyCharts()

  if (abortController) abortController.abort()
  abortController = new AbortController()

  try {
    const data = await apiRun({
      code:        props.code,
      start:       store.startDate,
      end:         store.endDate,
      strategy_id: store.selectedId,
      params:      store.mergedParams,
    })
    
    if (data.error) {
      console.warn('Backtest error:', data.error)
      return
    }
    
    result.value = data
    await nextTick()
    buildCharts(data)
  } catch (err) {
    if (err.name !== 'AbortError') {
      console.error('Backtest failed:', err)
    }
  } finally {
    loading.value = false
  }
}

// ── 圖表構建 ─────────────────────────────────────────────────────────
const candleEl = ref(null)
const equityEl = ref(null)
let candleChart = null
let equityChart = null

function buildCharts(data) {
  const baseOpts = {
    layout:          { background: { color: '#0a0c12' }, textColor: '#b1bac4' },
    grid:            { vertLines: { color: 'rgba(255,255,255,0.03)' }, horzLines: { color: 'rgba(255,255,255,0.03)' } },
    rightPriceScale: { borderColor: 'rgba(255,255,255,0.1)' },
    timeScale:       { borderColor: 'rgba(255,255,255,0.1)', timeVisible: false },
    localization:    { dateFormat: 'yyyy/MM/dd' },
  }

  candleChart = createChart(candleEl.value, {
    ...baseOpts, crosshair: { mode: 1 },
    width: candleEl.value.clientWidth, height: 340,
  })

  const candleSeries = candleChart.addSeries(CandlestickSeries, {
    upColor: COLORS.up, downColor: COLORS.down,
    borderUpColor: COLORS.up, borderDownColor: COLORS.down,
    wickUpColor: COLORS.up, wickDownColor: COLORS.down,
  })
  candleSeries.setData(data.kbars.map(r => ({
    time: r.ts, open: r.open, high: r.high, low: r.low, close: r.close,
  })))

  const volSeries = candleChart.addSeries(HistogramSeries, {
    color: 'rgba(100, 181, 246, 0.3)', priceFormat: { type: 'volume' }, priceScaleId: 'volume',
  })
  candleChart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } })
  volSeries.setData(data.kbars.map(r => ({
    time: r.ts, value: r.volume,
    color: r.close >= r.open ? 'rgba(242, 54, 69, 0.3)' : 'rgba(8, 153, 129, 0.3)',
  })))

  createSeriesMarkers(candleSeries, data.trades.map(t => ({
    time:     t.date,
    position: t.action === 'BUY' ? 'belowBar' : 'aboveBar',
    color:    t.action === 'BUY' ? COLORS.up : COLORS.down,
    shape:    t.action === 'BUY' ? 'arrowUp' : 'arrowDown',
    text:     t.action === 'BUY' ? '買' : '賣',
  })))
  candleChart.timeScale().fitContent()

  equityChart = createChart(equityEl.value, {
    ...baseOpts,
    width: equityEl.value.clientWidth, height: 140,
  })
  equityChart.addSeries(LineSeries, { color: 'var(--accent-cyan)', lineWidth: 2 })
    .setData(data.equity_curve.map(e => ({ time: e.date, value: e.value })))
  equityChart.timeScale().fitContent()
}

function destroyCharts() {
  candleChart?.remove(); candleChart = null
  equityChart?.remove(); equityChart = null
}

watch(() => props.code, () => { 
  result.value = null
  destroyCharts() 
})

onBeforeUnmount(() => {
  destroyCharts()
  if (abortController) abortController.abort()
  window.removeEventListener('resize', syncBtSidebar)
})

function fmtNum(n) {
  if (n == null) return '—'
  return Number(n).toLocaleString('zh-TW')
}
</script>

<style scoped>
.bt-root { display: flex; height: 100%; overflow: hidden; }

/* ── 側欄 ── */
.bt-sidebar {
  width: 280px; min-width: 280px;
  background: rgba(5, 8, 16, 0.7);
  border-right: 1px solid var(--border-color);
  display: flex; flex-direction: column;
}

/* 執行按鈕 */
.btn-run-bt {
  margin: 16px;
  background: linear-gradient(135deg, rgba(0,212,255,0.12) 0%, rgba(129,140,248,0.12) 100%);
  color: var(--accent-cyan);
  border: 1px solid rgba(0, 212, 255, 0.4);
  border-radius: 8px; padding: 14px; font-size: 15px; font-weight: 800;
  cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px;
  transition: all 0.3s; letter-spacing: 0.05em; position: relative; overflow: hidden;
}
.btn-run-bt::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba(0,212,255,0.2), rgba(129,140,248,0.2));
  opacity: 0; transition: opacity 0.3s;
}
.btn-run-bt:hover:not(:disabled)::before { opacity: 1; }
.btn-run-bt:hover:not(:disabled) {
  border-color: rgba(77,184,204,0.6);
  transform: translateY(-1px);
}
.btn-run-bt:disabled { opacity: 0.35; cursor: not-allowed; }

.btn-svg { width: 18px; height: 18px; position: relative; z-index: 1; }
.spin-small { animation: spin 1s linear infinite; display: inline-block; font-size: 18px; position: relative; z-index: 1; }

/* ── 主區域 ── */
.bt-main { flex: 1; min-height: 0; min-width: 0; overflow-y: auto; scrollbar-width: thin; scrollbar-color: var(--border-color) transparent; }
.empty-hint-tech {
  height: 100%; display: flex; flex-direction: column;
  align-items: center; justify-content: center; color: var(--text-dim);
  font-size: 12px; letter-spacing: 0.15em; font-weight: 700; text-transform: uppercase; gap: 12px;
}

/* ── 指標格 ── */
.metrics-grid {
  display: grid; grid-template-columns: repeat(5, 1fr);
  gap: 1px; background: var(--border-color); border-bottom: 1px solid var(--border-color);
}
.m-card {
  background: rgba(8, 12, 20, 0.95); padding: 20px; text-align: center;
  position: relative; overflow: hidden; transition: background 0.3s;
}
.m-card::after {
  content: ''; position: absolute; top: 0; left: 20%; right: 20%; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,212,255,0.4), transparent);
}
.m-card:hover { background: rgba(0, 212, 255, 0.04); }

.m-lbl {
  font-size: 11px; font-weight: 800; color: var(--text-mut);
  margin-bottom: 10px; letter-spacing: 0.1em; text-transform: uppercase;
}
.m-val {
  font-size: 24px; font-weight: 900; color: var(--text-pri);
  font-family: 'JetBrains Mono', monospace;
}
.m-unit { font-size: 13px; color: var(--text-mut); margin-left: 4px; font-weight: 600; }
.highlight { color: var(--accent-cyan); }

/* ── 進階指標列 ── */
.adv-metrics-bar {
  display: flex; background: rgba(0,0,0,0.25);
  padding: 12px 24px; border-bottom: 1px solid var(--border-color); gap: 32px;
  flex-wrap: wrap;
}
.am-item { display: flex; align-items: center; gap: 10px; }
.am-lbl { font-size: 11px; color: var(--text-mut); font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase; }
.am-val { font-size: 15px; font-weight: 800; color: var(--text-pri); font-family: 'JetBrains Mono', monospace; }

/* ── 圖表 ── */
.charts-container { padding: 18px; display: flex; flex-direction: column; gap: 18px; }
.chart-section {
  background: rgba(8, 12, 20, 0.8);
  border: 1px solid var(--border-color); border-radius: 10px; overflow: hidden;
  position: relative;
}
.chart-section::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(77,184,204,0.15), rgba(98,114,164,0.15), transparent);
}
.section-hd {
  padding: 12px 18px;
  background: rgba(0,0,0,0.2);
  border-bottom: 1px solid var(--border-color);
  font-size: 11px; font-weight: 900; color: var(--accent-blue);
  letter-spacing: 0.12em; text-transform: uppercase;
  display: flex; align-items: center; gap: 8px;
}
.section-hd::before {
  content: ''; width: 5px; height: 5px; border-radius: 50%;
  background: var(--accent-blue); opacity: 0.7;
  flex-shrink: 0;
}
.canvas-box { width: 100%; height: 340px; }
.canvas-box-sm { width: 100%; height: 140px; }

/* ── 交易明細 ── */
.trades-section {
  margin: 0 18px 40px;
  border: 1px solid var(--border-color); border-radius: 10px; overflow: hidden;
  position: relative;
}
.trades-section::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(77,184,204,0.15), rgba(98,114,164,0.15), transparent);
}
.trades-table-wrap { max-height: 500px; overflow-y: auto; scrollbar-width: thin; scrollbar-color: var(--border-color) transparent; }
.t-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.t-table th {
  position: sticky; top: 0;
  background: rgba(10, 14, 24, 0.98);
  color: var(--text-mut); padding: 12px 16px; text-align: left;
  font-weight: 800; font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase;
  border-bottom: 1px solid var(--border-color); z-index: 1; white-space: nowrap;
}
.t-table td { padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.02); white-space: nowrap; }
.t-table tr:hover td { background: rgba(255,255,255,0.02); }

.buy-row  td { background: rgba(255, 71, 87, 0.02); }
.sell-row td { background: rgba(0, 214, 143, 0.02); }
.buy-row:hover  td { background: rgba(255, 71, 87, 0.04) !important; }
.sell-row:hover td { background: rgba(0, 214, 143, 0.04) !important; }

.action-badge { padding: 3px 10px; border-radius: 5px; font-size: 12px; font-weight: 900; letter-spacing: 0.05em; }
.action-badge.buy  { background: rgba(255,71,87,0.1);  color: var(--stock-up);   border: 1px solid rgba(255,71,87,0.25); }
.action-badge.sell { background: rgba(0,214,143,0.1);  color: var(--stock-down); border: 1px solid rgba(0,214,143,0.25); }

.t-date { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--text-mut); }
.t-num  { font-family: 'JetBrains Mono', monospace; text-align: right; font-weight: 600; }
.t-reason { color: var(--text-mut); font-size: 12px; }

/* ── 手機版展開設定按鈕（桌面隱藏） ─────────────────────── */
.mobile-sidebar-toggle { display: none; }
.toggle-btn {
  display: flex; align-items: center; gap: 8px;
  background: rgba(0,0,0,0.3); border: 1px solid var(--border-color);
  color: var(--accent-cyan); padding: 10px 18px; font-size: 13px;
  font-weight: 700; cursor: pointer; border-radius: 0;
  width: 100%; letter-spacing: 0.05em; transition: background 0.2s;
}
.toggle-btn:hover { background: rgba(77,184,204,0.06); }

/* ── Tablet (768-1023px) ─────────────────────────────── */
@media (max-width: 1023px) {
  .bt-sidebar { width: 240px; min-width: 240px; }
  .metrics-grid { grid-template-columns: repeat(3, 1fr); }
}

/* ── Mobile (< 768px) ───────────────────────────────── */
@media (max-width: 767px) {
  .bt-root { flex-direction: column; }

  .bt-sidebar {
    width: 100%; min-width: 0;
    max-height: 60vh; overflow-y: auto;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
    flex-shrink: 0;
  }

  .mobile-sidebar-toggle { display: block; border-bottom: 1px solid var(--border-color); }

  .bt-main { flex: 1; min-height: 0; }

  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
  .m-val { font-size: 18px; }

  .adv-metrics-bar { gap: 16px; padding: 10px 14px; flex-wrap: wrap; }
  .am-item { flex-basis: calc(50% - 8px); }

  .charts-container { padding: 10px; gap: 10px; }
  .canvas-box { height: 220px; }
  .canvas-box-sm { height: 100px; }

  .trades-section { margin: 0 10px 24px; }
  .trades-table-wrap { overflow-x: auto; }
  .t-table { min-width: 620px; }
  .t-table th, .t-table td { padding: 10px 10px; font-size: 12px; }
}
</style>
