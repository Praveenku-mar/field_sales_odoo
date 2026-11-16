<template>
  <div>
    <PageHeader :title="d.product_title || name" :breadcrumbs="[{ label: 'Products', to: { name: 'Products' } }]" />

    <div v-if="doc.get.error" class="px-5"><div class="fs-card"><EmptyState icon="lucide-circle-alert" title="Product not found" :description="errorText" /></div></div>

    <FormView v-else :ribbon="d.status === 'Archived' ? { label: 'Archived', tone: 'danger' } : null">
      <template #smart>
        <SmartButton icon="lucide-shopping-cart" :value="activity.data?.orders_30d ?? '—'" label="Orders · 30 days" @click="tab = 'orders'" />
        <SmartButton icon="lucide-boxes" :value="activity.data ? formatNumber(activity.data.units_30d) : '—'" label="Units sold · 30 days" />
        <SmartButton icon="lucide-indian-rupee" :value="activity.data ? formatCurrency(activity.data.value_30d, undefined, 0) : '—'" label="Sales · 30 days" />
        <SmartButton
          v-if="d.track_inventory"
          icon="lucide-warehouse"
          :value="formatNumber(d.available_qty)"
          label="In stock"
          @click="tab = 'stock'"
        />
      </template>

      <div class="mb-4 flex gap-5">
        <div class="min-w-0 flex-1">
          <div class="text-[13px] text-odoo-muted">{{ d.variant_title || 'Product' }}</div>
          <div class="text-[28px] font-semibold leading-tight text-odoo-strong">{{ d.product_title || name }}</div>
          <div class="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <span class="text-[22px] font-semibold tabular-nums text-odoo-strong">{{ formatCurrency(d.price) }}</span>
            <span v-if="d.compare_at_price > d.price" class="text-odoo-muted line-through">{{ formatCurrency(d.compare_at_price) }}</span>
            <span v-if="discount" class="text-sm font-medium text-ink-green-7">{{ discount }}% off</span>
            <StatusPill v-if="d.status" :status="d.status" />
          </div>
          <div class="mt-1 flex items-center gap-2">
            <span class="text-odoo-muted">Stock:</span>
            <span v-if="!d.track_inventory" class="text-odoo-text">Not tracked (always available)</span>
            <template v-else>
              <span class="font-medium tabular-nums" :class="stock.class">{{ formatNumber(d.available_qty) }}</span>
              <StatusPill :status="stock.status" :label="stock.label" />
            </template>
          </div>
        </div>
        <!-- Odoo shows the product image at the sheet's top right -->
        <img v-if="d.image" :src="d.image" :alt="d.product_title" class="size-28 shrink-0 rounded border border-odoo-line object-cover" />
        <div v-else class="flex size-28 shrink-0 items-center justify-center rounded bg-odoo-hover">
          <span class="lucide-package size-10 text-odoo-muted" aria-hidden="true" />
        </div>
      </div>

      <div class="grid grid-cols-1 gap-x-10 gap-y-2 lg:grid-cols-3">
        <div class="lg:col-span-2">
          <SectionCard title="General Information">
            <InfoGrid :items="details" :columns="2" />
          </SectionCard>
        </div>
        <SectionCard title="Store Link">
          <InfoGrid :items="storeInfo" :columns="1" />
        </SectionCard>
      </div>

      <Notebook v-model="tab" :tabs="tabs">
        <template #orders>
          <DataTable
            boxed
            :columns="orderColumns"
            :rows="activity.data?.recent_orders || []"
            :loading="activity.loading"
            :row-route="(r) => ({ name: 'Order', params: { name: r.name } })"
            empty-icon="lucide-shopping-cart"
            empty-title="Not ordered yet"
          >
            <template #cell-sync_status="{ row }"><StatusPill :status="orderStatus(row)" /></template>
          </DataTable>
          <p class="mt-2 text-xs text-odoo-muted">Submitted orders you can see.</p>
        </template>
        <template #stock>
          <DataTable boxed :columns="locationColumns" :rows="locationStock.data || []">
            <template #cell-available_qty="{ row }">
              <span :class="stockOf(row).class">{{ formatNumber(row.available_qty) }}</span>
            </template>
          </DataTable>
        </template>
        <template #variants>
          <DataTable boxed :columns="variantColumns" :rows="activity.data?.variants || []" :row-route="(r) => ({ name: 'Product', params: { name: r.name } })">
            <template #cell-available_qty="{ row }">
              <span v-if="!row.track_inventory" class="text-odoo-muted">Not tracked</span>
              <span v-else :class="stockOf(row).class">{{ formatNumber(row.available_qty) }}</span>
            </template>
          </DataTable>
        </template>
      </Notebook>
    </FormView>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Button, createDocumentResource, createListResource, createResource } from 'frappe-ui'
import PageHeader from '@/components/PageHeader.vue'
import FormView from '@/components/odoo/FormView.vue'
import Notebook from '@/components/odoo/Notebook.vue'
import SmartButton from '@/components/odoo/SmartButton.vue'
import SectionCard from '@/components/SectionCard.vue'
import InfoGrid from '@/components/InfoGrid.vue'
import DataTable from '@/components/DataTable.vue'
import StatusPill from '@/components/StatusPill.vue'
import EmptyState from '@/components/EmptyState.vue'
import { formatCurrency, formatDate, formatDateTime, formatNumber, orderStatus } from '@/utils/format'

// Same threshold as the desk's Platform Product list.
const LOW_STOCK = 5

const props = defineProps({ name: { type: String, required: true } })

const doc = createDocumentResource({ doctype: 'Platform Product', name: props.name, auto: true })
const d = computed(() => doc.doc || {})
const errorText = computed(() => String(doc.get.error?.messages?.[0] || doc.get.error || ''))

const activity = createResource({
  url: 'field_sales_odoo.frontend_api.get_product_activity',
  params: { product: props.name },
  auto: true,
})

// Stock at each location the shop sells from (the figure above is the default location's).
const locationStock = createListResource({
  doctype: 'Product Stock',
  fields: ['name', 'location_id', 'location_name', 'available_qty', 'stock_updated_at'],
  filters: { product: props.name },
  orderBy: 'location_name asc',
  pageLength: 50,
  auto: true,
})

function stockOf(row) {
  const qty = row.available_qty || 0
  if (qty <= 0) return { status: 'Failed', label: 'Out of Stock', class: 'text-ink-red-5' }
  if (qty <= LOW_STOCK) return { status: 'Pending', label: 'Low Stock', class: 'text-ink-amber-7' }
  return { status: 'Synced', label: 'In Stock', class: 'text-ink-green-7' }
}
const stock = computed(() => stockOf(d.value))

const discount = computed(() =>
  d.value.compare_at_price > d.value.price ? Math.round((1 - d.value.price / d.value.compare_at_price) * 100) : 0,
)

const details = computed(() => [
  { label: 'SKU', value: d.value.sku },
  { label: 'Barcode', value: d.value.barcode },
  { label: 'Collection', value: d.value.collection },
  { label: 'Unit', value: d.value.uom },
  { label: 'Variant', value: d.value.variant_title },
  { label: 'Status', value: d.value.status },
])
const storeInfo = computed(() => [
  { label: 'Platform', value: d.value.platform },
  { label: 'Product ID', value: d.value.external_product_id },
  { label: 'Variant ID', value: d.value.external_variant_id },
  { label: 'Inventory item', value: d.value.external_inventory_id, hide: !d.value.track_inventory },
  { label: 'Stock location', value: d.value.location_id, hide: !d.value.track_inventory },
  { label: 'Last synced', value: d.value.last_synced ? formatDateTime(d.value.last_synced) : null },
])

const variantColumns = [
  { key: 'variant_title', label: 'Variant', format: (v) => v || 'Default' },
  { key: 'sku', label: 'SKU', format: (v) => v || '—' },
  { key: 'price', label: 'Price', align: 'right', format: (v) => formatCurrency(v) },
  { key: 'available_qty', label: 'Stock', align: 'right' },
]
const locationColumns = [
  { key: 'location_name', label: 'Location', format: (v, row) => v || row.location_id },
  { key: 'available_qty', label: 'Available', align: 'right' },
  { key: 'stock_updated_at', label: 'Updated', format: (v) => (v ? formatDateTime(v) : '—') },
]
const orderColumns = [
  { key: 'name', label: 'Order' },
  { key: 'retailer_name', label: 'Shop' },
  { key: 'order_date', label: 'Date', format: formatDate },
  { key: 'qty', label: 'Qty', align: 'right', format: (v) => formatNumber(v) },
  { key: 'amount', label: 'Amount', align: 'right', format: (v) => formatCurrency(v) },
  { key: 'sync_status', label: 'Status' },
]

// Odoo form: the notebook's pages (stock and variants only when there are some).
const tab = ref('orders')
const tabs = computed(() => [
  { value: 'orders', label: 'Recent Orders' },
  { value: 'stock', label: 'Stock by Location', hide: !(d.value.track_inventory && locationStock.data?.length) },
  { value: 'variants', label: `Other Variants (${activity.data?.variants?.length || 0})`, hide: !activity.data?.variants?.length },
])
</script>
