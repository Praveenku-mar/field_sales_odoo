import { computed, reactive, ref, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { getPreference, setPreference } from '@/utils/storage'

/**
 * A filterable list of one doctype, one page at a time (Odoo's pager: "1-80 / 240"), plus
 * its total count. Goes through frappe.client.get_list, so desk permissions (and the Sales
 * Rep hierarchy) apply.
 *
 * A `preset` (key of frontend_api.get_attention_presets) adds the server's filters for that
 * dashboard card, so the list shows exactly what the card counted. The page's own
 * filters/search narrow it further.
 *
 * @param {object} options
 * @param {string} options.doctype
 * @param {string[]} options.fields
 * @param {string} options.orderBy  default sort, e.g. "order_date desc, creation desc"
 * @param {(model: object) => Array} options.buildFilters  ListFilters model -> frappe filters
 * @param {string[]} [options.searchFields]  fields the search box matches (any of them)
 * @param {object} [options.initial]  initial ListFilters model
 * @param {number} [options.pageLength]  default rows per page; the user's pick (the pager's
 *   limit) is remembered per doctype in this browser
 * @param {string|null} [options.preset]  dashboard preset key (e.g. from ?preset=)
 *
 * @returns {{ model, list, count, refresh, presetLabel, pageSize, pager, sort }}
 *   `list` keeps the shape pages already use: `data`, `list.loading`, `hasNextPage`, `next()`,
 *   `reload()`. `pager` drives components/odoo/Pager.vue; `sort` the list view's headers.
 */
export function useDocList({
  doctype,
  fields,
  orderBy,
  buildFilters,
  searchFields = [],
  initial = {},
  pageLength = 80,
  preset = null,
}) {
  // Replaced wholesale by ListFilters (v-model), so a ref, not a reactive.
  const model = ref({ search: '', ...initial })

  // Rows per page. Browser storage is only a convenience: it may be unavailable.
  const storageKey = `field_sales:page_length:${doctype}`
  const pageSize = ref(readPageSize(storageKey) || pageLength)
  const page = ref(0)

  // Not cached: a cached resource is shared between page visits and keeps the
  // first visit's callbacks, so a second visit's list would never load.
  const presetResource = createResource({
    url: 'field_sales_odoo.frontend_api.get_list_preset',
    params: { key: preset },
    auto: !!preset,
  })
  const presetLabel = computed(() => (preset ? presetResource.data?.label || '…' : null))

  const filters = () => [...(preset ? presetResource.data?.filters || [] : []), ...buildFilters(model.value)]
  const orFilters = () =>
    model.value.search ? searchFields.map((field) => [field, 'like', `%${model.value.search}%`]) : []

  // A header click sorts by that field; clicking it again reverses it. No field: the default.
  const sort = reactive({
    field: null,
    order: 'asc',
    by(field) {
      if (sort.field === field) sort.order = sort.order === 'asc' ? 'desc' : 'asc'
      else Object.assign(sort, { field, order: 'asc' })
      refresh()
    },
  })

  // The filters of the current search, fixed when it is run (paging keeps them).
  let current = { filters: [], or_filters: [] }

  const rows = createResource({
    url: 'frappe.client.get_list',
    makeParams: () => ({
      doctype,
      fields,
      filters: current.filters,
      or_filters: current.or_filters,
      order_by: sort.field ? `${sort.field} ${sort.order}` : orderBy,
      limit_start: page.value * pageSize.value,
      limit_page_length: pageSize.value,
    }),
  })
  const count = createResource({
    url: 'frappe.desk.reportview.get_count',
    makeParams: () => ({ doctype, filters: current.filters, or_filters: current.or_filters }),
  })

  /** Run the search again from the first page (filters, search, page size or sort changed). */
  function refresh() {
    // With a preset, wait for its filters: an unfiltered first page would flash the wrong rows.
    if (preset && !presetResource.data) return
    current = { filters: filters(), or_filters: orFilters() }
    page.value = 0
    rows.reload()
    count.reload()
  }

  function goTo(n) {
    const last = Math.max(0, Math.ceil((count.data || 0) / pageSize.value) - 1)
    const target = Math.min(Math.max(0, n), last)
    if (target === page.value) return
    page.value = target
    rows.reload()
  }

  const total = computed(() => count.data ?? null)
  const hasNextPage = computed(() => total.value != null && (page.value + 1) * pageSize.value < total.value)

  // What the pages read: the shape they were written against.
  const list = reactive({
    data: computed(() => rows.data || []),
    list: computed(() => ({ loading: rows.loading })),
    loading: computed(() => rows.loading),
    hasNextPage,
    next: () => goTo(page.value + 1),
    prev: () => goTo(page.value - 1),
    reload: () => {
      rows.reload()
      count.reload()
    },
  })

  const pager = reactive({
    total,
    loading: computed(() => rows.loading),
    from: computed(() => (total.value ? page.value * pageSize.value + 1 : 0)),
    to: computed(() => Math.min((page.value + 1) * pageSize.value, total.value || 0)),
    pageSize,
    hasPrev: computed(() => page.value > 0),
    hasNext: hasNextPage,
    next: () => goTo(page.value + 1),
    prev: () => goTo(page.value - 1),
    setPageSize: (n) => (pageSize.value = n),
  })

  watch(model, refresh, { deep: true })

  // A new page size reloads from the first row.
  watch(pageSize, (size) => {
    setPreference(storageKey, size)
    refresh()
  })

  // Load the list once this page's preset filters have arrived.
  watch(
    () => presetResource.data,
    (data) => {
      if (!data) return
      if (data.doctype !== doctype) {
        console.error(`Preset ${preset} is for ${data.doctype}, not ${doctype}`)
        return
      }
      refresh()
    },
  )
  if (!preset) refresh()

  return { model, list, count, refresh, presetLabel, pageSize, pager, sort }
}

function readPageSize(key) {
  return Number(getPreference(key)) || null
}
