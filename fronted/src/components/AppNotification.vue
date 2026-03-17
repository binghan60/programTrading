<template>
  <div class="notification-container">
    <transition-group name="list">
      <div
        v-for="n in notify.notifications"
        :key="n.id"
        :class="['notif-box', n.type]"
        @click="notify.remove(n.id)"
      >
        <div class="notif-edge"></div>
        <div class="notif-icon">
          <svg v-if="n.type === 'success'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg>
          <svg v-else-if="n.type === 'error'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M18 6L6 18M6 6l12 12"/></svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
        </div>
        <div class="notif-msg">{{ n.message }}</div>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { useNotifyStore } from '@/stores/notify'
const notify = useNotifyStore()
</script>

<style scoped>
.notification-container {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
}

.notif-box {
  pointer-events: auto;
  min-width: 280px;
  max-width: 400px;
  background: rgba(13, 17, 23, 0.9);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border-color);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.notif-edge {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.success .notif-edge { background: var(--stock-up); box-shadow: 0 0 10px var(--stock-up); }
.error .notif-edge { background: var(--stock-down); box-shadow: 0 0 10px var(--stock-down); }
.info .notif-edge { background: var(--accent-cyan); box-shadow: 0 0 10px var(--accent-cyan); }

.notif-icon { width: 20px; height: 20px; flex-shrink: 0; }
.success .notif-icon { color: var(--stock-up); }
.error .notif-icon { color: var(--stock-down); }
.info .notif-icon { color: var(--accent-cyan); }

.notif-msg {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

/* 動畫 */
.list-enter-active, .list-leave-active { transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.list-enter-from { opacity: 0; transform: translateX(50px) scale(0.9); }
.list-leave-to { opacity: 0; transform: translateX(20px) scale(0.9); }
</style>
