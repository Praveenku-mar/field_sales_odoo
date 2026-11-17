<template>
  <!-- Odoo's notebook (nav-tabs): bordered tabs over the pages; each page stays mounted so
       unsaved edits survive switching tabs. -->
  <div class="mt-5">
    <div class="flex overflow-x-auto border-b border-odoo-line" role="tablist">
      <button
        v-for="tab in visible"
        :id="`tab-${uid}-${tab.value}`"
        :key="tab.value"
        type="button"
        role="tab"
        class="-mb-px whitespace-nowrap rounded-t border px-4 py-2 text-[14px] focus:outline-none focus-visible:ring-2 focus-visible:ring-odoo-action"
        :class="model === tab.value ? 'border-odoo-line border-b-white bg-white font-medium text-odoo-strong' : 'border-transparent text-odoo-muted hover:text-odoo-strong'"
        :aria-selected="model === tab.value"
        :aria-controls="`pane-${uid}-${tab.value}`"
        @click="model = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>
    <div
      v-for="tab in visible"
      v-show="model === tab.value"
      :id="`pane-${uid}-${tab.value}`"
      :key="tab.value"
      role="tabpanel"
      :aria-labelledby="`tab-${uid}-${tab.value}`"
      class="pt-4"
    >
      <slot :name="tab.value" />
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'

const props = defineProps({
  /** [{ value, label, hide? }] */
  tabs: { type: Array, required: true },
})
const model = defineModel({ type: String, default: null })
const uid = Math.random().toString(36).slice(2, 7)
const visible = computed(() => props.tabs.filter((t) => !t.hide))

// Keep a visible tab selected (a tab can hide when the record changes, e.g. on submit).
watch(
  visible,
  (tabs) => {
    if (!tabs.some((t) => t.value === model.value)) model.value = tabs[0]?.value ?? null
  },
  { immediate: true },
)
</script>
