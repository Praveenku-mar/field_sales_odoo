<template>
  <div>
    <PageHeader :title="d.retailer_name || name" :breadcrumbs="[{ label: 'Shops', to: { name: 'Retailers' } }]">
      <template #actions>
        <Button
          v-if="session.isManager"
          label="Edit"
          icon-left="lucide-pencil"
          :disabled="!d.name"
          @click="editOpen = true"
        />
        <Dropdown :options="moreActions">
          <Button variant="ghost" icon="lucide-settings" aria-label="Actions" title="Actions" />
        </Dropdown>
      </template>
    </PageHeader>

    <div v-if="doc.get.error" class="px-5"><div class="fs-card"><EmptyState icon="lucide-circle-alert" title="Shop not found" :description="errorText" /></div></div>

    <FormView v-else :ribbon="d.status === 'Inactive' ? { label: 'Inactive', tone: 'danger' } : null">
      <template #statusbar>
        <Button label="Plan Visit Today" icon-left="lucide-calendar-plus" variant="solid" :loading="planning" :disabled="!d.name || d.status === 'Inactive'" @click="planVisit" />
        <Button v-if="canWrite && ['Draft', 'Failed'].includes(d.sync_status)" label="Sync to Store" icon-left="lucide-refresh-cw" :loading="syncing" @click="syncToStore" />
      </template>
      <template #smart>
        <SmartButton icon="lucide-map-pin-check" :value="summary.data?.visits_30d ?? '—'" label="Visits · 30 days" @click="tab = 'visits'" />
        <SmartButton icon="lucide-shopping-cart" :value="summary.data?.orders_30d ?? '—'" label="Orders · 30 days" @click="tab = 'orders'" />
        <SmartButton
          icon="lucide-indian-rupee"
          :value="summary.data ? formatCurrency(summary.data.value_30d, undefined, 0) : '—'"
          label="Sales · 30 days"
        />
        <SmartButton icon="lucide-calendar-clock" :value="d.last_visit ? relativeDay(d.last_visit) : 'Never'" label="Last visit" />
      </template>

      <div class="mb-4 flex flex-wrap items-end justify-between gap-2">
        <div class="min-w-0">
          <div class="text-[13px] text-odoo-muted">{{ name }}</div>
          <div class="text-[28px] font-semibold leading-tight text-odoo-strong">{{ d.retailer_name || name }}</div>
        </div>
        <StatusPill v-if="d.name" :status="statusLabel" />
      </div>

      <div class="grid grid-cols-1 gap-x-10 gap-y-2 lg:grid-cols-3">
        <div class="space-y-2 lg:col-span-2">
          <SectionCard title="Details">
            <InfoGrid :items="details" :columns="2" />
          </SectionCard>
          <SectionCard title="Address & Location">
            <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <InfoGrid :items="address" :columns="1" />
              <MapEmbed :latitude="d.latitude" :longitude="d.longitude" :title="d.retailer_name" empty-description="Set when the first visit checks in, or in the desk." />
            </div>
          </SectionCard>
        </div>
        <div class="space-y-2">
          <SectionCard title="Store Sync">
            <InfoGrid :items="syncInfo" :columns="1" />
            <div v-if="d.sync_error" class="mt-3 rounded-3 px-3 py-2 text-sm" :class="d.sync_status === 'Failed' ? 'bg-surface-red-1 text-ink-red-5' : 'bg-surface-amber-1 text-ink-amber-7'">
              {{ d.sync_error }}
            </div>
          </SectionCard>

          <!-- Managers only: invite the customer into the app's My Orders view. -->
          <RetailerLoginCard
            v-if="session.isManager"
            :retailer="name"
            :fallback-email="d.email || ''"
            @updated="doc.reload()"
          />
        </div>
      </div>

      <Notebook v-model="tab" :tabs="TABS">
        <template #visits>
          <DataTable boxed :columns="visitColumns" :rows="visits.data || []" :loading="visits.list.loading" :row-route="(r) => ({ name: 'Visit', params: { name: r.name } })" empty-icon="lucide-map-pin" empty-title="No visits yet">
            <template #cell-status="{ value }"><StatusPill :status="value" /></template>
          </DataTable>
        </template>
        <template #orders>
          <DataTable boxed :columns="orderColumns" :rows="orders.data || []" :loading="orders.list.loading" :row-route="(r) => ({ name: 'Order', params: { name: r.name } })" empty-icon="lucide-shopping-cart" empty-title="No orders yet">
            <template #cell-sync_status="{ row }"><StatusPill :status="orderStatus(row)" /></template>
          </DataTable>
        </template>
      </Notebook>
      <template #chatter>
        <Chatter doctype="Retailer" :name="name" :version="d.modified || null" />
      </template>
    </FormView>

    <!-- Managers only: session.isManager gates the Edit button above. -->
    <RetailerDialog v-model="editOpen" :retailer="name" @updated="doc.reload()" />
    <NewOrderDialog v-model="newOrderOpen" :retailer="name" />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Dropdown, createDocumentResource, createListResource, createResource, toast } from 'frappe-ui'
import PageHeader from '@/components/PageHeader.vue'
import FormView from '@/components/odoo/FormView.vue'
import Notebook from '@/components/odoo/Notebook.vue'
import SmartButton from '@/components/odoo/SmartButton.vue'
import Chatter from '@/components/odoo/Chatter.vue'
import SectionCard from '@/components/SectionCard.vue'
import InfoGrid from '@/components/InfoGrid.vue'
import MapEmbed from '@/components/MapEmbed.vue'
import DataTable from '@/components/DataTable.vue'
import StatusPill from '@/components/StatusPill.vue'
import EmptyState from '@/components/EmptyState.vue'
import RetailerDialog from '@/components/RetailerDialog.vue'
import NewOrderDialog from '@/components/NewOrderDialog.vue'
import RetailerLoginCard from '@/components/RetailerLoginCard.vue'
import { useSessionStore } from '@/stores/session'
import { callMethod } from '@/utils/api'
import { formatCurrency, formatDate, formatDateTime, orderStatus, relativeDay, today } from '@/utils/format'

const props = defineProps({ name: { type: String, required: true } })
const router = useRouter()
const session = useSessionStore()

const doc = createDocumentResource({ doctype: 'Retailer', name: props.name, auto: true })
const d = computed(() => doc.doc || {})
const errorText = computed(() => String(doc.get.error?.messages?.[0] || doc.get.error || ''))
const statusLabel = computed(() => (d.value.status === 'Inactive' ? 'Inactive' : d.value.sync_status || 'Draft'))

const rep = createResource({
  url: 'frappe.client.get_value',
  makeParams: () => ({ doctype: 'Sales Rep', filters: d.value.sales_rep, fieldname: 'full_name' }),
})
const summary = createResource({ url: 'field_sales_odoo.api.get_retailer_summary', params: { retailer: props.name }, auto: true })
const visits = createListResource({
  doctype: 'Visit',
  fields: ['name', 'visit_date', 'sales_rep_name', 'status', 'time_on_site_min'],
  filters: { retailer: props.name },
  orderBy: 'visit_date desc',
  pageLength: 5,
  auto: true,
})
const orders = createListResource({
  doctype: 'Field Order',
  fields: ['name', 'order_date', 'grand_total', 'docstatus', 'sync_status'],
  filters: { retailer: props.name, docstatus: ['!=', 2] },
  orderBy: 'order_date desc',
  pageLength: 5,
  auto: true,
})

// Rep name once the document has loaded.
const repName = computed(() => rep.data?.full_name || d.value.sales_rep)
watch(
  () => d.value.sales_rep,
  (value) => value && rep.fetch(),
  { immediate: true },
)

const details = computed(() => [
  { label: 'Owner', value: d.value.owner_name },
  { label: 'Phone', value: d.value.phone, href: d.value.phone && `tel:${d.value.phone}` },
  { label: 'Email', value: d.value.email, href: d.value.email && `mailto:${d.value.email}` },
  { label: 'Type', value: d.value.retailer_type },
  { label: 'Sales Rep', value: repName.value },
  // Indian GST number; retailers without a country predate the field and are Indian.
  ...(!d.value.country || d.value.country === 'India' ? [{ label: 'GSTIN', value: d.value.gstin }] : []),
])
const address = computed(() => [
  { label: 'Address', value: [d.value.address_line1, d.value.address_line2].filter(Boolean).join(', ') },
  { label: 'City', value: d.value.city },
  { label: 'State', value: d.value.state },
  { label: 'Postal Code', value: d.value.pincode },
  { label: 'Country', value: d.value.country },
  { label: 'Geofence', value: d.value.geofence_radius_m ? `${d.value.geofence_radius_m} m` : '50 m (default)' },
])
const syncInfo = computed(() => [
  { label: 'Status', value: d.value.sync_status || 'Draft' },
  { label: 'Platform', value: d.value.platform },
  { label: 'Store customer ID', value: d.value.external_customer_id },
  { label: 'Last synced', value: d.value.last_synced ? formatDateTime(d.value.last_synced) : null },
])
const visitColumns = [
  { key: 'visit_date', label: 'Date', format: formatDate },
  { key: 'sales_rep_name', label: 'Sales Rep' },
  { key: 'time_on_site_min', label: 'On Site', align: 'right', format: (v, r) => (r.status === 'Completed' ? `${v || 0} min` : '—') },
  { key: 'status', label: 'Status' },
]
const orderColumns = [
  { key: 'name', label: 'Order' },
  { key: 'order_date', label: 'Date', format: formatDate },
  { key: 'grand_total', label: 'Total', align: 'right', format: (v) => formatCurrency(v) },
  { key: 'sync_status', label: 'Status' },
]

// Every rep can see every retailer, but only edits those of their hierarchy.
const writePerm = createResource({
  url: 'frappe.client.has_permission',
  params: { doctype: 'Retailer', docname: props.name, perm_type: 'write' },
  auto: true,
})
const canWrite = computed(() => !!writePerm.data?.has_permission)

const moreActions = computed(() => [
  { label: 'New Order', icon: 'lucide-shopping-cart', onClick: () => (newOrderOpen.value = true) },
])

const planning = ref(false)
const editOpen = ref(false)
const newOrderOpen = ref(false)
async function planVisit() {
  planning.value = true
  try {
    const visit = await callMethod('frappe.client.insert', {
      doc: {
        doctype: 'Visit',
        retailer: props.name,
        sales_rep: session.salesRep?.name || d.value.sales_rep,
        visit_date: today(),
      },
    })
    toast.success('Visit planned for today')
    router.push({ name: 'Visit', params: { name: visit.name } })
  } finally {
    planning.value = false
  }
}

const syncing = ref(false)
async function syncToStore() {
  syncing.value = true
  try {
    const r = await callMethod('field_sales_odoo.api.sync_retailers', { names: [props.name] })
    toast.success(r.message)
    setTimeout(() => doc.reload(), 3000)
  } finally {
    syncing.value = false
  }
}

// Odoo form: the notebook under the sheet's groups.
const TABS = [
  { value: 'visits', label: 'Recent Visits' },
  { value: 'orders', label: 'Recent Orders' },
]
const tab = ref('visits')
</script>
