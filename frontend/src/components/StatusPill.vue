<template>
  <!-- Odoo's status badge (badge rounded-pill, decoration colours): a tinted pill. -->
  <span
    class="inline-flex max-w-full items-center gap-1 whitespace-nowrap rounded-full px-2 py-px text-xs font-medium leading-5"
    :class="STYLES[tone]"
  >
    <span v-if="icon" :class="[icon, 'size-3 shrink-0']" aria-hidden="true" />
    <span class="truncate">{{ label || status }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, required: true },
  label: { type: String, default: null },
  /** Icon class (e.g. lucide-circle-check) rendered before the label. */
  icon: { type: String, default: null },
})

// Odoo's decoration colours: success, warning, danger, info, muted.
const STYLES = {
  success: 'bg-[#d4edda] text-[#1a6f2e]',
  warning: 'bg-[#fbebcc] text-[#a36e00]',
  danger: 'bg-[#f6dbde] text-[#9b3540]',
  info: 'bg-[#cce5e6] text-[#01585c]',
  muted: 'bg-[#e7e9ed] text-[#4b5563]',
}

// Sync, payment and document states used across Field Order, Retailer, Visit, Sales Rep and Sync Log.
const TONES = {
  Synced: 'success',
  Success: 'success',
  Completed: 'success',
  Active: 'success',
  Earned: 'success',
  Paid: 'success',
  Pending: 'warning',
  Retrying: 'warning',
  'In Progress': 'warning',
  'Partially Paid': 'warning',
  'Link Expired': 'warning',
  Planned: 'info',
  Approved: 'info',
  'Link Sent': 'info',
  Failed: 'danger',
  'Out of Stock': 'danger',
  Cancelled: 'danger',
  Reversed: 'danger',
  'Link Cancelled': 'danger',
  Draft: 'muted',
  Unpaid: 'muted',
  Inactive: 'muted',
}
const tone = computed(() => TONES[props.status] || 'muted')
</script>
