<template>
  <div class="bt-root tech-root">

    <!-- ── 左側設定欄 ── -->
    <aside class="bt-sidebar">
      <StrategyParamsSidebar :show-save="true" @run="runBacktest" />

      <button class="btn-run-bt" :disabled="loading || !store.selectedId" @click="runBacktest">
        <svg v-if="!loading" class="btn-svg" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        <span v-else class="spin-small">◌</span>
        {{ loading ? '回測執行中...' : '執行策略回測' }}
      </button>
    </aside>

    <!-- ── 右側結果區 ── -->
    <div class="bt-main">

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

onMounted(() => store.init())

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
})

function fmtNum(n) {
  if (n == null) return '—'
  return Number(n).toLocaleString('zh-TW')
}
</script>

<style scoped>
.bt-root { display: flex; height: 100%; overflow: hidden; background: var(--bg-main); }

/* ── 側欄 ── */
.bt-sidebar {
  width: 280px; min-width: 280px;
  background: var(--bg-nav); border-right: 1px solid var(--border-color);
  display: flex; flex-direction: column;
}

.btn-run-bt {
  margin: 20px;
  background: rgba(100, 181, 246, 0.1); color: var(--accent-cyan);
  border: 1px solid var(--accent-cyan);
  border-radius: 6px; padding: 14px; font-size: 15px; font-weight: 800;
  cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px;
  transition: all 0.2s;
}
.btn-run-bt:hover:not(:disabled) { background: var(--accent-cyan); color: #000; box-shadow: 0 0 20px rgba(100, 181, 246, 0.3); }
.btn-run-bt:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-svg { width: 18px; height: 18px; }
.spin-small { animation: spin 1s linear infinite; display: inline-block; font-size: 18px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── 主區域 ── */
.bt-main { flex: 1; min-height: 0; min-width: 0; overflow-y: auto; scrollbar-width: thin; }

.empty-hint-tech { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--text-mut); opacity: 0.6; }

/* 指標格 */
.metrics-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1px; background: var(--border-color); border-bottom: 1px solid var(--border-color); }
.m-card { background: var(--bg-nav); padding: 20px; text-align: center; }
.m-lbl { font-size: 11px; font-weight: 800; color: var(--text-mut); margin-bottom: 8px; letter-spacing: 0.05em; }
.m-val { font-size: 22px; font-weight: 900; color: #fff; font-family: 'JetBrains Mono', monospace; }
.m-unit { font-size: 12px; color: var(--text-mut); margin-left: 4px; }
.highlight { color: var(--accent-cyan); }

/* 進階指標列 */
.adv-metrics-bar { display: flex; background: rgba(0,0,0,0.2); padding: 12px 24px; border-bottom: 1px solid var(--border-color); gap: 32px; }
.am-item { display: flex; align-items: center; gap: 10px; }
.am-lbl { font-size: 12px; color: var(--text-mut); font-weight: 600; }
.am-val { font-size: 14px; font-weight: 800; color: #fff; font-family: 'JetBrains Mono', monospace; }

/* 圖表 */
.charts-container { padding: 20px; display: flex; flex-direction: column; gap: 20px; }
.chart-section { background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; }
.section-hd { padding: 12px 16px; background: rgba(255,255,255,0.02); border-bottom: 1px solid var(--border-color); font-size: 13px; font-weight: 800; color: var(--accent-blue); letter-spacing: 0.05em; }
.canvas-box { width: 100%; height: 340px; }
.canvas-box-sm { width: 100%; height: 140px; }

/* 交易明細 */
.trades-section { margin: 0 20px 40px; border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; }
.trades-table-wrap { max-height: 500px; overflow-y: auto; }
.t-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.t-table th { position: sticky; top: 0; background: #1a1d27; color: var(--text-mut); padding: 12px 16px; text-align: left; font-weight: 800; border-bottom: 1px solid var(--border-color); z-index: 1; }
.t-table td { padding: 14px 16px; border-bottom: 1px solid rgba(255,255,255,0.02); }

.buy-row td { background: rgba(255, 82, 82, 0.02); }
.sell-row td { background: rgba(76, 175, 80, 0.02); }

.action-badge { padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 800; }
.action-badge.buy { background: rgba(255, 82, 82, 0.1); color: var(--stock-up); border: 1px solid rgba(255, 82, 82, 0.2); }
.action-badge.sell { background: rgba(76, 175, 80, 0.1); color: var(--stock-down); border: 1px solid rgba(76, 175, 80, 0.2); }

.t-date { font-family: 'JetBrains Mono', monospace; font-size: 13px; color: var(--text-mut); }
.t-num { font-family: 'JetBrains Mono', monospace; text-align: right; font-weight: 600; }
.t-reason { color: var(--text-mut); font-size: 12px; }
</style>
