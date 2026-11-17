<template>
  <!-- Odoo's view switcher: icon buttons for the views a page offers. -->
  <div class="flex" role="group" aria-label="Views">
    <button
      v-for="(view, i) in VIEWS"
      :key="view.value"
      type="button"
      class="flex h-[28px] w-[34px] items-center justify-center bg-odoo-hover text-odoo-text hover:bg-odoo-line focus:outline-none focus-visible:ring-2 focus-visible:ring-odoo-action"
      :class="[i === 0 && 'rounded-l', i === VIEWS.length - 1 && 'rounded-r', i > 0 && 'border-l border-white', model === view.value && '!bg-odoo-line text-odoo-strong']"
      :aria-label="view.label"
      :aria-pressed="model === view.value"
      :title="view.label"
      @click="model = view.value"
    >
      <span :class="[view.icon, 'size-4']" aria-hidden="true" />
    </button>
  </div>
</template>

<script setup>
const VIEWS = [
  { value: 'list', label: 'List', icon: 'lucide-list' },
  { value: 'kanban', label: 'Kanban', icon: 'lucide-layout-grid' },
]
const model = defineModel({ type: String, default: 'list' })
</script>
