<template>
  <!-- Full height: the table fills what is left and scrolls inside its card -->
  <div class="flex h-full flex-col">
    <PageHeader title="Visits" :pager="pageTab === 'visits' && !kanbanGroupBy ? pager : null" flush>
      <template #actions>
        <Button v-if="pageTab === 'visits'" label="New Visit" icon-left="lucide-plus" variant="solid" @click="newVisitOpen = true" />
      </template>
      <template v-if="pageTab === 'visits'" #search>
        <ListFilters v-model="model" v-model:group-by="groupBy" :groups="view === 'kanban' ? GROUPS : []" search-placeholder="Search shop" :tabs="tabs" :fields="fields">
          <PresetChip :label="presetLabel" />
        </ListFilters>
      </template>
      <template v-if="pageTab === 'visits'" #views><ViewSwitcher v-model="view" /></template>
    </PageHeader>
    <div v-if="session.isManager" class="shrink-0 border-b border-odoo-line bg-white px-4 py-2"><TabButtons v-model="pageTab" :options="pageTabs" /></div>
    <VisitImport v-if="pageTab === 'import'" />
    <div v-show="pageTab === 'visits'" class="flex min-h-0 flex-1 flex-col">
      <DataTable
        v-if="view === 'list'"
        class="min-h-0 flex-1"
        :sort="sort"
        :columns="columns"
        :rows="list.data || []"
        :loading="list.list.loading"
        :row-route="(row) => ({ name: 'Visit', params: { name: row.name } })"
        empty-icon="lucide-map-pin-check"
        empty-title="No visits found"
      >
        <template #cell-retailer_name="{ row }">
          <div class="font-medium text-ink-gray-9">{{ row.retailer_name }}</div>
          <div class="text-xs text-ink-gray-5">{{ [row.name, row.city].filter(Boolean).join(' · ') }}</div>
        </template>
        <template #cell-status="{ value }"><StatusPill :status="value" /></template>
        <template #cell-within_geofence="{ row }">
          <span v-if="!row.check_in_time" class="text-ink-gray-4">—</span>
          <span v-else :class="row.within_geofence ? 'text-ink-green-7' : 'text-ink-amber-7'">
            {{ row.within_geofence ? 'Inside' : `${Math.round(row.distance_from_retailer_m || 0)} m away` }}
          </span>
        </template>
      </DataTable>
      <KanbanView
        v-else
        :rows="list.data || []"
        :loading="list.list.loading"
        :columns="kanban.columns.value"
        :row-route="(row) => ({ name: 'Visit', params: { name: row.name } })"
        empty-icon="lucide-map-pin-check"
        empty-title="No visits found"
        @load-more="kanban.loadMore"
      >
        <template #card="{ row }">
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <div class="truncate text-[14px] font-semibold text-odoo-strong">{{ row.retailer_name }}</div>
              <div class="truncate text-odoo-muted">
                {{ formatDate(row.visit_date) }}<template v-if="row.check_in_time"> · {{ formatTime(row.check_in_time) }}</template>
              </div>
              <div v-if="row.city" class="truncate text-xs text-odoo-muted">{{ row.city }}</div>
            </div>
            <StatusPill :status="row.status" />
          </div>
          <div class="mt-2 flex items-center justify-between gap-2 text-xs text-odoo-muted">
            <span>{{ row.status === 'Completed' ? `${row.time_on_site_min || 0} min on site` : '' }}</span>
            <Avatar v-if="row.sales_rep_name" :label="row.sales_rep_name" size="sm" :title="row.sales_rep_name" />
          </div>
        </template>
      </KanbanView>
    </div>
    <VisitDialog v-model="newVisitOpen" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Avatar, Button, TabButtons } from 'frappe-ui'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import ListFilters from '@/components/ListFilters.vue'
import PresetChip from '@/components/PresetChip.vue'
import DataTable from '@/components/DataTable.vue'
import StatusPill from '@/components/StatusPill.vue'
import VisitDialog from '@/components/VisitDialog.vue'
import VisitImport from '@/components/VisitImport.vue'
import { useDocList } from '@/composables/useDocList'
import ViewSwitcher from '@/components/odoo/ViewSwitcher.vue'
import KanbanView from '@/components/odoo/KanbanView.vue'
import { useViewMode } from '@/composables/useViewMode'
import { useKanbanGroups } from '@/composables/useKanbanGroups'
import { useSessionStore } from '@/stores/session'
import { formatDate, formatTime, today } from '@/utils/format'

const session = useSessionStore()
const newVisitOpen = ref(false)

// Page tab, kept in the URL (?tab=import) so a refresh or a link opens it. The list below
// stays mounted (hidden) while importing, so its filters are not lost. Importing is for
// Sales Managers / System Managers only (the server checks too).
const pageTabs = [
  { label: 'Visits', value: 'visits' },
  { label: 'Import from Excel', value: 'import' },
]
const route = useRoute()
const router = useRouter()
const pageTab = computed({
  get: () => (session.isManager && route.query.tab === 'import' ? 'import' : 'visits'),
  set: (value) => router.replace({ query: value === 'import' ? { tab: 'import' } : {} }),
})

const tabs = [
  { label: 'Today', value: 'today' },
  { label: 'Upcoming', value: 'upcoming' },
  { label: 'Past', value: 'past' },
  { label: 'All', value: 'all' },
]
const fields = [{ fieldname: 'status', label: 'Status', options: ['', 'Planned', 'In Progress', 'Completed', 'Cancelled'] }]
const columns = [
  { key: 'retailer_name', label: 'Shop', sortField: 'retailer_name' },
  { key: 'sales_rep_name', label: 'Sales Rep', sortField: 'sales_rep_name' },
  { key: 'visit_date', label: 'Date', sortField: 'visit_date', format: formatDate },
  { key: 'check_in_time', label: 'Check-in', sortField: 'check_in_time', format: (v) => (v ? formatTime(v) : '—') },
  { key: 'time_on_site_min', label: 'On Site', sortField: 'time_on_site_min', align: 'right', format: (v, row) => (row.status === 'Completed' ? `${v || 0} min` : '—') },
  { key: 'within_geofence', label: 'Geofence' },
  { key: 'status', label: 'Status', sortField: 'status' },
]

function buildFilters(m) {
  const filters = []
  if (m.tab === 'today') filters.push(['visit_date', '=', today()])
  if (m.tab === 'upcoming') filters.push(['visit_date', '>', today()])
  if (m.tab === 'past') filters.push(['visit_date', '<', today()])
  if (m.status) filters.push(['status', '=', m.status])
  return filters
}

const docList = useDocList({
  doctype: 'Visit',
  fields: ['name', 'retailer_name', 'city', 'sales_rep_name', 'visit_date', 'status', 'check_in_time', 'time_on_site_min', 'within_geofence', 'distance_from_retailer_m'],
  orderBy: 'visit_date desc, modified desc',
  buildFilters,
  searchFields: ['retailer_name', 'name', 'city', 'sales_rep_name'],
  // ?preset=… (dashboard cards) shows exactly what the card counted, under the "All" tab;
  // ?tab=… opens a tab directly.
  initial: { tab: route.query.preset ? 'all' : (route.query.tab !== 'import' && route.query.tab) || 'today' },
  preset: route.query.preset || null,
})
const { model, list, count, presetLabel, pageSize, pager, sort } = docList

// List or kanban (remembered; phones start in kanban), and the kanban's Group By columns.
const view = useViewMode('visits')
const groupBy = ref(null)
const GROUPS = [
  { field: 'status', label: 'Status' },
]
const GROUP_COLUMNS = {
  status: [{ value: 'Planned', label: 'Planned' }, { value: 'In Progress', label: 'In Progress' }, { value: 'Completed', label: 'Completed' }, { value: 'Cancelled', label: 'Cancelled' }],
}
const kanbanGroupBy = computed(() => (view.value === 'kanban' ? groupBy.value : null))
const kanban = useKanbanGroups(docList, kanbanGroupBy, GROUP_COLUMNS)
</script>
