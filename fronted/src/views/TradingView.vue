<template>
  <div class="page">
    <header class="content-header">
      <div class="header-left">
        <template v-if="market.selectedStock">
          <span class="stock-name">{{ market.selectedStock.name }}</span>
          <span class="stock-code">{{ market.selectedStock.code }}</span>
        </template>
        <span v-else class="mode-title-tech">交易終端</span>
      </div>
      <div v-if="market.selectedStock" class="tech-tabs">
        <button
          v-for="t in TABS" :key="t"
          :class="['tech-tab-btn', { active: activeTab === t }]"
          @click="activeTab = t"
        >{{ t }}</button>
      </div>
    </header>

    <div class="view-body">
      <div v-if="!market.selectedStock" class="empty-state-tech">
        <div class="es-ring-wrap">
          <div class="es-ring ring-outer"></div>
          <div class="es-ring ring-inner"></div>
          <div class="es-ring ring-dot"></div>
          <svg class="es-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
        </div>
        <h3>系統就緒</h3>
        <p>數據通道穩定 <span class="sep">//</span> 等待選擇標的</p>
        <div class="es-badges">
          <span class="es-badge">LIVE</span>
          <span class="es-badge muted">AWAITING INPUT</span>
        </div>
      </div>
      <KLineChart v-else-if="activeTab === 'K線圖表'" :code="market.selectedStock.code" />
      <BacktestPanel v-else :code="market.selectedStock.code" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useMarketStore } from '@/stores/market'
import KLineChart from '@/components/KLineChart.vue'
import BacktestPanel from '@/components/BacktestPanel.vue'

const market   = useMarketStore()
const TABS     = ['K線圖表', '策略回測']
const activeTab = ref('K線圖表')
</script>

<style scoped>
.page { display: flex; flex-direction: column; height: 100%; }
.view-body { flex: 1; overflow: hidden; position: relative; }

/* 空狀態動畫 */
.es-ring-wrap {
  position: relative; width: 100px; height: 100px;
  display: flex; align-items: center; justify-content: center; margin-bottom: 8px;
}
.es-ring {
  position: absolute; border-radius: 50%; border: 1px solid;
  animation: orbit-ring linear infinite;
}
.ring-outer {
  width: 100px; height: 100px;
  border-color: rgba(77, 184, 204, 0.1);
  border-top-color: rgba(77, 184, 204, 0.45);
  animation-duration: 4s;
}
.ring-inner {
  width: 68px; height: 68px;
  border-color: rgba(98, 114, 164, 0.1);
  border-bottom-color: rgba(98, 114, 164, 0.45);
  animation-duration: 3s; animation-direction: reverse;
}
.ring-dot {
  width: 36px; height: 36px;
  border-color: rgba(77, 184, 204, 0.08);
  border-right-color: rgba(77, 184, 204, 0.35);
  animation-duration: 2s;
}
.es-icon {
  width: 22px; height: 22px; color: var(--accent-cyan);
  opacity: 0.8;
  position: relative; z-index: 1;
}
.sep { color: var(--text-dim); margin: 0 6px; }
.es-badges { display: flex; gap: 8px; margin-top: 8px; }
.es-badge {
  font-size: 9px; font-weight: 900; letter-spacing: 0.15em;
  padding: 3px 10px; border-radius: 4px;
  border: 1px solid rgba(77,184,204,0.25);
  color: var(--accent-cyan); background: rgba(77,184,204,0.06);
}
.es-badge.muted { color: var(--text-dim); border-color: var(--border-color); background: transparent; }

/* ── Mobile (< 768px) ───────────────────────────────── */
@media (max-width: 767px) {
  /* header 改為垂直堆疊 */
  :deep(.content-header) {
    height: auto; min-height: 56px;
    flex-wrap: wrap; padding: 10px 14px; gap: 8px;
  }
  :deep(.header-left) { gap: 8px; }
  :deep(.stock-name)  { font-size: 20px; }
  :deep(.stock-code)  { font-size: 14px; }
  :deep(.mode-title-tech) { font-size: 18px; }
  :deep(.tech-tab-btn)    { padding: 7px 16px; font-size: 13px; }
}
</style>
