<template>
  <!-- A dashboard card's filter, as an Odoo search facet. -->
  <span v-if="label" class="flex max-w-full items-stretch overflow-hidden rounded border border-odoo-line text-[13px]">
    <span class="flex items-center bg-odoo-primary px-1.5 text-white"><span class="lucide-star size-3.5" aria-hidden="true" /></span>
    <span class="truncate bg-odoo-hover px-1.5 py-0.5 text-odoo-text">{{ label }}</span>
    <button type="button" class="flex items-center bg-odoo-hover px-1 text-odoo-muted hover:text-odoo-strong" :aria-label="`Remove ${label}`" title="Show all" @click="clear">
      <span class="lucide-x size-3.5" aria-hidden="true" />
    </button>
  </span>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'

defineProps({ label: { type: String, default: null } })

const route = useRoute()
const router = useRouter()

/** Drop ?preset= (and the tab it chose), showing the page's normal list. */
function clear() {
  const query = { ...route.query }
  delete query.preset
  delete query.tab
  router.replace({ query })
}
</script>
