<template>
  <div class="sidebar-tech-inner">
    <!-- 標題內置，與選股大師對齊 -->
    <div class="sb-title-tech">策略參數設定</div>

    <div class="sidebar-scroll">
      <!-- ① 策略選擇 -->
      <div class="sb-section-tech">
        <div class="sb-hd-tech" @click="toggle('strategy')">
          <span>選擇交易策略</span>
          <span class="sb-arrow-tech">{{ open.strategy ? '▾' : '▸' }}</span>
        </div>
        <div v-show="open.strategy" class="sb-body-tech">
          <select v-model="store.selectedId" class="num-inp-tech" @change="store.onStrategyChange()">
            <option v-for="s in store.strategies" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
          <div v-if="store.current" class="hint-tech mt8">{{ store.current.description }}</div>
        </div>
      </div>

      <!-- ② 指標參數 -->
      <div v-if="store.current?.params?.length" class="sb-section-tech">
        <div class="sb-hd-tech" @click="toggle('indicator')">
          <span>技術指標參數</span>
          <span class="sb-arrow-tech">{{ open.indicator ? '▾' : '▸' }}</span>
        </div>
        <div v-show="open.indicator" class="sb-body-tech">
          <div v-for="p in store.current.params" :key="p.key" class="row-tech mb16">
            <div class="pr-hd-tech">
              <span class="lbl-tech">{{ p.label }}</span>
              <span class="pr-val-tech">{{ fmtParamVal(p, store.params[p.key]) }}</span>
            </div>
            <template v-if="!p.type || p.type === 'range'">
              <input type="range" :min="p.min" :max="p.max" :step="p.step ?? 1" v-model.number="store.params[p.key]" class="sl-tech" />
            </template>
            <template v-else-if="p.type === 'select'">
              <select v-model="store.params[p.key]" class="num-inp-tech">
                <option v-for="o in p.options" :key="o.value" :value="o.value">{{ o.label }}</option>
              </select>
            </template>
            <template v-else-if="p.type === 'switch'">
              <div class="sw-track-tech" :class="{ on: store.params[p.key] }" @click="store.params[p.key] = !store.params[p.key]">
                <div class="sw-thumb-tech" />
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- ③ 停損停利 -->
      <div class="sb-section-tech">
        <div class="sb-hd-tech" @click="toggle('sl')">
          <span>出場與風險控管</span>
          <span class="sb-arrow-tech">{{ open.sl ? '▾' : '▸' }}</span>
        </div>
        <div v-show="open.sl" class="sb-body-tech">
          <div class="row-tech mb16">
            <div class="pr-hd-tech">
              <span class="lbl-tech">停利目標 %</span>
              <MetricValue :value="store.rp.tp_pct" suffix="%" class="pr-val-tech" />
            </div>
            <input type="range" min="2" max="50" step="0.5" v-model.number="store.rp.tp_pct" class="sl-tech sl-up-tech" />
          </div>
          <div class="row-tech mb16">
            <div class="pr-hd-tech">
              <span class="lbl-tech">停損限制 %</span>
              <MetricValue :value="store.rp.sl_pct" suffix="%" class="pr-val-tech" inverse />
            </div>
            <input type="range" min="1" max="20" step="0.5" v-model.number="store.rp.sl_pct" class="sl-tech sl-down-tech" />
          </div>
          <div class="hint-tech">當前盈虧比: <strong :class="rrClass">{{ rrRatio }}</strong></div>
        </div>
      </div>

      <div class="sb-group-tech">進階設定</div>

      <!-- ④ 倉位管理 -->
      <div class="sb-section-tech">
        <div class="sb-hd-tech" @click="toggle('position')">
          <span>資金與倉位</span>
          <span class="sb-arrow-tech">{{ open.position ? '▾' : '▸' }}</span>
        </div>
        <div v-show="open.position" class="sb-body-tech">
          <div class="row-tech mb12">
            <span class="lbl-tech">每筆投入資金 %</span>
            <input type="number" v-model.number="store.rp.position_pct" class="num-inp-tech" />
          </div>
          <div class="row-tech">
            <span class="lbl-tech">最大持倉檔數</span>
            <input type="number" v-model.number="store.rp.max_positions" class="num-inp-tech" />
          </div>
        </div>
      </div>

      <!-- ⑥ 回測區間 -->
      <div class="sb-section-tech">
        <div class="sb-hd-tech" @click="toggle('daterange')">
          <span>歷史回測區間</span>
          <span class="sb-arrow-tech">{{ open.daterange ? '▾' : '▸' }}</span>
        </div>
        <div v-show="open.daterange" class="sb-body-tech">
          <div class="shortcuts-tech mb12">
            <button v-for="r in SHORTCUTS" :key="r.label" :class="['sc-tech', { active: activeShort === r.label }]" @click="applyShort(r)">{{ r.label }}</button>
          </div>
          <div class="row-tech mb8"><label class="lbl-tech">開始日期</label><input type="date" v-model="store.startDate" class="num-inp-tech" /></div>
          <div class="row-tech"><label class="lbl-tech">結束日期</label><input type="date" v-model="store.endDate" class="num-inp-tech" /></div>
        </div>
      </div>
    </div>

    <div class="sidebar-actions">
      <button class="btn-primary-tech" @click="validate() && $emit('run')">開始回測</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useStrategyStore } from '@/stores/strategy'
import { useNotifyStore } from '@/stores/notify'
import MetricValue from '@/components/MetricValue.vue'

const props = defineProps({ showSave: { type: Boolean, default: true } })
const emit = defineEmits(['run'])
const store = useStrategyStore()
const notify = useNotifyStore()

const open = reactive({ strategy: true, indicator: true, sl: true, position: false, daterange: true })
function toggle(k) { open[k] = !open[k] }

const rrRatio = computed(() => store.rp.sl_pct ? (store.rp.tp_pct / store.rp.sl_pct).toFixed(2) + ' : 1' : '—')
const rrClass = computed(() => { const r = store.rp.tp_pct / store.rp.sl_pct; return r >= 2 ? 'up' : r < 1 ? 'down' : '' })

function fmtParamVal(p, val) {
  if (p.suffix) return val + p.suffix
  if (p.type === 'select') return p.options?.find(o => o.value === val)?.label ?? val
  if (p.type === 'switch') return val ? '啟用' : '關閉'
  return val
}

function validate() {
  if (store.rp.sl_pct <= 0) { notify.error('停損比例必須大於 0'); return false }
  if (store.rp.tp_pct <= 0) { notify.error('停利比例必須大於 0'); return false }
  if (store.startDate >= store.endDate) { notify.error('結束日期必須晚於開始日期'); return false }
  if (store.rp.position_pct * store.rp.max_positions > 100) {
    notify.info('每筆投入 × 最大持倉超過 100%，請確認資金配置')
  }
  return true
}

const SHORTCUTS = [ { label: '1M', months: 1 }, { label: '3M', months: 3 }, { label: '6M', months: 6 }, { label: '1Y', months: 12 } ]
const activeShort = ref('1Y')
function applyShort(r) {
  const end = new Date(); const start = new Date(); start.setMonth(start.getMonth() - r.months)
  store.endDate = end.toISOString().slice(0, 10); store.startDate = start.toISOString().slice(0, 10); activeShort.value = r.label
}
</script>

<style scoped>
.sidebar-tech-inner { width: 100%; height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.sb-title-tech { padding: 24px 20px; font-size: 14px; font-weight: 900; color: var(--accent-cyan); letter-spacing: 0.1em; border-bottom: 1px solid var(--border-color); }
.sidebar-scroll { flex: 1; overflow-y: auto; scrollbar-width: thin; scrollbar-color: var(--accent-cyan) transparent; }
.sb-section-tech { border-bottom: 1px solid rgba(255,255,255,0.03); }
.sb-hd-tech { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; cursor: pointer; font-size: 14px; font-weight: 700; color: var(--text-mut); }
.sb-hd-tech:hover { background: rgba(255,255,255,0.02); color: var(--text-pri); }
.sb-body-tech { padding: 0 20px 20px; }

.row-tech { display: flex; flex-direction: column; gap: 8px; }
.mb16 { margin-bottom: 16px; }
.mb12 { margin-bottom: 12px; }
.mb8 { margin-bottom: 8px; }
.mt8 { margin-top: 8px; }

.lbl-tech { font-size: 11px; color: var(--text-mut); font-weight: 600; text-transform: uppercase; }
.hint-tech { font-size: 12px; color: var(--text-mut); opacity: 0.7; line-height: 1.5; }

.pr-hd-tech { display: flex; justify-content: space-between; align-items: center; }
.pr-val-tech { font-size: 14px; font-weight: 800; font-family: 'JetBrains Mono', monospace; }

.sl-tech { width: 100%; accent-color: var(--accent-blue); cursor: pointer; height: 6px; border-radius: 3px; background: #161b22; }
.sl-up-tech { accent-color: var(--stock-up); }
.sl-down-tech { accent-color: var(--stock-down); }

.num-inp-tech { background: #0d1117; border: 1px solid var(--border-color); color: var(--text-pri); padding: 10px; border-radius: 6px; font-size: 14px; font-family: 'JetBrains Mono', monospace; width: 100%; outline: none; box-sizing: border-box; }
.num-inp-tech:focus { border-color: var(--accent-cyan); }

.sw-track-tech { width: 38px; height: 20px; border-radius: 10px; background: #161b22; position: relative; cursor: pointer; border: 1px solid var(--border-color); transition: 0.3s; }
.sw-track-tech.on { background: rgba(100,181,246,0.1); border-color: var(--accent-cyan); }
.sw-thumb-tech { position: absolute; width: 14px; height: 14px; border-radius: 50%; background: var(--text-mut); top: 2px; left: 2px; transition: 0.3s; }
.sw-track-tech.on .sw-thumb-tech { transform: translateX(18px); background: var(--accent-cyan); box-shadow: 0 0 10px var(--accent-cyan); }

.up { color: var(--stock-up) !important; }
.down { color: var(--stock-down) !important; }

.shortcuts-tech { display: flex; flex-wrap: wrap; gap: 6px; }
.sc-tech { flex: 1; min-width: calc(50% - 6px); background: #0d1117; border: 1px solid var(--border-color); border-radius: 4px; color: var(--text-mut); padding: 8px 4px; font-size: 11px; cursor: pointer; font-weight: 700; transition: 0.2s; }
.sc-tech:hover { border-color: var(--accent-cyan); color: var(--text-pri); }
.sc-tech.active { background: rgba(100, 181, 246, 0.1); color: var(--accent-cyan); border-color: var(--accent-cyan); }

.sb-group-tech { padding: 18px 20px 10px; font-size: 11px; font-weight: 900; color: var(--accent-blue); letter-spacing: 0.15em; border-bottom: 1px solid rgba(255,255,255,0.03); background: rgba(0,0,0,0.1); margin-bottom: 12px; }
.sb-arrow-tech { font-size: 12px; color: var(--text-mut); }
.sidebar-actions { padding: 20px; border-top: 1px solid var(--border-color); background: rgba(0,0,0,0.2); }
.btn-primary-tech { width: 100%; padding: 14px; background: var(--accent-cyan); color: #000; border: none; border-radius: 6px; font-weight: 900; cursor: pointer; transition: 0.2s; }
.btn-primary-tech:hover { box-shadow: 0 0 20px rgba(100, 181, 246, 0.3); transform: translateY(-1px); }
</style>
