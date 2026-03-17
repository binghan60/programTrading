<template>
  <div class="page">
    <header class="content-header">
      <span class="mode-title-tech">策略排行</span>
    </header>
    <div class="view-body">
      <StrategyRankPanel ref="rankPanel" @select-stock="handleSelectAndJump" />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useMarketStore } from '@/stores/market'
import { useStrategyStore } from '@/stores/strategy'
import StrategyRankPanel from '@/components/StrategyRankPanel.vue'

const router   = useRouter()
const market   = useMarketStore()
const strategy = useStrategyStore()

const rankPanel = ref(null)

// 接收來自 sidebar 的執行觸發（透過 store 的 signal）
watch(() => strategy.rankRunTrigger, () => {
  rankPanel.value?.runAll()
})

function handleSelectAndJump(stock) {
  market.selectStock(stock)
  router.push('/trading')
}
</script>

<style scoped>
.page { display: flex; flex-direction: column; height: 100%; }
.view-body { flex: 1; overflow: hidden; position: relative; }
</style>
