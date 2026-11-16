<template>
  <!-- Odoo's field groups (o_group): label on the left, value on the right, in one or two
       columns. Links in the action teal. -->
  <dl class="grid grid-cols-1 gap-x-10 gap-y-1.5 sm:grid-cols-2" :class="columns === 3 && 'lg:grid-cols-3'">
    <div
      v-for="item in visibleItems"
      :key="item.label"
      class="grid min-w-0 grid-cols-[minmax(7rem,38%)_minmax(0,1fr)] items-baseline gap-2 py-0.5"
    >
      <dt class="text-[14px] font-medium text-odoo-strong">{{ item.label }}</dt>
      <dd class="break-words text-[14px] text-odoo-text">
        <a v-if="item.href" :href="item.href" class="o-link">{{ item.value }}</a>
        <RouterLink v-else-if="item.route" :to="item.route" class="o-link">{{ item.value }}</RouterLink>
        <template v-else>{{ item.value ?? '' }}</template>
      </dd>
    </div>
  </dl>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** [{ label, value, href?, route?, hide? }] */
  items: { type: Array, required: true },
  columns: { type: Number, default: 2 },
})
const visibleItems = computed(() => props.items.filter((item) => !item.hide))
</script>
