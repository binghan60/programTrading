<template>
  <div class="screener-root tech-root">
    <div class="grid-bg"></div>
    
    <div class="screener-header">
      <div class="header-info">
        <h2 class="title-main">選股大師 <span class="badge-beta">PRO</span></h2>
        <p class="subtitle">基於市場結構分析，自動識別趨勢轉折與多頭結構</p>
      </div>
      <button 
        class="action-btn-main" 
        :disabled="market.loading" 
        @click="runScan"
      >
        <span v-if="market.loading" class="spin">◌</span>
        <span v-else>🚀</span>
        {{ market.loading ? '正在掃描全市場...' : '開始趨勢掃描' }}
      </button>
    </div>

    <div class="screener-body">
      <!-- 策略選單 -->
      <div class="form-group-tech" style="margin-bottom: 24px;">
        <div class="label-row">
          <label for="strategy-select" class="lbl-tech">選股策略</label>
          <div class="info-icon-wrap">
            <svg class="info-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <div class="tooltip">{{ currentStrategyDescription }}</div>
          </div>
        </div>
        <div class="select-wrapper-tech">
          <select id="strategy-select" v-model="selectedStrategy" class="select-tech">
            <option v-for="strategy in strategies" :key="strategy.id" :value="strategy.id">
              {{ strategy.name }}
            </option>
          </select>
        </div>
      </div>

      <!-- 結果列表 -->
      <div v-if="market.loading" class="loading-state">
        <div class="radar-scan"></div>
        <div class="scan-text">正在分析 1,976 檔標的之 K 線結構...</div>
      </div>

      <div v-else-if="market.isScreening && market.stocks.length === 0" class="empty-results">
        <div class="empty-icon">🔍</div>
        <p>當前市場暫無符合標準 HH/HL 結構的標的</p>
        <button class="reset-btn" @click="market.fetchStocks('')">重新整理</button>
      </div>

      <div v-else-if="market.isScreening" class="stock-list-tech">
        <div 
          v-for="s in market.stocks" 
          :key="s.code" 
          :class="['stock-item-tech', { active: props.selectedStock?.code === s.code }]"
          @click="selectAndGo(s)"
        >
          <div class="stock-info-main">
            <span class="stock-code-tech">{{ s.code }}</span>
            <span class="stock-name-tech">{{ s.name }}</span>
          </div>
          <div class="stock-status-info">
            <span class="stock-ex-tech">{{ s.exchange }}</span>
          </div>
        </div>
      </div>

      <div v-else class="welcome-state">
        <div class="welcome-gfx">
          <div class="orb"></div>
        </div>
        <h3>準備好挖掘強勢股了嗎？</h3>
        <p>點擊上方按鈕開始全市場數據掃描</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useMarketStore } from '@/stores/market'

const props = defineProps({
  selectedStock: Object,
})

const market = useMarketStore()
const emit = defineEmits(['select-stock'])

// --- Strategy Management ---
const strategies = ref([
  { 
    id: 'hh_hl', 
    name: '多頭結構 (HH/HL)',
    description: '篩選條件：高點越來越高 (Higher High) 且 低點越來越高 (Higher Low)。這是技術分析中最經典的健康上升趨勢。'
  },
  // { id: 'some_other', name: '未來策略範例', description: '另一個策略的描述' }
])
const selectedStrategy = ref('hh_hl')

const currentStrategyDescription = computed(() => {
  return strategies.value.find(s => s.id === selectedStrategy.value)?.description
})
// --- End Strategy Management ---

function runScan() {
  if (selectedStrategy.value === 'hh_hl') {
    market.screenUptrend()
  }
  // In the future, you could add:
  // else if (selectedStrategy.value === 'some_other') {
  //   market.screenOther()
  // }
}

function selectAndGo(s) {
  emit('select-stock', s)
}
</script>

<style scoped>
/* MODIFIED FOR SIDEBAR */
.screener-root { display: flex; flex-direction: column; height: 100%; position: relative; overflow: hidden; background: transparent; /* Changed from #05070a */ }
.grid-bg { display: none; /* Hide grid in sidebar */ }

.screener-header { 
  padding: 20px; /* Reduced padding */
  border-bottom: 1px solid var(--border-color); 
  display: flex; 
  flex-direction: column; /* Stack vertically */
  align-items: flex-start; /* Align to left */
  gap: 16px; /* Add gap between items */
  z-index: 10; 
  background: rgba(8, 10, 15, 0.8); 
  backdrop-filter: blur(10px); 
}
.title-main { 
  font-size: 22px; /* Reduced font size */
  font-weight: 900; 
  color: #fff; 
  margin-bottom: 0; /* Removed margin */
  letter-spacing: 0.05em; 
  display: flex; 
  align-items: center; 
  gap: 12px; /* Reduced gap */
}
.badge-beta { font-size: 10px; background: var(--accent-cyan); color: #000; padding: 2px 6px; border-radius: 4px; vertical-align: middle; }
.subtitle { color: var(--text-mut); font-size: 13px; line-height: 1.5; }

.action-btn-main { 
  background: var(--accent-cyan); 
  color: #000; 
  border: none; 
  padding: 12px 16px; /* Reduced padding */
  width: 100%; /* Make full width */
  border-radius: 6px; /* Adjusted border-radius */
  font-weight: 900; 
  font-size: 14px; /* Reduced font size */
  cursor: pointer; 
  transition: all 0.3s; 
  box-shadow: 0 0 20px rgba(100, 181, 246, 0.2); 
  display: flex; 
  align-items: center;
  justify-content: center; /* Center text/icon */
  gap: 10px; 
}
.action-btn-main:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 0 30px rgba(100, 181, 246, 0.4); }
.action-btn-main:disabled { opacity: 0.6; cursor: not-allowed; }

.screener-body { 
  flex: 1; 
  overflow-y: auto; 
  /* Adjusted padding to remove horizontal space for the list */
  padding: 20px 0 20px 20px; 
  z-index: 5; 
  display: flex;
  flex-direction: column;
}

.form-group-tech {
  padding-right: 20px; /* Add back padding for form elements */
}

/* --- Added styles for list, copied from StockSidebar --- */
.stock-list-tech { 
  flex: 1; 
  overflow-y: auto; 
  list-style: none; 
  scrollbar-width: thin; 
  scrollbar-color: var(--accent-cyan) transparent;
  padding-right: 20px; /* Add padding for the scrollbar */
}
.stock-item-tech { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; height: 76px; cursor: pointer; border-bottom: 1px solid rgba(255, 255, 255, 0.03); position: relative; transition: all 0.2s; overflow: hidden; box-sizing: border-box; margin-right: -20px; /* Counteract parent padding */ padding-right: 40px; }
.stock-info-main { display: flex; flex-direction: column; gap: 4px; z-index: 1; }
.stock-code-tech { font-size: 18px; font-weight: 800; color: var(--text-pri); font-family: 'JetBrains Mono', monospace; }
.stock-name-tech { font-size: 14px; color: var(--text-mut); font-weight: 500; }
.stock-status-info { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; z-index: 1; }
.stock-ex-tech { font-size: 11px; color: var(--accent-blue); font-weight: 700; letter-spacing: 0.05em; }
.stock-item-tech:hover { background: rgba(255, 255, 255, 0.03); }
.stock-item-tech.active { background: rgba(100, 181, 246, 0.05); }
.stock-item-tech.active::after { content: ''; position: absolute; right: 0; top: 0; bottom: 0; width: 3px; background: var(--accent-cyan); box-shadow: 0 0 15px var(--accent-cyan); }
.stock-item-tech.active .stock-code-tech { color: var(--accent-cyan); text-shadow: 0 0 10px rgba(100, 181, 246, 0.4); }
/* --- End copied styles --- */


.loading-state, .welcome-state { height: auto; min-height: 300px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 20px; flex: 1; }
.radar-scan { width: 80px; height: 80px; }
.scan-text { font-size: 12px; }

.orb { width: 80px; height: 80px; }

.empty-results { text-align: center; padding: 40px 20px; color: var(--text-mut); flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.empty-icon { font-size: 32px; margin-bottom: 16px; }
.reset-btn { margin-top: 16px; padding: 8px 20px; }

.spin { display: inline-block; animation: spin 1s linear infinite; font-size: 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* --- Added styles for form elements --- */
.form-group-tech {
  margin-bottom: 20px;
}
.lbl-tech {
  font-size: 12px;
  color: var(--text-mut);
  font-weight: 700;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
  display: block;
}
.select-wrapper-tech {
  position: relative;
}
.select-wrapper-tech::after {
  content: '▼';
  font-size: 12px;
  color: var(--accent-cyan);
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}
.select-tech {
  width: 100%;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-pri);
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 700;
  appearance: none;
  -webkit-appearance: none;
  cursor: pointer;
}
.select-tech:focus {
  outline: none;
  border-color: var(--accent-cyan);
  box-shadow: 0 0 10px rgba(100, 181, 246, 0.1);
}
.label-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.label-row .lbl-tech {
  margin-bottom: 0;
}
.info-icon-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.info-icon {
  width: 14px;
  height: 14px;
  color: var(--text-mut);
  cursor: default;
  opacity: 0.6;
  transition: opacity 0.2s;
}
.info-icon-wrap:hover .info-icon {
  opacity: 1;
  color: var(--accent-cyan);
}
.tooltip {
  display: none;
  position: absolute;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  background: #161b22;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 12px;
  color: var(--text-mut);
  line-height: 1.6;
  width: 220px;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  pointer-events: none;
}
.info-icon-wrap:hover .tooltip {
  display: block;
}
</style>
