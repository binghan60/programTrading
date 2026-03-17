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
        <h3>系統就緒</h3><p>數據通道穩定 // 等待選擇標的</p>
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
</style>
