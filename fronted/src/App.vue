<template>
  <div class="app-container tech-theme">
    <!-- 1. 最左側：模式切換 (Nav Rail) -->
    <nav class="nav-rail">
      <div class="nav-items">
        <button
          v-for="m in MODES" :key="m.id"
          :class="['nav-btn', { active: route.name === m.id }]"
          @click="navigate(m.id)"
        >
          <div class="nav-icon-wrap"><svg class="svg-icon" viewBox="0 0 24 24" v-html="m.icon"></svg></div>
          <span class="nav-text">{{ m.name }}</span>
        </button>
      </div>
      <div class="nav-footer">
        <button class="collapse-btn" @click="isCollapsed = !isCollapsed">
          <svg :class="['svg-icon', { rotated: isCollapsed }]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <div class="pulse-status online"></div>
      </div>
    </nav>

    <!-- 2. 左側控制欄（依路由顯示不同 sidebar） -->
    <transition name="slide">
      <div v-if="!isCollapsed" class="unified-sidebar">
        <StockSidebar          v-if="route.name === 'trading'" />
        <StrategyParamsSidebar v-else-if="route.name === 'ranking'" :show-save="false" @run="strategy.triggerRankRun()" />
        <ScreenerPanel         v-else-if="route.name === 'screener'" :selected-stock="market.selectedStock" @select-stock="market.selectStock" />
      </div>
    </transition>

    <!-- 3. 主內容區 -->
    <main class="main-content">
      <AppNotification />
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMarketStore }   from '@/stores/market'
import { useStrategyStore } from '@/stores/strategy'
import StockSidebar          from '@/components/StockSidebar.vue'
import StrategyParamsSidebar from '@/components/StrategyParamsSidebar.vue'
import ScreenerPanel         from '@/components/ScreenerPanel.vue'
import AppNotification       from '@/components/AppNotification.vue'

const route    = useRoute()
const router   = useRouter()
const market   = useMarketStore()
const strategy = useStrategyStore()

const isCollapsed = ref(false)

const MODES = [
  { id: 'trading',  name: '交易終端', icon: '<path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>' },
  { id: 'ranking',  name: '策略排行', icon: '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>' },
  { id: 'screener', name: '選股大師', icon: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>' },
]

function navigate(name) {
  if (name === 'ranking') market.selectStock(null)
  isCollapsed.value = false
  router.push('/' + name)
}
</script>

<style>
/* ── 全域變數 & 共用元件樣式 ───────────────────────────── */
:root {
  --bg-main: #05070a; --bg-surface: #0d1117; --bg-nav: #080a0f;
  --border-color: #1f2937; --accent-cyan: #64b5f6; --accent-blue: #5c6bc0;
  --text-pri: #ffffff; --text-mut: #b1bac4;
  --stock-up: #ff5252; --stock-down: #4caf50;
}
body { background: var(--bg-main); color: var(--text-pri); font-family: 'Inter', 'Microsoft JhengHei', sans-serif; font-size: 16px; height: 100vh; overflow: hidden; }

/* sidebar 內部共用 */
.sidebar-tech-inner { width: 100%; height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.sb-title-tech { padding: 24px 20px; font-size: 14px; font-weight: 900; color: var(--accent-cyan); letter-spacing: 0.1em; border-bottom: 1px solid var(--border-color); }
.sidebar-scroll { flex: 1; overflow-y: auto; scrollbar-width: thin; scrollbar-color: var(--accent-cyan) transparent; }
.sb-section-tech { border-bottom: 1px solid rgba(255,255,255,0.03); }
.sb-hd-tech { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; cursor: pointer; font-size: 14px; font-weight: 700; color: var(--text-mut); }
.sb-hd-tech:hover { background: rgba(255,255,255,0.02); color: var(--text-pri); }
.sb-body-tech { padding: 0 20px 20px; }
.sb-group-tech { padding: 18px 20px 10px; font-size: 11px; font-weight: 900; color: var(--accent-blue); letter-spacing: 0.15em; border-bottom: 1px solid rgba(255,255,255,0.03); background: rgba(0,0,0,0.1); margin-bottom: 12px; }
.num-inp-tech { background: #0d1117; border: 1px solid var(--border-color); color: var(--text-pri); padding: 10px; border-radius: 6px; font-size: 14px; font-family: 'JetBrains Mono', monospace; width: 100%; outline: none; transition: 0.2s; }
.num-inp-tech:focus { border-color: var(--accent-cyan); box-shadow: 0 0 10px rgba(100, 181, 246, 0.1); }
.sl-tech { width: 100%; accent-color: var(--accent-blue); cursor: pointer; height: 6px; border-radius: 3px; background: #161b22; }
.sw-track-tech { width: 38px; height: 20px; border-radius: 10px; background: #161b22; position: relative; cursor: pointer; border: 1px solid var(--border-color); }
.sw-track-tech.on { background: rgba(100,181,246,0.1); border-color: var(--accent-cyan); }
.sw-thumb-tech { position: absolute; width: 14px; height: 14px; border-radius: 50%; background: var(--text-mut); top: 2px; left: 2px; transition: 0.3s; }
.sw-track-tech.on .sw-thumb-tech { transform: translateX(18px); background: var(--accent-cyan); box-shadow: 0 0 10px var(--accent-cyan); }
.lbl-tech { font-size: 11px; color: var(--text-mut); font-weight: 600; text-transform: uppercase; margin-bottom: 8px; display: block; }
.hint-tech { font-size: 12px; color: var(--text-mut); opacity: 0.7; line-height: 1.5; }

/* ── 各頁面共用的 header & 內容樣式 ────────────────────── */
.content-header { height: 72px; background: rgba(13, 17, 23, 0.8); backdrop-filter: blur(10px); border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; padding: 0 24px; flex-shrink: 0; }
.header-left { display: flex; align-items: baseline; gap: 12px; }
.stock-name { font-size: 28px; font-weight: 800; color: #fff; }
.stock-code { font-size: 18px; color: var(--accent-cyan); font-family: 'JetBrains Mono', monospace; }
.mode-title-tech { font-size: 24px; font-weight: 900; color: #fff; letter-spacing: 0.05em; }
.tech-tabs { display: flex; background: rgba(0, 0, 0, 0.3); padding: 5px; border-radius: 6px; border: 1px solid var(--border-color); }
.tech-tab-btn { background: none; border: none; color: var(--text-mut); padding: 10px 32px; font-size: 16px; font-weight: 700; cursor: pointer; transition: 0.2s; }
.tech-tab-btn.active { background: var(--accent-cyan); color: #000; border-radius: 4px; }
.empty-state-tech { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; }
</style>

<style scoped>
.app-container { display: flex; height: 100vh; width: 100vw; background: var(--bg-main); overflow: hidden; }

/* Nav Rail */
.nav-rail { width: 72px; background: var(--bg-nav); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; align-items: center; padding: 24px 0; flex-shrink: 0; z-index: 100; }
.nav-items { flex: 1; display: flex; flex-direction: column; gap: 24px; width: 100%; }
.nav-btn { background: none; border: none; color: var(--text-mut); width: 100%; padding: 8px 0; cursor: pointer; display: flex; flex-direction: column; align-items: center; gap: 8px; transition: all 0.3s; }
.nav-icon-wrap { width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 12px; transition: all 0.3s; }
.svg-icon { width: 22px; height: 22px; fill: none; stroke: currentColor; stroke-width: 2; transition: transform 0.3s; }
.nav-btn.active .nav-icon-wrap { background: rgba(100, 181, 246, 0.1); box-shadow: inset 0 0 15px rgba(100, 181, 246, 0.1); }
.nav-btn.active { color: var(--accent-cyan); }
.nav-text { font-size: 10px; font-weight: 700; }
.nav-footer { margin-top: auto; display: flex; flex-direction: column; align-items: center; gap: 20px; }
.collapse-btn { background: none; border: 1px solid var(--border-color); color: var(--text-mut); width: 32px; height: 32px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.rotated { transform: rotate(180deg); }
.pulse-status { width: 8px; height: 8px; border-radius: 50%; background: #4ecb71; box-shadow: 0 0 10px #4ecb71; animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

/* Sidebar */
.unified-sidebar { width: 280px; min-width: 280px; background: var(--bg-nav); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; z-index: 50; height: 100vh; }
.slide-enter-active, .slide-leave-active { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); overflow: hidden; }
.slide-enter-from, .slide-leave-to { width: 0; min-width: 0; opacity: 0; }

/* Main */
.main-content { flex: 1; display: flex; flex-direction: column; min-width: 0; background: #080a0f; height: 100vh; overflow: hidden; }

</style>
