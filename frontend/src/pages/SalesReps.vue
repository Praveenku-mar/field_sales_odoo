<template>
  <!-- Full height: the table fills what is left and scrolls inside its card -->
  <div class="flex h-full flex-col">
    <PageHeader title="Sales Reps" :pager="kanbanGroupBy ? null : pager" flush>
      <template #actions>
        <Button v-if="session.isManager" label="New Sales Rep" icon-left="lucide-plus" variant="solid" @click="newRepOpen = true" />
      </template>
      <template #search>
        <ListFilters v-model="model" v-model:group-by="groupBy" :groups="view === 'kanban' ? GROUPS : []" search-placeholder="Search name, email, territory" :tabs="tabs" :fields="fields" />
      </template>
      <template #views><ViewSwitcher v-model="view" /></template>
    </PageHeader>
      <DataTable
        v-if="view === 'list'"
        class="min-h-0 flex-1"
        :sort="sort"
        :columns="columns"
        :rows="list.data || []"
        :loading="list.list.loading"
        :row-route="(row) => ({ name: 'SalesRep', params: { name: row.name } })"
        empty-icon="lucide-user-round"
        empty-title="No sales reps found"
      >
        <template #cell-full_name="{ row }">
          <div class="flex items-center gap-2.5">
            <Avatar :label="row.full_name || row.name" :image="row.user_image" size="md" />
            <div class="min-w-0">
              <div class="truncate font-medium text-ink-gray-9">{{ row.full_name || row.name }}</div>
              <div class="truncate text-xs text-ink-gray-5">{{ row.name }}</div>
            </div>
          </div>
        </template>
        <template #cell-order_value="{ row }">
          <span class="tabular-nums">{{ stat(row, 'order_value') == null ? '—' : formatCurrency(stat(row, 'order_value'), undefined, 0) }}</span>
          <div class="text-xs text-ink-gray-5">{{ plural(stat(row, 'orders') || 0, 'order') }}</div>
        </template>
        <template #cell-achievement="{ row }">
          <Achievement :pct="stat(row, 'achievement_pct')" />
        </template>
        <template #cell-active="{ row }">
          <StatusPill :status="row.active ? 'Active' : 'Inactive'" />
        </template>
      </DataTable>
      <KanbanView
        v-else
        :rows="list.data || []"
        :loading="list.list.loading"
        :columns="kanban.columns.value"
        :row-route="(row) => ({ name: 'SalesRep', params: { name: row.name } })"
        empty-icon="lucide-user-round"
        empty-title="No sales reps found"
        @load-more="kanban.loadMore"
      >
        <template #card="{ row }">
          <div class="flex items-center gap-3">
            <Avatar :label="row.full_name || row.name" :image="row.user_image" size="xl" />
            <div class="min-w-0 flex-1">
              <div class="truncate text-[14px] font-semibold text-odoo-strong">{{ row.full_name || row.name }}</div>
              <div class="truncate text-odoo-muted">{{ row.territory || row.name }}</div>
              <div v-if="row.mobile" class="truncate text-xs text-odoo-muted">{{ row.mobile }}</div>
            </div>
            <StatusPill :status="row.active ? 'Active' : 'Inactive'" />
          </div>
          <div class="mt-2 flex items-center justify-between gap-2 text-xs text-odoo-muted">
            <span>{{ stat(row, 'order_value') == null ? '' : `${formatCurrency(stat(row, 'order_value'), undefined, 0)} this month` }}</span>
            <span>{{ plural(stat(row, 'orders') || 0, 'order') }}</span>
          </div>
        </template>
      </KanbanView>
    <NewSalesRepDialog v-model="newRepOpen" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Avatar, Button, createResource } from 'frappe-ui'
import NewSalesRepDialog from '@/components/NewSalesRepDialog.vue'

const newRepOpen = ref(false)
import PageHeader from '@/components/PageHeader.vue'
import ListFilters from '@/components/ListFilters.vue'
import DataTable from '@/components/DataTable.vue'
import StatusPill from '@/components/StatusPill.vue'
import Achievement from '@/components/Achievement.vue'
import { useDocList } from '@/composables/useDocList'
import ViewSwitcher from '@/components/odoo/ViewSwitcher.vue'
import KanbanView from '@/components/odoo/KanbanView.vue'
import { useViewMode } from '@/composables/useViewMode'
import { useKanbanGroups } from '@/composables/useKanbanGroups'
import { useSessionStore } from '@/stores/session'
import { formatCurrency, plural } from '@/utils/format'

const session = useSessionStore()

const tabs = [
  { label: 'Active', value: 'active' },
  { label: 'Inactive', value: 'inactive' },
  { label: 'All', value: 'all' },
]
const fields = [{ fieldname: 'territory', label: 'Territory', type: 'text' }]
const columns = [
  { key: 'full_name', label: 'Sales Rep', sortField: 'full_name' },
  { key: 'territory', label: 'Territory', sortField: 'territory' },
  { key: 'reports_to_name', label: 'Reports To' },
  { key: 'mobile', label: 'Mobile' },
  { key: 'monthly_target', label: 'Monthly Target', sortField: 'monthly_target', sum: true, align: 'right', format: (v) => (v ? formatCurrency(v, undefined, 0) : '—') },
  { key: 'order_value', label: 'This Month', align: 'right' },
  { key: 'achievement', label: 'Achievement', width: '160px' },
  { key: 'active', label: 'Status', sortField: 'active' },
]

function buildFilters(m) {
  const filters = []
  if (m.tab === 'active') filters.push(['active', '=', 1])
  if (m.tab === 'inactive') filters.push(['active', '=', 0])
  if (m.territory) filters.push(['territory', 'like', `%${m.territory}%`])
  return filters
}

const docList = useDocList({
  doctype: 'Sales Rep',
  fields: ['name', 'full_name', 'user.user_image as user_image', 'territory', 'reports_to', 'reports_to.full_name as reports_to_name', 'mobile', 'monthly_target', 'active'],
  orderBy: 'full_name asc',
  buildFilters,
  searchFields: ['full_name', 'name', 'territory', 'mobile'],
  initial: { tab: 'active' },
})
const { model, list, count, pageSize, pager, sort } = docList

// List or kanban (remembered; phones start in kanban), and the kanban's Group By columns.
const view = useViewMode('sales-reps')
const groupBy = ref(null)
const GROUPS = [
  { field: 'active', label: 'Status' },
]
const GROUP_COLUMNS = {
  active: [{ value: 1, label: 'Active' }, { value: 0, label: 'Inactive' }],
}
const kanbanGroupBy = computed(() => (view.value === 'kanban' ? groupBy.value : null))
const kanban = useKanbanGroups(docList, kanbanGroupBy, GROUP_COLUMNS)

// Month-to-date numbers for every rep the user can see, keyed by rep.
const stats = createResource({ url: 'field_sales_odoo.frontend_api.get_rep_month_stats', auto: true })
const stat = (row, key) => stats.data?.[row.name]?.[key] ?? null
</script>
