<template>
  <div class="sidebar-tech-inner">
    <div class="search-box-tech">
      <div class="search-inner">
        <span class="search-icon">
          <svg class="svg-icon-small" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        </span>
        <input
          v-model="market.query"
          @input="market.onSearchInput"
          placeholder="搜尋股票代號..."
          class="search-input-tech"
        />
        <button 
          class="screener-btn" 
          :class="{ active: market.isScreening }"
          @click="market.screenUptrend" 
          title="選股大師：多頭趨勢 (HH/HL)"
        >
          📈
        </button>
      </div>
    </div>

    <div v-if="market.isScreening" class="screening-status">
      <span class="status-text">✨ 選股大師：多頭趨勢</span>
      <button class="clear-screen-btn" @click="market.fetchStocks('')">✕</button>
    </div>

    <RecycleScroller
      class="stock-list-tech scroller"
      :items="market.stocks"
      :item-size="76"
      key-field="code"
      v-slot="{ item: s }"
    >
      <div
        :class="['stock-item-tech', { active: market.selectedStock?.code === s.code, 'no-data': !s.has_data }]"
        @click="market.selectStock(s)"
      >
        <div class="stock-info-main">
          <span class="stock-code-tech">{{ s.code }}</span>
          <span class="stock-name-tech">{{ s.name }}</span>
        </div>
        <div class="stock-status-info">
          <span v-if="!s.has_data" class="data-badge">無資料</span>
          <span class="stock-ex-tech">{{ s.exchange }}</span>
        </div>
      </div>
    </RecycleScroller>
    
    <div v-if="market.stocks.length === 0 && (market.query || market.isScreening) && !market.loading" class="no-result-tech">
      {{ market.isScreening ? '目前無符合多頭結構的標的' : '未找到相關標的' }}
    </div>
    <div v-if="market.loading" class="loading-item">數據分析中...</div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useMarketStore } from '@/stores/market'

const market = useMarketStore()

onMounted(() => {
  if (market.stocks.length === 0) market.fetchStocks()
})
</script>

<style scoped>
.sidebar-tech-inner { width: 100%; height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.search-box-tech { padding: 15px 20px; border-bottom: 1px solid var(--border-color); background: rgba(0, 0, 0, 0.2); }
.search-inner { display: flex; align-items: center; background: #0d1117; border: 1px solid var(--border-color); border-radius: 6px; padding: 4px 10px 4px 14px; transition: all 0.3s; }
.search-inner:focus-within { border-color: var(--accent-cyan); box-shadow: 0 0 15px rgba(100, 181, 246, 0.1); }
.search-icon { display: flex; align-items: center; color: var(--accent-cyan); margin-right: 12px; }
.svg-icon-small { width: 16px; height: 16px; }
.search-input-tech { width: 100%; background: none; border: none; color: var(--text-pri); padding: 10px 0; font-size: 14px; font-weight: 700; letter-spacing: 0.1em; outline: none; }
.search-input-tech::placeholder { color: #4a5060; }

.screener-btn { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 4px; padding: 4px 8px; cursor: pointer; transition: all 0.2s; font-size: 16px; margin-left: 8px; }
.screener-btn:hover { background: rgba(100, 181, 246, 0.1); border-color: var(--accent-cyan); }
.screener-btn.active { background: var(--accent-cyan); border-color: var(--accent-cyan); box-shadow: 0 0 10px var(--accent-cyan); }

.screening-status { background: rgba(100, 181, 246, 0.1); padding: 8px 20px; border-bottom: 1px solid rgba(100, 181, 246, 0.2); display: flex; justify-content: space-between; align-items: center; }
.status-text { font-size: 12px; color: var(--accent-cyan); font-weight: 700; }
.clear-screen-btn { background: none; border: none; color: var(--accent-cyan); cursor: pointer; font-size: 14px; opacity: 0.7; }
.clear-screen-btn:hover { opacity: 1; }

.stock-list-tech { flex: 1; overflow-y: auto; list-style: none; scrollbar-width: thin; scrollbar-color: var(--accent-cyan) transparent; }

/* RecycleScroller specific */
.scroller { height: 100%; }

.stock-item-tech { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; height: 76px; cursor: pointer; border-bottom: 1px solid rgba(255, 255, 255, 0.03); position: relative; transition: all 0.2s; overflow: hidden; box-sizing: border-box; }
.stock-info-main { display: flex; flex-direction: column; gap: 4px; z-index: 1; }
.stock-code-tech { font-size: 18px; font-weight: 800; color: var(--text-pri); font-family: 'JetBrains Mono', monospace; }
.stock-name-tech { font-size: 14px; color: var(--text-mut); font-weight: 500; }
.stock-status-info { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; z-index: 1; }
.stock-ex-tech { font-size: 11px; color: var(--accent-blue); font-weight: 700; letter-spacing: 0.05em; }
.data-badge { font-size: 10px; background: rgba(255, 255, 255, 0.05); color: #4a5060; padding: 1px 4px; border-radius: 3px; border: 1px solid rgba(255, 255, 255, 0.1); }
.stock-item-tech.no-data { opacity: 0.6; }

.stock-item-tech:hover { background: rgba(255, 255, 255, 0.03); }
.stock-item-tech.active { background: rgba(100, 181, 246, 0.05); }
.stock-item-tech.active::after { content: ''; position: absolute; right: 0; top: 0; bottom: 0; width: 3px; background: var(--accent-cyan); box-shadow: 0 0 15px var(--accent-cyan); }
.stock-item-tech.active .stock-code-tech { color: var(--accent-cyan); text-shadow: 0 0 10px rgba(100, 181, 246, 0.4); }
.no-result-tech, .loading-item { padding: 60px 20px; text-align: center; color: #4a5060; font-size: 14px; letter-spacing: 0.2em; font-weight: 700; }
</style>
