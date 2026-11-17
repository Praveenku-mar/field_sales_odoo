<template>
  <!-- Odoo's control panel (o_control_panel): breadcrumbs and the view's buttons on the left,
       the search bar in the middle, the pager (and view switcher) on the right. Phones put
       the search on its own row. -->
  <div class="o-control-panel shrink-0 border-b border-odoo-line bg-white px-4 py-2.5" :class="!flush && 'mb-4'">
    <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
      <div class="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-2">
        <nav class="flex min-w-0 items-center gap-1.5 text-[18px]" aria-label="Breadcrumb">
          <template v-for="crumb in breadcrumbs" :key="crumb.label">
            <RouterLink :to="crumb.to" class="truncate text-odoo-action hover:text-odoo-action-dark">{{ crumb.label }}</RouterLink>
            <span class="text-odoo-muted" aria-hidden="true">/</span>
          </template>
          <h1 class="truncate font-medium text-odoo-strong">{{ title }}</h1>
        </nav>
        <StatusPill v-if="status" :status="status" />
        <slot name="meta" />
        <div v-if="$slots.actions" class="flex flex-wrap items-center gap-2">
          <slot name="actions" />
        </div>
      </div>

      <div v-if="$slots.search" class="order-last w-full min-w-0 lg:order-none lg:w-auto lg:max-w-2xl lg:flex-1">
        <slot name="search" />
      </div>
      <div v-else class="flex-1" />

      <div v-if="pager || $slots.views" class="ml-auto flex items-center gap-3">
        <Pager v-if="pager" :pager="pager" />
        <slot name="views" />
      </div>
    </div>
  </div>
</template>

<script setup>
import StatusPill from './StatusPill.vue'
import Pager from './odoo/Pager.vue'

defineProps({
  title: { type: String, required: true },
  /** Shown as a StatusPill next to the title. */
  status: { type: String, default: null },
  /** Earlier steps, Odoo-style: [{ label, to }] before the title. */
  breadcrumbs: { type: Array, default: () => [] },
  /** useDocList's `pager`: shows Odoo's "1-80 / 240" with previous / next. */
  pager: { type: Object, default: null },
  /** No gap below: a list view starts right under the panel. */
  flush: { type: Boolean, default: false },
})
</script>
