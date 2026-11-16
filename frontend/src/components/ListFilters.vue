<template>
  <!-- Odoo's search view: the active filters as facets inside the search box, a typed search
       offered as "Search … for: text" (Enter takes the first), and the toggle that opens the
       Filters panel. Backspace in an empty box removes the last facet. -->
  <div class="flex min-w-0 items-stretch">
    <div
      class="relative flex min-h-[32px] min-w-0 flex-1 flex-wrap items-center gap-1 rounded-l border border-r-0 border-odoo-line bg-white py-0.5 pl-2 pr-1 focus-within:border-odoo-action"
    >
      <span class="lucide-search size-4 shrink-0 text-odoo-muted" aria-hidden="true" />
      <span
        v-for="facet in facets"
        :key="facet.key"
        class="flex max-w-full items-stretch overflow-hidden rounded border border-odoo-line text-[13px]"
      >
        <span class="flex items-center bg-odoo-primary px-1.5 text-white" :title="facet.group">
          <span :class="[facet.icon, 'size-3.5']" aria-hidden="true" />
        </span>
        <span class="truncate bg-odoo-hover px-1.5 py-0.5 text-odoo-text">
          <span v-if="facet.label" class="text-odoo-muted">{{ facet.label }}: </span>{{ facet.value }}
        </span>
        <button
          type="button"
          class="flex items-center bg-odoo-hover px-1 text-odoo-muted hover:text-odoo-strong"
          :aria-label="`Remove ${facet.label || facet.group}: ${facet.value}`"
          @click="facet.remove()"
        >
          <span class="lucide-x size-3.5" aria-hidden="true" />
        </button>
      </span>
      <!-- Dashboard presets ("Showing: …") and similar extra facets -->
      <slot />
      <input
        ref="input"
        v-model="query"
        type="text"
        class="h-7 min-w-[8rem] flex-1 border-0 bg-transparent p-0 text-[14px] text-odoo-strong placeholder:text-odoo-muted focus:ring-0"
        :placeholder="facets.length ? '' : searchPlaceholder"
        :aria-label="searchPlaceholder"
        role="combobox"
        :aria-expanded="suggestions.length > 0"
        aria-autocomplete="list"
        @keydown.down.prevent="move(1)"
        @keydown.up.prevent="move(-1)"
        @keydown.enter.prevent="pick(suggestions[active])"
        @keydown.esc="query = ''"
        @keydown.backspace="removeLast"
      />
      <!-- Beside the search box, e.g. a barcode scan button -->
      <slot name="search-actions" />

      <ul
        v-if="suggestions.length"
        class="absolute left-0 right-0 top-full z-30 mt-px overflow-hidden rounded-b border border-odoo-line bg-white py-1 shadow-lg"
        role="listbox"
      >
        <li
          v-for="(s, i) in suggestions"
          :key="s.key"
          role="option"
          :aria-selected="i === active"
          class="cursor-pointer px-3 py-1.5 text-[14px]"
          :class="i === active ? 'bg-odoo-hover' : ''"
          @mousedown.prevent="pick(s)"
          @mouseenter="active = i"
        >
          Search <b class="font-medium">{{ s.label }}</b> for: <i class="not-italic text-odoo-action">{{ query }}</i>
        </li>
      </ul>
    </div>

    <!-- Filters panel toggle -->
    <Popover v-if="tabs.length || choiceFields.length" align="end">
      <template #trigger>
        <button
          type="button"
          class="flex w-8 items-center justify-center rounded-r border border-odoo-line bg-white text-odoo-muted hover:bg-odoo-hover hover:text-odoo-strong focus:outline-none focus-visible:border-odoo-action"
          aria-label="Filters"
          title="Filters"
        >
          <span class="lucide-chevron-down size-4" aria-hidden="true" />
        </button>
      </template>
      <div class="flex max-h-[70vh] min-w-[15rem] flex-col overflow-y-auto p-3 text-[14px]">
        <div class="mb-1 flex items-center gap-2 font-semibold text-odoo-strong">
          <span class="lucide-filter size-4 text-odoo-primary" aria-hidden="true" /> Filters
        </div>
        <button
          v-for="t in tabs"
          :key="t.value"
          type="button"
          class="flex items-center gap-2 rounded px-2 py-1 text-left hover:bg-odoo-hover"
          :aria-pressed="tab === t.value"
          @click="toggleTab(t.value)"
        >
          <span class="size-4 shrink-0" :class="tab === t.value && 'lucide-check text-odoo-action'" aria-hidden="true" />
          {{ t.label }}
        </button>
        <template v-for="field in choiceFields" :key="field.fieldname">
          <hr class="my-2 border-odoo-hover" />
          <div class="px-2 pb-0.5 text-xs font-medium uppercase tracking-wide text-odoo-muted">{{ field.label }}</div>
          <button
            v-for="option in field.choices"
            :key="option.value"
            type="button"
            class="flex items-center gap-2 rounded px-2 py-1 text-left hover:bg-odoo-hover"
            :aria-pressed="values[field.fieldname] === option.value"
            @click="values[field.fieldname] = values[field.fieldname] === option.value ? '' : option.value"
          >
            <span class="size-4 shrink-0" :class="values[field.fieldname] === option.value && 'lucide-check text-odoo-action'" aria-hidden="true" />
            {{ option.label }}
          </button>
        </template>
      </div>
    </Popover>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Popover } from 'frappe-ui'

const props = defineProps({
  searchPlaceholder: { type: String, default: 'Search…' },
  /** Exclusive filters (Odoo's predefined filters): [{ label, value }] */
  tabs: { type: Array, default: () => [] },
  /**
   * Extra filters: [{ fieldname, label, type?: 'select' | 'text', options? }]. Choice fields
   * are listed in the Filters panel; text fields are offered while typing ("Search X for:").
   */
  fields: { type: Array, default: () => [] },
})

/** { search, tab, ...fields } — the parent turns these into list filters. */
const model = defineModel({ type: Object, default: () => ({}) })

const input = ref(null)
const query = ref('')
const active = ref(0)

// "All" (or the first filter when there is none) is the unfiltered state, shown as no facet.
const allValue = computed(() => (props.tabs.find((t) => t.value === 'all') || props.tabs[0])?.value)
const tab = computed({
  get: () => model.value.tab ?? props.tabs[0]?.value,
  set: (value) => (model.value = { ...model.value, tab: value }),
})
function toggleTab(value) {
  tab.value = tab.value === value && value !== allValue.value ? allValue.value : value
}

const values = reactive(Object.fromEntries(props.fields.map((f) => [f.fieldname, model.value[f.fieldname] ?? ''])))
watch(values, () => (model.value = { ...model.value, ...values }))

/** Options as { label, value }, without the "all" entry (an empty value). */
function choicesOf(field) {
  return (field.options || [])
    .map((o) => (typeof o === 'object' && o !== null ? { label: o.label, value: o.value } : { label: String(o), value: o }))
    .filter((o) => o.value !== '' && o.value != null)
}
const choiceFields = computed(() =>
  props.fields.filter((f) => (f.type || 'select') === 'select').map((f) => ({ ...f, choices: choicesOf(f) })),
)
const textFields = computed(() => props.fields.filter((f) => f.type === 'text'))

const facets = computed(() => {
  const list = []
  const t = props.tabs.find((x) => x.value === tab.value)
  if (t && t.value !== allValue.value) {
    list.push({ key: 'tab', group: 'Filter', icon: 'lucide-filter', value: t.label, remove: () => (tab.value = allValue.value) })
  }
  for (const field of props.fields) {
    const v = values[field.fieldname]
    if (v === '' || v == null) continue
    const label = field.type === 'text' ? v : choicesOf(field).find((o) => o.value === v)?.label ?? v
    list.push({
      key: `f-${field.fieldname}`,
      group: field.label,
      label: field.label,
      icon: field.type === 'text' ? 'lucide-search' : 'lucide-filter',
      value: label,
      remove: () => (values[field.fieldname] = ''),
    })
  }
  if (model.value.search) {
    list.push({
      key: 'search',
      group: 'Search',
      icon: 'lucide-search',
      value: model.value.search,
      remove: () => (model.value = { ...model.value, search: '' }),
    })
  }
  return list
})

// While typing: the main search first, then each text field.
const suggestions = computed(() => {
  if (!query.value.trim()) return []
  return [
    { key: 'search', label: props.searchPlaceholder.replace(/^Search\s*/i, '').replace(/…$/, '') || 'all', target: 'search' },
    ...textFields.value.map((f) => ({ key: f.fieldname, label: f.label, target: f.fieldname })),
  ]
})
watch(query, () => (active.value = 0))

function move(step) {
  const n = suggestions.value.length
  if (n) active.value = (active.value + step + n) % n
}

function pick(suggestion) {
  const text = query.value.trim()
  if (!suggestion || !text) return
  if (suggestion.target === 'search') model.value = { ...model.value, search: text }
  else values[suggestion.target] = text
  query.value = ''
}

function removeLast(event) {
  if (query.value || !facets.value.length) return
  event.preventDefault()
  facets.value[facets.value.length - 1].remove()
}
</script>
