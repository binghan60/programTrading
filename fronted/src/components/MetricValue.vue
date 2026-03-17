<template>
  <span :class="['metric-value-tech', colorClass, { 'is-mono': mono }]">
    <slot name="prefix">{{ prefix }}</slot>
    {{ displayValue }}
    <slot name="suffix">{{ suffix }}</slot>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value:     { type: [Number, String], default: null },
  type:      { type: String, default: 'number' }, // 'percent', 'number', 'ratio'
  precision: { type: Number, default: 2 },
  prefix:    { type: String, default: '' },
  suffix:    { type: String, default: '' },
  showSign:  { type: Boolean, default: false }, // 是否強制顯示 + 號
  inverse:   { type: Boolean, default: false }, // 是否反轉紅綠 (如：MDD 越大越綠/紅)
  mono:      { type: Boolean, default: true }   // 是否使用等寬字體
})

const displayValue = computed(() => {
  if (props.value === null || props.value === undefined || props.value === '') return '—'
  
  const num = Number(props.value)
  if (isNaN(num)) return props.value

  let formatted = ''
  if (props.type === 'number') {
    formatted = num.toLocaleString('zh-TW', { minimumFractionDigits: 0, maximumFractionDigits: props.precision })
  } else {
    formatted = num.toFixed(props.precision)
  }

  if (props.showSign && num > 0) return `+${formatted}`
  return formatted
})

const colorClass = computed(() => {
  const num = Number(props.value)
  if (isNaN(num) || num === 0 || props.value === null) return ''
  
  const isPositive = num > 0
  const isGood = props.inverse ? !isPositive : isPositive
  
  return isGood ? 'pos' : 'neg'
})
</script>

<style scoped>
.metric-value-tech {
  font-weight: 600;
}
.is-mono {
  font-family: 'JetBrains Mono', monospace;
}
.pos { color: var(--stock-up); }
.neg { color: var(--stock-down); }
</style>
