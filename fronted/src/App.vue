<template>
  <div class="app-container tech-theme">
    <!-- 背景網格裝飾 -->
    <div class="bg-grid" aria-hidden="true"></div>
    <div class="bg-glow-orb orb-1" aria-hidden="true"></div>
    <div class="bg-glow-orb orb-2" aria-hidden="true"></div>

    <!-- 1. 最左側：模式切換 (Nav Rail) -->
    <nav class="nav-rail">
      <!-- 品牌 Logo -->
      <div class="nav-brand">
        <div class="brand-mark">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
            <polyline points="16 7 22 7 22 13" />
          </svg>
        </div>
        <span class="brand-text">PT</span>
      </div>

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
        <button class="collapse-btn" @click="isCollapsed = !isCollapsed" :title="isCollapsed ? '展開側欄' : '收起側欄'">
          <svg :class="['svg-icon', { rotated: isCollapsed }]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <div class="pulse-status online" title="系統連線中"></div>
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
  /* 背景色階 */
  --bg-main:    #020408;
  --bg-surface: #080c14;
  --bg-nav:     #050810;
  --bg-card:    #0b0f1b;

  /* 邊框 */
  --border-color: #17213a;
  --border-bright: rgba(0, 212, 255, 0.25);

  /* 強調色（低飽和，護眼） */
  --accent-cyan:   #4db8cc;
  --accent-blue:   #6272a4;
  --accent-purple: #8b7ec8;

  /* 文字 */
  --text-pri: #cdd6e0;
  --text-mut: #4e5c72;
  --text-dim: #273040;

  /* 股票漲跌 */
  --stock-up:   #c0392b;
  --stock-down: #27ae60;

  /* 發光陰影（柔和，降低擴散範圍） */
  --glow-cyan:   0 0 12px rgba(77, 184, 204, 0.2);
  --glow-blue:   0 0 12px rgba(98, 114, 164, 0.2);
  --glow-purple: 0 0 12px rgba(139, 126, 200, 0.2);
  --glow-up:     0 0 10px rgba(192, 57, 43, 0.25);
  --glow-down:   0 0 10px rgba(39, 174, 96, 0.25);
}

*, *::before, *::after { box-sizing: border-box; }
body {
  background: var(--bg-main);
  color: var(--text-pri);
  font-family: 'Inter', 'Microsoft JhengHei', sans-serif;
  font-size: 16px;
  height: 100vh;
  overflow: hidden;
}

/* ── 自訂捲軸 ─────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0, 212, 255, 0.3); }

/* ── Sidebar 共用 ──────────────────────────────────────── */
.sidebar-tech-inner { width: 100%; height: 100%; display: flex; flex-direction: column; overflow: hidden; }

.sb-title-tech {
  padding: 20px 20px 16px;
  font-size: 12px; font-weight: 900; letter-spacing: 0.15em; text-transform: uppercase;
  color: var(--accent-cyan);
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(180deg, rgba(0, 212, 255, 0.04) 0%, transparent 100%);
}

.sidebar-scroll {
  flex: 1; overflow-y: auto;
  scrollbar-width: thin; scrollbar-color: var(--border-color) transparent;
}

.sb-section-tech { border-bottom: 1px solid rgba(255,255,255,0.03); }

.sb-hd-tech {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px;
  cursor: pointer; font-size: 13px; font-weight: 700;
  color: var(--text-mut); letter-spacing: 0.08em; text-transform: uppercase;
  transition: all 0.2s;
}
.sb-hd-tech:hover { background: rgba(0, 212, 255, 0.03); color: var(--accent-cyan); }

.sb-body-tech { padding: 0 20px 20px; }

.sb-group-tech {
  padding: 14px 20px 10px;
  font-size: 11px; font-weight: 900; letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--accent-blue);
  border-bottom: 1px solid rgba(255,255,255,0.03);
  background: rgba(0,0,0,0.15);
  margin-bottom: 12px;
}

.num-inp-tech {
  background: rgba(0,0,0,0.3);
  border: 1px solid var(--border-color);
  color: var(--text-pri);
  padding: 10px 12px;
  border-radius: 6px; font-size: 15px;
  font-family: 'JetBrains Mono', monospace;
  width: 100%; outline: none; transition: 0.25s;
}
.num-inp-tech:focus {
  border-color: var(--accent-cyan);
  box-shadow: 0 0 0 1px rgba(77, 184, 204, 0.12);
  background: rgba(77, 184, 204, 0.03);
}

.sl-tech {
  width: 100%; accent-color: var(--accent-cyan);
  cursor: pointer; height: 4px; border-radius: 2px;
  background: var(--border-color);
}

.sw-track-tech {
  width: 40px; height: 22px; border-radius: 11px;
  background: rgba(0,0,0,0.4); position: relative; cursor: pointer;
  border: 1px solid var(--border-color); transition: 0.3s;
}
.sw-track-tech.on { background: rgba(77,184,204,0.1); border-color: rgba(77,184,204,0.4); }
.sw-thumb-tech { position: absolute; width: 16px; height: 16px; border-radius: 50%; background: var(--text-mut); top: 2px; left: 2px; transition: 0.3s; }
.sw-track-tech.on .sw-thumb-tech { transform: translateX(18px); background: var(--accent-cyan); }

.lbl-tech { font-size: 11px; color: var(--text-mut); font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; display: block; }
.hint-tech { font-size: 12px; color: var(--text-mut); opacity: 0.7; line-height: 1.6; }

/* ── 頁面共用 Header ──────────────────────────────────── */
.content-header {
  height: 64px;
  background: rgba(5, 8, 16, 0.85);
  backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  border-bottom: 1px solid var(--border-color);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 28px; flex-shrink: 0;
  position: relative;
}
.content-header::after {
  content: '';
  position: absolute; bottom: -1px; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(77, 184, 204, 0.15), transparent);
}

.header-left { display: flex; align-items: baseline; gap: 14px; }

.stock-name {
  font-size: 28px; font-weight: 800; color: var(--text-pri);
  background: linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.7) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.stock-code {
  font-size: 17px; color: var(--accent-cyan);
  font-family: 'JetBrains Mono', monospace; font-weight: 700;
}

.mode-title-tech {
  font-size: 24px; font-weight: 900; letter-spacing: 0.05em;
  background: linear-gradient(135deg, var(--text-pri) 0%, var(--accent-cyan) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}

/* ── 標籤切換 ─────────────────────────────────────────── */
.tech-tabs {
  display: flex; background: rgba(0, 0, 0, 0.4); padding: 4px;
  border-radius: 8px; border: 1px solid var(--border-color);
  gap: 2px;
}
.tech-tab-btn {
  background: none; border: none; color: var(--text-mut);
  padding: 8px 28px; font-size: 15px; font-weight: 700;
  cursor: pointer; border-radius: 6px; transition: all 0.25s;
  letter-spacing: 0.03em;
}
.tech-tab-btn:hover { color: var(--text-pri); background: rgba(255,255,255,0.04); }
.tech-tab-btn.active {
  background: rgba(77, 184, 204, 0.1);
  color: var(--accent-cyan);
  box-shadow: inset 0 0 0 1px rgba(77, 184, 204, 0.2);
}

/* ── 空狀態 ──────────────────────────────────────────── */
.empty-state-tech {
  height: 100%; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 16px;
  color: var(--text-mut);
}
.empty-state-tech h3 {
  font-size: 22px; font-weight: 800; color: var(--text-pri);
  background: linear-gradient(135deg, var(--text-pri) 0%, var(--accent-cyan) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  margin: 0;
}
.empty-state-tech p { font-size: 14px; color: var(--text-mut); margin: 0; letter-spacing: 0.05em; }

/* ── 全域動畫 ─────────────────────────────────────────── */
@keyframes pulse       { 0%,100%{opacity:1} 50%{opacity:0.3} }
@keyframes spin        { to{transform:rotate(360deg)} }
@keyframes glow-pulse  { 0%,100%{opacity:0.6;transform:scale(1)} 50%{opacity:1;transform:scale(1.05)} }
@keyframes scan-line   { 0%{top:-5%} 100%{top:105%} }
@keyframes orbit-ring  { to{transform:rotate(360deg)} }
</style>

<style scoped>
/* ── 整體容器 ──────────────────────────────────────────── */
.app-container {
  display: flex; height: 100vh; width: 100vw;
  background: var(--bg-main); overflow: hidden;
  position: relative;
}

/* ── 背景裝飾 ─────────────────────────────────────────── */
.bg-grid {
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    linear-gradient(rgba(77, 184, 204, 0.012) 1px, transparent 1px),
    linear-gradient(90deg, rgba(77, 184, 204, 0.012) 1px, transparent 1px);
  background-size: 48px 48px;
}

.bg-glow-orb {
  position: fixed; pointer-events: none; z-index: 0;
  border-radius: 50%; filter: blur(100px);
}
.orb-1 {
  width: 600px; height: 400px;
  top: -100px; left: -100px;
  background: radial-gradient(ellipse, rgba(77, 184, 204, 0.03) 0%, transparent 70%);
}
.orb-2 {
  width: 500px; height: 500px;
  bottom: -150px; right: 10%;
  background: radial-gradient(ellipse, rgba(98, 114, 164, 0.035) 0%, transparent 70%);
}

/* ── Nav Rail ────────────────────────────────────────── */
.nav-rail {
  width: 72px;
  background: rgba(5, 8, 16, 0.95);
  border-right: 1px solid var(--border-color);
  display: flex; flex-direction: column; align-items: center;
  padding: 0 0 20px; flex-shrink: 0; z-index: 100;
  position: relative;
}
.nav-rail::after {
  content: '';
  position: absolute; top: 0; right: -1px; bottom: 0; width: 1px;
  background: linear-gradient(180deg, transparent, rgba(77, 184, 204, 0.08) 30%, rgba(98, 114, 164, 0.08) 70%, transparent);
  pointer-events: none;
}

/* 品牌標誌 */
.nav-brand {
  width: 100%; height: 64px; flex-shrink: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  border-bottom: 1px solid var(--border-color); gap: 2px;
}
.brand-mark {
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  color: var(--accent-cyan); filter: drop-shadow(0 0 4px rgba(77,184,204,0.3));
}
.brand-mark svg { width: 100%; height: 100%; }
.brand-text {
  font-size: 10px; font-weight: 900; letter-spacing: 0.18em;
  color: var(--accent-cyan); opacity: 0.7;
  font-family: 'JetBrains Mono', monospace;
}

/* Nav 按鈕 */
.nav-items { flex: 1; display: flex; flex-direction: column; gap: 4px; width: 100%; padding: 16px 0; }
.nav-btn {
  background: none; border: none; color: var(--text-mut);
  width: 100%; padding: 6px 0; cursor: pointer;
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  transition: all 0.25s; position: relative;
}
.nav-btn:hover { color: var(--text-pri); }
.nav-btn:hover .nav-icon-wrap { background: rgba(255,255,255,0.05); transform: scale(1.05); }

.nav-icon-wrap {
  width: 44px; height: 44px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 14px; transition: all 0.25s;
}
.svg-icon {
  width: 20px; height: 20px; fill: none; stroke: currentColor;
  stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;
  transition: all 0.25s;
}

/* 啟用狀態 */
.nav-btn.active { color: var(--accent-cyan); }
.nav-btn.active .nav-icon-wrap {
  background: rgba(77, 184, 204, 0.08);
  box-shadow: inset 0 0 0 1px rgba(77, 184, 204, 0.15);
}
.nav-btn.active .svg-icon { filter: drop-shadow(0 0 4px rgba(77,184,204,0.4)); }
.nav-btn.active::before {
  content: ''; position: absolute; left: 0; top: 50%; transform: translateY(-50%);
  width: 2px; height: 22px; border-radius: 0 2px 2px 0;
  background: var(--accent-cyan); opacity: 0.7;
}

.nav-text { font-size: 10px; font-weight: 800; letter-spacing: 0.05em; }

/* Nav 底部 */
.nav-footer { margin-top: auto; display: flex; flex-direction: column; align-items: center; gap: 16px; padding-bottom: 4px; }
.collapse-btn {
  background: rgba(0,0,0,0.3); border: 1px solid var(--border-color);
  color: var(--text-mut); width: 32px; height: 32px; border-radius: 8px;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all 0.25s;
}
.collapse-btn:hover { border-color: rgba(77,184,204,0.25); color: var(--accent-cyan); }
.rotated { transform: rotate(180deg); }

.pulse-status {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--stock-down); box-shadow: 0 0 6px rgba(39,174,96,0.4);
  animation: pulse 2.5s ease-in-out infinite;
}

/* ── Sidebar ─────────────────────────────────────────── */
.unified-sidebar {
  width: 280px; min-width: 280px;
  background: rgba(5, 8, 16, 0.95);
  border-right: 1px solid var(--border-color);
  display: flex; flex-direction: column; z-index: 50; height: 100vh;
  position: relative;
}
.unified-sidebar::after {
  content: '';
  position: absolute; top: 0; right: -1px; bottom: 0; width: 1px;
  background: linear-gradient(180deg, transparent, rgba(77, 184, 204, 0.06) 30%, rgba(77, 184, 204, 0.06) 70%, transparent);
  pointer-events: none;
}

.slide-enter-active, .slide-leave-active { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); overflow: hidden; }
.slide-enter-from, .slide-leave-to { width: 0; min-width: 0; opacity: 0; }

/* ── Main ────────────────────────────────────────────── */
.main-content {
  flex: 1; display: flex; flex-direction: column; min-width: 0;
  background: transparent; height: 100vh; overflow: hidden;
  position: relative; z-index: 1;
}
</style>
