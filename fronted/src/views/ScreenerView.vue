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
        <h3>選股大師</h3><p>請於左側面板設定條件 // 點擊個股以分析</p>
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
</style>
