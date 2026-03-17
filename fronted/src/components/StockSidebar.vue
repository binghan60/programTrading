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

/* ── 搜尋列 ─────────────────────────────────────────── */
.search-box-tech {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(180deg, rgba(0,0,0,0.3) 0%, transparent 100%);
}
.search-inner {
  display: flex; align-items: center;
  background: rgba(0,0,0,0.35);
  border: 1px solid var(--border-color);
  border-radius: 8px; padding: 4px 10px 4px 14px;
  transition: all 0.3s;
}
.search-inner:focus-within {
  border-color: rgba(77,184,204,0.4);
  background: rgba(77, 184, 204, 0.025);
}
.search-icon { display: flex; align-items: center; color: var(--accent-cyan); margin-right: 10px; opacity: 0.7; }
.svg-icon-small { width: 15px; height: 15px; }
.search-input-tech {
  width: 100%; background: none; border: none; color: var(--text-pri);
  padding: 9px 0; font-size: 15px; font-weight: 600;
  letter-spacing: 0.08em; outline: none; font-family: 'JetBrains Mono', monospace;
}
.search-input-tech::placeholder { color: var(--text-dim); }

.screener-btn {
  background: rgba(255,255,255,0.04); border: 1px solid var(--border-color);
  border-radius: 6px; padding: 5px 8px; cursor: pointer;
  transition: all 0.25s; font-size: 15px; margin-left: 8px; flex-shrink: 0;
}
.screener-btn:hover { background: rgba(77,184,204,0.08); border-color: rgba(77,184,204,0.3); }
.screener-btn.active {
  background: rgba(77,184,204,0.12); border-color: rgba(77,184,204,0.4);
}

/* ── 選股狀態列 ──────────────────────────────────────── */
.screening-status {
  background: rgba(0,212,255,0.06); padding: 8px 18px;
  border-bottom: 1px solid rgba(0,212,255,0.15);
  display: flex; justify-content: space-between; align-items: center;
}
.status-text { font-size: 11px; color: var(--accent-cyan); font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
.clear-screen-btn {
  background: none; border: none; color: var(--accent-cyan);
  cursor: pointer; font-size: 13px; opacity: 0.6;
  width: 22px; height: 22px; border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.clear-screen-btn:hover { opacity: 1; background: rgba(0,212,255,0.1); }

/* ── 股票列表 ─────────────────────────────────────────── */
.stock-list-tech { flex: 1; overflow-y: auto; list-style: none; }
.scroller { height: 100%; }

.stock-item-tech {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; height: 76px; cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.025);
  position: relative; transition: all 0.2s; overflow: hidden;
  box-sizing: border-box;
}
.stock-item-tech::before {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0;
  width: 2px; background: var(--accent-cyan); opacity: 0;
  transition: opacity 0.2s;
}
.stock-item-tech:hover::before { opacity: 0.4; }
.stock-item-tech:hover { background: rgba(0,212,255,0.03); }

.stock-item-tech.active {
  background: linear-gradient(90deg, rgba(0,212,255,0.07) 0%, transparent 100%);
}
.stock-item-tech.active::before { opacity: 0.6; }

.stock-info-main { display: flex; flex-direction: column; gap: 3px; z-index: 1; }
.stock-code-tech {
  font-size: 18px; font-weight: 800;
  color: var(--text-pri); font-family: 'JetBrains Mono', monospace;
  transition: color 0.2s;
}
.stock-item-tech.active .stock-code-tech {
  color: var(--accent-cyan);
}
.stock-name-tech { font-size: 14px; color: var(--text-mut); font-weight: 500; }

.stock-status-info { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; z-index: 1; }
.stock-ex-tech {
  font-size: 10px; color: var(--accent-blue); font-weight: 800;
  letter-spacing: 0.1em; text-transform: uppercase;
}
.data-badge {
  font-size: 9px; background: rgba(255,255,255,0.04); color: var(--text-dim);
  padding: 2px 6px; border-radius: 4px; border: 1px solid var(--border-color);
  letter-spacing: 0.05em;
}
.stock-item-tech.no-data { opacity: 0.5; }

.no-result-tech, .loading-item {
  padding: 60px 20px; text-align: center; color: var(--text-dim);
  font-size: 12px; letter-spacing: 0.2em; font-weight: 800; text-transform: uppercase;
}
.loading-item { animation: pulse 1.5s ease-in-out infinite; color: var(--accent-cyan); }
</style>
