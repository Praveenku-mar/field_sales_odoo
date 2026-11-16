<template>
  <!-- Odoo's pager: "1-80 / 240" (the range opens the page size), then ‹ › . -->
  <div v-if="pager.total" class="flex shrink-0 items-center gap-1.5 text-[13px] text-odoo-text">
    <Popover align="end">
      <template #trigger>
        <button
          type="button"
          class="rounded px-1 tabular-nums hover:bg-odoo-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-odoo-action"
          :aria-label="`Records ${pager.from} to ${pager.to}; change how many are shown`"
        >
          {{ pager.from }}-{{ pager.to }}
        </button>
      </template>
      <template #default="{ close }">
        <div class="p-1" role="listbox" aria-label="Records per page">
          <button
            v-for="n in sizes"
            :key="n"
            type="button"
            role="option"
            :aria-selected="pager.pageSize === n"
            class="flex w-full items-center justify-between gap-6 rounded px-2.5 py-1.5 text-left text-[13px] hover:bg-odoo-hover"
            @click="pager.setPageSize(n); close()"
          >
            {{ n }} per page
            <span v-if="pager.pageSize === n" class="lucide-check size-4 text-odoo-action" aria-hidden="true" />
          </button>
        </div>
      </template>
    </Popover>
    <span class="tabular-nums text-odoo-muted">/ {{ pager.total }}</span>
    <div class="ml-1 flex" role="group" aria-label="Pages">
      <button
        type="button"
        class="o-pager-btn rounded-l"
        aria-label="Previous page"
        :disabled="!pager.hasPrev || pager.loading"
        @click="pager.prev()"
      >
        <span class="lucide-chevron-left size-4" aria-hidden="true" />
      </button>
      <button
        type="button"
        class="o-pager-btn rounded-r border-l border-white"
        aria-label="Next page"
        :disabled="!pager.hasNext || pager.loading"
        @click="pager.next()"
      >
        <span class="lucide-chevron-right size-4" aria-hidden="true" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { Popover } from 'frappe-ui'

defineProps({
  /** useDocList's `pager`. */
  pager: { type: Object, required: true },
  sizes: { type: Array, default: () => [20, 80, 200, 500] },
})
</script>

<style scoped>
.o-pager-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  width: 30px;
  background-color: var(--o-border-light);
  color: var(--o-text);
}
.o-pager-btn:hover:not(:disabled) {
  background-color: var(--o-border);
}
.o-pager-btn:disabled {
  opacity: 0.45;
}
</style>
