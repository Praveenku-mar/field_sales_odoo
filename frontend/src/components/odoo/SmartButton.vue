<template>
  <!-- Odoo's smart (stat) button: icon, a figure and its label; opens related records. -->
  <component
    :is="to ? 'RouterLink' : href ? 'a' : 'button'"
    v-bind="to ? { to } : href ? { href, target: '_blank', rel: 'noopener' } : { type: 'button' }"
    class="flex min-w-[8.5rem] items-center gap-2 border-l border-odoo-hover px-3 py-1.5 text-left hover:bg-[#f2f3f5] focus:outline-none focus-visible:bg-[#f2f3f5]"
  >
    <span :class="[icon, 'size-5 shrink-0 text-odoo-action']" aria-hidden="true" />
    <span class="flex min-w-0 flex-col leading-tight">
      <span class="truncate text-[14px] font-semibold text-odoo-strong">{{ value }}</span>
      <span class="truncate text-[12px] text-odoo-muted">{{ label }}</span>
    </span>
  </component>
</template>

<script setup>
defineProps({
  icon: { type: String, required: true },
  value: { type: [String, Number], default: '' },
  label: { type: String, required: true },
  to: { type: [Object, String], default: null },
  href: { type: String, default: null },
})
</script>
