<template>
  <!-- Odoo's list view (o_list_view): a full-width white table, bold header row with sortable
       columns, light row rules and hover, and a totals row for summed columns. In a
       height-bounded parent (list pages) the rows scroll under a sticky header. -->
  <div class="flex min-h-0 flex-col overflow-hidden bg-white" :class="boxed && 'rounded border border-odoo-line'">
    <div class="min-h-0 overflow-auto">
      <table class="w-full text-left text-[13px]">
        <thead>
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              scope="col"
              class="sticky top-0 z-10 whitespace-nowrap border-b-2 border-odoo-line bg-white px-3 py-2 font-semibold text-odoo-strong"
              :class="col.align === 'right' && 'text-right'"
              :style="col.width && { width: col.width }"
              :aria-sort="ariaSort(col)"
            >
              <button
                v-if="sort && col.sortField"
                type="button"
                class="inline-flex items-center gap-1 hover:text-odoo-action"
                :class="col.align === 'right' && 'flex-row-reverse'"
                @click="sort.by(col.sortField)"
              >
                {{ col.label }}
                <span
                  class="size-3.5"
                  :class="sort.field === col.sortField ? (sort.order === 'asc' ? 'lucide-chevron-up' : 'lucide-chevron-down') : ''"
                  aria-hidden="true"
                />
              </button>
              <template v-else>{{ col.label }}</template>
            </th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading && !rows.length">
            <tr v-for="i in 6" :key="'s' + i" class="border-b border-odoo-hover">
              <td v-for="col in columns" :key="col.key" class="px-3 py-2.5">
                <div class="h-3 w-3/4 animate-pulse rounded bg-odoo-hover" />
              </td>
            </tr>
          </template>
          <tr
            v-for="row in rows"
            :key="row.name"
            class="border-b border-odoo-hover"
            :class="[(rowRoute || rowClickable) && 'cursor-pointer hover:bg-[#f2f3f5]', loading && 'opacity-60']"
            @click="rowRoute ? $router.push(rowRoute(row)) : rowClickable && $emit('row-click', row)"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              class="px-3 py-2 align-middle text-odoo-text"
              :class="[col.align === 'right' && 'text-right tabular-nums', col.class]"
            >
              <slot :name="'cell-' + col.key" :row="row" :value="row[col.key]">
                {{ col.format ? col.format(row[col.key], row) : row[col.key] ?? '' }}
              </slot>
            </td>
          </tr>
        </tbody>
        <tfoot v-if="hasSums && rows.length">
          <tr class="border-t border-odoo-line bg-white font-semibold text-odoo-strong">
            <td
              v-for="col in columns"
              :key="col.key"
              class="sticky bottom-0 bg-white px-3 py-2"
              :class="col.align === 'right' && 'text-right tabular-nums'"
            >
              <template v-if="col.sum">{{ col.format ? col.format(sumOf(col.key)) : sumOf(col.key) }}</template>
            </td>
          </tr>
        </tfoot>
      </table>
    </div>

    <EmptyState v-if="!loading && !rows.length" :icon="emptyIcon" :title="emptyTitle" :description="emptyDescription" />

    <!-- Tables that grow by "Load more" (their own data, not useDocList) -->
    <div
      v-if="!pager && hasMore && rows.length"
      class="flex shrink-0 items-center justify-between border-t border-odoo-hover px-3 py-1.5 text-[13px] text-odoo-muted"
    >
      <span class="tabular-nums">{{ rows.length }}<template v-if="total != null"> / {{ total }}</template></span>
      <button type="button" class="text-odoo-action hover:text-odoo-action-dark disabled:opacity-50" :disabled="loading" @click="$emit('load-more')">
        Load more
      </button>
    </div>

    <!-- A secondary table's own pager (the page's main list has it in the control panel) -->
    <div v-if="pager && pager.total > pager.pageSize" class="flex shrink-0 justify-end border-t border-odoo-hover px-3 py-1.5">
      <Pager :pager="pager" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import EmptyState from './EmptyState.vue'
import Pager from './odoo/Pager.vue'

const props = defineProps({
  /**
   * [{ key, label, align?: 'right', width?, format?: (value, row) => string, class?,
   *    sortField?: a field to sort by on header click, sum?: total it under the column }]
   */
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  /** row => route location; makes rows clickable */
  rowRoute: { type: Function, default: null },
  /** Without a rowRoute, make rows clickable and emit `row-click` with the row. */
  rowClickable: { type: Boolean, default: false },
  emptyTitle: { type: String, default: 'No record found' },
  emptyDescription: { type: String, default: null },
  emptyIcon: { type: String, default: 'lucide-inbox' },
  /** useDocList's `sort`: makes columns with a `sortField` sortable. */
  sort: { type: Object, default: null },
  /** useDocList's `pager`, for a table that is not the page's main list. */
  pager: { type: Object, default: null },
  /** A bordered box (a table inside a page section) instead of a full-width view. */
  boxed: { type: Boolean, default: false },
  /** For tables without a pager: show "Load more" (emits `load-more`). */
  hasMore: { type: Boolean, default: false },
  total: { type: Number, default: null },
})
defineEmits(['row-click', 'load-more'])

const hasSums = computed(() => props.columns.some((c) => c.sum))

/** Odoo sums the records on screen. */
function sumOf(key) {
  return props.rows.reduce((total, row) => total + (Number(row[key]) || 0), 0)
}

function ariaSort(col) {
  if (!props.sort || !col.sortField || props.sort.field !== col.sortField) return undefined
  return props.sort.order === 'asc' ? 'ascending' : 'descending'
}
</script>
