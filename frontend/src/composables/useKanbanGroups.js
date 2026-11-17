import { reactive, ref, watch } from 'vue'
import { call } from 'frappe-ui'

const COLUMN_PAGE = 40

/**
 * Odoo's grouped kanban: one column per value of a field, each loading its own first records
 * (40, then "Load more") and its count, with the list's current filters and search.
 *
 * @param {object} docList  useDocList's return value (query, doctype, fields)
 * @param {import('vue').Ref<string|null>} groupBy  field to group by, or null
 * @param {object} options  { [field]: [{ value, label }] } the columns for each field
 */
export function useKanbanGroups(docList, groupBy, options) {
  const columns = ref([])
  let run = 0

  async function load() {
    const field = groupBy.value
    const id = ++run
    if (!field || !options[field]) {
      columns.value = []
      return
    }
    columns.value = options[field].map((o) =>
      reactive({ value: o.value, label: o.label, rows: [], count: null, loading: true, error: null, start: 0 }),
    )
    await Promise.all(columns.value.map((col) => fetchColumn(col, field, id, true)))
  }

  async function fetchColumn(col, field, id, first) {
    const filters = [...docList.query.filters, [field, '=', col.value]]
    col.loading = true
    try {
      const [rows, count] = await Promise.all([
        call('frappe.client.get_list', {
          doctype: docList.doctype,
          fields: docList.fields,
          filters,
          or_filters: docList.query.or_filters,
          order_by: docList.query.order_by,
          limit_start: col.start,
          limit_page_length: COLUMN_PAGE,
        }),
        first ? call('frappe.desk.reportview.get_count', { doctype: docList.doctype, filters, or_filters: docList.query.or_filters }) : null,
      ])
      if (id !== run) return // a newer search replaced these columns
      col.rows = first ? rows : [...col.rows, ...rows]
      if (first) col.count = count
      col.start += rows.length
    } catch (e) {
      if (id === run) col.error = e?.messages?.[0] || e?.message || 'Could not load'
    } finally {
      if (id === run) col.loading = false
    }
  }

  function loadMore(col) {
    return fetchColumn(col, groupBy.value, run, false)
  }

  watch([groupBy, () => docList.query.version], load, { immediate: true })

  return { columns, loadMore, reload: load }
}
