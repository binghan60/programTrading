<template>
  <div class="page">
    <header class="content-header">
      <div class="header-left">
        <template v-if="market.selectedStock">
          <span class="stock-name">{{ market.selectedStock.name }}</span>
          <span class="stock-code">{{ market.selectedStock.code }}</span>
        </template>
        <span v-else class="mode-title-tech">選股大師</span>
      </div>
    </header>
    <div class="view-body">
      <KLineChart
        v-if="market.selectedStock"
        :key="market.selectedStock.code"
        :code="market.selectedStock.code"
      />
      <div v-else class="empty-state-tech">
        <div class="es-ring-wrap">
          <div class="es-ring ring-outer"></div>
          <div class="es-ring ring-inner"></div>
          <svg class="es-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        </div>
        <h3>選股大師</h3>
        <p>請於左側面板設定條件 <span class="sep">//</span> 點擊個股以分析</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useMarketStore } from '@/stores/market'
import KLineChart from '@/components/KLineChart.vue'

const market = useMarketStore()
</script>

<style scoped>
.page { display: flex; flex-direction: column; height: 100%; }
.view-body { flex: 1; overflow: hidden; position: relative; }

.es-ring-wrap {
  position: relative; width: 90px; height: 90px;
  display: flex; align-items: center; justify-content: center; margin-bottom: 8px;
}
.es-ring {
  position: absolute; border-radius: 50%; border: 1px solid;
  animation: orbit-ring linear infinite;
}
.ring-outer {
  width: 90px; height: 90px;
  border-color: rgba(77, 184, 204, 0.1);
  border-top-color: rgba(77, 184, 204, 0.4);
  animation-duration: 5s;
}
.ring-inner {
  width: 58px; height: 58px;
  border-color: rgba(98, 114, 164, 0.1);
  border-bottom-color: rgba(98, 114, 164, 0.4);
  animation-duration: 3.5s; animation-direction: reverse;
}
.es-icon {
  width: 20px; height: 20px; color: var(--accent-cyan);
  opacity: 0.75; position: relative; z-index: 1;
}
.sep { color: var(--text-dim); margin: 0 6px; }

@media (max-width: 767px) {
  :deep(.content-header) { height: auto; min-height: 56px; padding: 10px 14px; }
  :deep(.stock-name)      { font-size: 20px; }
  :deep(.stock-code)      { font-size: 14px; }
  :deep(.mode-title-tech) { font-size: 18px; }
}
</style>
