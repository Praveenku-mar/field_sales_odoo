<template>
  <!-- Odoo's kanban view: a grid of cards, or (grouped) one column per value with its count and
       "Load more". The page draws each card in the #card slot. -->
  <div class="min-h-0 flex-1 overflow-auto bg-desk-bg">
    <!-- Grouped -->
    <div v-if="columns && columns.length" class="flex h-full min-h-0 gap-3 overflow-x-auto p-3">
      <section
        v-for="col in columns"
        :key="String(col.value)"
        class="flex w-72 shrink-0 flex-col"
        :aria-label="`${col.label}: ${col.count ?? '…'}`"
      >
        <header class="flex items-center justify-between px-1 pb-2">
          <h2 class="truncate text-[15px] font-semibold text-odoo-strong">{{ col.label }}</h2>
          <span class="text-[13px] tabular-nums text-odoo-muted">{{ col.count ?? '' }}</span>
        </header>
        <div class="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto pb-2">
          <KanbanCard v-for="row in col.rows" :key="row.name" :to="rowRoute?.(row)">
            <slot name="card" :row="row" />
          </KanbanCard>
          <p v-if="col.error" class="px-1 text-[13px] text-ink-red-6">{{ col.error }}</p>
          <p v-else-if="!col.loading && !col.rows.length" class="px-1 text-[13px] text-odoo-muted">Nothing here</p>
          <button
            v-if="col.count > col.rows.length"
            type="button"
            class="self-start px-1 text-[13px] text-odoo-action hover:text-odoo-action-dark disabled:opacity-50"
            :disabled="col.loading"
            @click="$emit('load-more', col)"
          >
            Load more ({{ col.count - col.rows.length }})
          </button>
          <div v-if="col.loading && !col.rows.length" class="h-20 animate-pulse rounded bg-white" />
        </div>
      </section>
    </div>

    <!-- Ungrouped -->
    <template v-else>
      <div
        v-if="rows.length || loading"
        class="grid gap-2 p-3 [grid-template-columns:repeat(auto-fill,minmax(min(100%,18rem),1fr))]"
        :class="loading && rows.length && 'opacity-60'"
      >
        <KanbanCard v-for="row in rows" :key="row.name" :to="rowRoute?.(row)">
          <slot name="card" :row="row" />
        </KanbanCard>
        <template v-if="loading && !rows.length">
          <div v-for="i in 8" :key="i" class="h-24 animate-pulse rounded border border-odoo-line bg-white" />
        </template>
      </div>
      <EmptyState v-else :icon="emptyIcon" :title="emptyTitle" :description="emptyDescription" />
    </template>
  </div>
</template>

<script setup>
import { defineComponent, h, resolveComponent } from 'vue'
import EmptyState from '../EmptyState.vue'

defineProps({
  rows: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  /** useKanbanGroups' columns; empty or null shows the ungrouped grid. */
  columns: { type: Array, default: null },
  /** row => route location: cards open the record. */
  rowRoute: { type: Function, default: null },
  emptyTitle: { type: String, default: 'No record found' },
  emptyDescription: { type: String, default: null },
  emptyIcon: { type: String, default: 'lucide-inbox' },
})
defineEmits(['load-more'])

/** One card (o_kanban_record): a white box that opens its record. */
const KanbanCard = defineComponent({
  props: { to: { type: [Object, String], default: null } },
  setup(props, { slots }) {
    const RouterLink = resolveComponent('RouterLink')
    const cls =
      'block rounded border border-odoo-line bg-white p-2.5 text-[13px] text-odoo-text shadow-[0_1px_2px_rgba(0,0,0,0.04)] transition-colors hover:border-odoo-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-odoo-action'
    return () => (props.to ? h(RouterLink, { to: props.to, class: cls }, slots) : h('div', { class: cls }, slots.default?.()))
  },
})
</script>
