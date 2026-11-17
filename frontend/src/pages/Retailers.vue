<template>
  <!-- Full height: the table fills what is left and scrolls inside its card -->
  <div class="flex h-full flex-col">
    <PageHeader title="Shops" :pager="kanbanGroupBy ? null : pager" flush>
      <template #actions>
        <Button label="New Shop" icon-left="lucide-plus" variant="solid" @click="newRetailerOpen = true" />
      </template>
      <template #search>
        <ListFilters v-model="model" v-model:group-by="groupBy" :groups="view === 'kanban' ? GROUPS : []" search-placeholder="Search name, city, phone" :tabs="tabs" :fields="fields">
          <PresetChip :label="presetLabel" />
        </ListFilters>
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
        :row-route="(row) => ({ name: 'Retailer', params: { name: row.name } })"
        empty-icon="lucide-store"
        empty-title="No shops found"
      >
        <template #cell-retailer_name="{ row }">
          <div class="font-medium text-ink-gray-9">{{ row.retailer_name }}</div>
          <div class="text-xs text-ink-gray-5">{{ [row.name, row.city].filter(Boolean).join(' · ') }}</div>
        </template>
        <template #cell-last_visit="{ value }">
          <span :class="lastVisitClass(value)">{{ relativeDay(value) }}</span>
        </template>
        <template #cell-sync_status="{ row }">
          <StatusPill :status="row.status === 'Inactive' ? 'Inactive' : row.sync_status || 'Draft'" />
        </template>
      </DataTable>
      <KanbanView
        v-else
        :rows="list.data || []"
        :loading="list.list.loading"
        :columns="kanban.columns.value"
        :row-route="(row) => ({ name: 'Retailer', params: { name: row.name } })"
        empty-icon="lucide-store"
        empty-title="No shops found"
        @load-more="kanban.loadMore"
      >
        <template #card="{ row }">
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <div class="truncate text-[14px] font-semibold text-odoo-strong">{{ row.retailer_name }}</div>
              <div class="truncate text-odoo-muted">{{ [row.retailer_type, row.city].filter(Boolean).join(' · ') || row.name }}</div>
              <div v-if="row.phone" class="truncate text-odoo-muted">{{ row.phone }}</div>
            </div>
            <StatusPill :status="row.status === 'Inactive' ? 'Inactive' : row.sync_status || 'Draft'" />
          </div>
          <div class="mt-2 flex items-center justify-between gap-2 text-xs">
            <span :class="lastVisitClass(row.last_visit)">Last visit: {{ relativeDay(row.last_visit) }}</span>
            <Avatar v-if="row.sales_rep_name" :label="row.sales_rep_name" size="sm" :title="row.sales_rep_name" />
          </div>
        </template>
      </KanbanView>
    <RetailerDialog v-model="newRetailerOpen" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Avatar, Button } from 'frappe-ui'
import { useRoute } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import ListFilters from '@/components/ListFilters.vue'
import PresetChip from '@/components/PresetChip.vue'
import DataTable from '@/components/DataTable.vue'
import StatusPill from '@/components/StatusPill.vue'
import RetailerDialog from '@/components/RetailerDialog.vue'
import { useDocList } from '@/composables/useDocList'
import ViewSwitcher from '@/components/odoo/ViewSwitcher.vue'
import KanbanView from '@/components/odoo/KanbanView.vue'
import { useViewMode } from '@/composables/useViewMode'
import { useKanbanGroups } from '@/composables/useKanbanGroups'
import { daysAgo, relativeDay } from '@/utils/format'

const newRetailerOpen = ref(false)

const tabs = [
  { label: 'Active', value: 'Active' },
  { label: 'Inactive', value: 'Inactive' },
  { label: 'All', value: 'all' },
]
const fields = [
  { fieldname: 'retailer_type', label: 'Type', options: ['', 'Kirana', 'Supermarket', 'Wholesaler', 'Medical', 'Other'] },
  { fieldname: 'sync_status', label: 'Sync', options: ['', 'Draft', 'Pending', 'Synced', 'Failed'] },
]
const columns = [
  { key: 'retailer_name', label: 'Shop', sortField: 'retailer_name' },
  { key: 'retailer_type', label: 'Type', sortField: 'retailer_type' },
  { key: 'sales_rep_name', label: 'Sales Rep' },
  { key: 'phone', label: 'Phone' },
  { key: 'last_visit', label: 'Last Visit', sortField: 'last_visit' },
  { key: 'sync_status', label: 'Status', sortField: 'sync_status' },
]

function buildFilters(m) {
  const filters = []
  if (m.tab === 'Active' || m.tab === 'Inactive') filters.push(['status', '=', m.tab])
  if (m.retailer_type) filters.push(['retailer_type', '=', m.retailer_type])
  if (m.sync_status) filters.push(['sync_status', '=', m.sync_status])
  return filters
}

const route = useRoute()
const docList = useDocList({
  doctype: 'Retailer',
  fields: ['name', 'retailer_name', 'city', 'retailer_type', 'sales_rep', 'sales_rep.full_name as sales_rep_name', 'phone', 'last_visit', 'status', 'sync_status'],
  orderBy: 'retailer_name asc',
  buildFilters,
  searchFields: ['retailer_name', 'name', 'city', 'phone', 'owner_name'],
  // ?preset=… (dashboard cards) shows exactly what the card counted, under the "All" tab;
  // ?tab=… opens a tab directly.
  initial: { tab: route.query.preset ? 'all' : route.query.tab || 'Active' },
  preset: route.query.preset || null,
})
const { model, list, count, presetLabel, pageSize, pager, sort } = docList

// List or kanban (remembered; phones start in kanban), and the kanban's Group By columns.
const view = useViewMode('retailers')
const groupBy = ref(null)
const GROUPS = [
  { field: 'sync_status', label: 'Sync' },
  { field: 'retailer_type', label: 'Type' },
  { field: 'status', label: 'Status' },
]
const GROUP_COLUMNS = {
  sync_status: [{ value: 'Draft', label: 'Draft' }, { value: 'Pending', label: 'Pending' }, { value: 'Synced', label: 'Synced' }, { value: 'Failed', label: 'Failed' }],
  retailer_type: [{ value: 'Kirana', label: 'Kirana' }, { value: 'Supermarket', label: 'Supermarket' }, { value: 'Wholesaler', label: 'Wholesaler' }, { value: 'Medical', label: 'Medical' }, { value: 'Other', label: 'Other' }],
  status: [{ value: 'Active', label: 'Active' }, { value: 'Inactive', label: 'Inactive' }],
}
const kanbanGroupBy = computed(() => (view.value === 'kanban' ? groupBy.value : null))
const kanban = useKanbanGroups(docList, kanbanGroupBy, GROUP_COLUMNS)

function lastVisitClass(value) {
  const days = daysAgo(value)
  return days === null || days > 30 ? 'text-ink-red-5' : days > 7 ? 'text-ink-amber-7' : 'text-ink-gray-8'
}
</script>
