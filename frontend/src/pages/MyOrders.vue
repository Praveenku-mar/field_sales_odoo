<template>
  <!-- Full height: the table fills what is left and scrolls inside its card -->
  <div class="flex h-full flex-col">
    <PageHeader :title="session.retailer?.retailer_name || 'My Orders'" :pager="pager" flush>
      <template #search>
        <ListFilters v-model="model" search-placeholder="Search order" :tabs="tabs" />
      </template>
    </PageHeader>
      <DataTable
        class="min-h-0 flex-1"
        :sort="sort"
        :columns="columns"
        :rows="list.data || []"
        :loading="list.list.loading"
        :row-route="(row) => ({ name: 'MyOrder', params: { name: row.name } })"
        empty-icon="lucide-shopping-cart"
        empty-title="No orders yet"
        empty-description="Orders taken by your sales rep will appear here."
      >
        <template #cell-status="{ row }">
          <StatusPill :status="statusOf(row)" />
        </template>
      </DataTable>
  </div>
</template>

<script setup>
import PageHeader from '@/components/PageHeader.vue'
import ListFilters from '@/components/ListFilters.vue'
import DataTable from '@/components/DataTable.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useSessionStore } from '@/stores/session'
import { useDocList } from '@/composables/useDocList'
import { formatCurrency, formatDate, formatNumber } from '@/utils/format'

const session = useSessionStore()

const tabs = [
  { label: 'All', value: 'all' },
  { label: 'Unpaid', value: 'unpaid' },
  { label: 'Paid', value: 'paid' },
]
const columns = [
  { key: 'name', label: 'Order', sortField: 'name' },
  { key: 'order_date', label: 'Date', sortField: 'order_date', format: formatDate },
  { key: 'invoice_no', label: 'Invoice', format: (v) => v || '—' },
  { key: 'total_qty', label: 'Units', sortField: 'total_qty', sum: true, align: 'right', format: (v) => formatNumber(v) },
  { key: 'grand_total', label: 'Total', sortField: 'grand_total', sum: true, align: 'right', format: (v) => formatCurrency(v) },
  { key: 'status', label: 'Status' },
]

// The retailer's own orders only; the server enforces this (Field Order's permission
// query for a retailer login is its own retailer).
function buildFilters(m) {
  if (m.tab === 'unpaid') return [['docstatus', '!=', 2], ['payment_status', 'not in', ['Paid']]]
  if (m.tab === 'paid') return [['docstatus', '=', 1], ['payment_status', '=', 'Paid']]
  return [['docstatus', '!=', 2]]
}

/** Payment state is what a customer tracks: drafts and cancellations stay as such. */
function statusOf(row) {
  if (row.docstatus === 0) return 'Draft'
  if (row.docstatus === 2) return 'Cancelled'
  return row.payment_status || 'Unpaid'
}

const { model, list, count, pageSize, pager, sort } = useDocList({
  doctype: 'Field Order',
  fields: ['name', 'order_date', 'invoice_no', 'total_qty', 'grand_total', 'docstatus', 'payment_status'],
  orderBy: 'order_date desc, creation desc',
  buildFilters,
  searchFields: ['name', 'invoice_no'],
  initial: { tab: 'all' },
})
</script>
