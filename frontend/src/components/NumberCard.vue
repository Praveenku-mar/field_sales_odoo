<template>
  <component
    :is="to ? 'RouterLink' : 'div'"
    :to="to"
    class="fs-card block p-4"
    :class="to && 'transition-colors hover:border-odoo-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-odoo-action'"
  >
    <!-- An Odoo dashboard KPI: label, figure, caption; the icon in the action teal. -->
    <div class="flex items-center justify-between text-[13px] text-odoo-muted">
      <span class="truncate">{{ label }}</span>
      <span v-if="icon" :class="[icon, 'size-4 text-odoo-action']" aria-hidden="true" />
    </div>
    <div class="mt-1.5 flex items-baseline gap-2">
      <span v-if="loading" class="h-7 w-16 animate-pulse rounded bg-odoo-hover" />
      <span v-else class="text-[26px] font-semibold leading-8 tabular-nums" :class="valueClass">{{ formatted }}</span>
      <span v-if="delta != null && !loading" class="text-xs font-medium" :class="delta >= 0 ? 'text-ink-green-7' : 'text-ink-red-5'">
        {{ delta >= 0 ? '▲' : '▼' }} {{ Math.abs(delta).toFixed(1) }}%
      </span>
      <slot v-if="!loading" name="badge" />
    </div>
    <div v-if="caption" class="mt-1 truncate text-xs text-odoo-muted">{{ caption }}</div>
  </component>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [Number, String], default: null },
  /** 'number' | 'currency' | 'percent' */
  format: { type: String, default: 'number' },
  currency: { type: String, default: null },
  icon: { type: String, default: null },
  caption: { type: String, default: null },
  /** Change vs a comparison period, in percent. */
  delta: { type: Number, default: null },
  theme: { type: String, default: null },
  loading: { type: Boolean, default: false },
  to: { type: [String, Object], default: null },
})

const formatted = computed(() => {
  if (props.value == null || props.value === '') return '—'
  if (typeof props.value === 'string') return props.value
  if (props.format === 'percent') return `${props.value.toFixed(1)}%`
  const options = props.format === 'currency' && props.currency
    ? { style: 'currency', currency: props.currency, maximumFractionDigits: 0 }
    : { maximumFractionDigits: 2 }
  return new Intl.NumberFormat(undefined, options).format(props.value)
})

const valueClass = computed(() => ({ red: 'text-ink-red-5', green: 'text-ink-green-7' })[props.theme] || 'text-odoo-strong')
</script>
