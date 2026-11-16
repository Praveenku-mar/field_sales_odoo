<template>
  <!-- Odoo 17/18 navbar (o_main_navbar): the app's brand, its menu sections (a link, or a
       dropdown when a section has several pages), and the systray on the right. Phones get a
       menu button that opens the section drawer instead. -->
  <header class="flex h-topbar shrink-0 items-stretch border-b border-odoo-line bg-white px-1 text-[14px] text-odoo-text">
    <button type="button" class="o-nav-item md:hidden" aria-label="Menu" @click="$emit('open-menu')">
      <span class="lucide-menu size-5" aria-hidden="true" />
    </button>

    <RouterLink :to="{ name: homeRoute }" class="o-nav-item min-w-0 gap-2 pr-3" title="Home">
      <img :src="LOGO" alt="" class="size-6 shrink-0 rounded" />
      <span class="truncate text-[16px] font-semibold text-odoo-strong">{{ brand }}</span>
    </RouterLink>

    <nav class="hidden min-w-0 items-stretch md:flex" aria-label="Main menu">
      <template v-for="section in sections" :key="section.label">
        <RouterLink
          v-if="pages(section).length === 1"
          :to="{ name: pages(section)[0].route }"
          class="o-nav-item"
          :class="isActive(section) && 'o-nav-item-active'"
          :aria-current="isActive(section) ? 'page' : undefined"
        >
          {{ section.label }}
          <CountBadge :count="sectionCount(section)" />
        </RouterLink>
        <Dropdown v-else :options="dropdownOptions(section)" align="start">
          <template #default="{ open }">
            <button
              type="button"
              class="o-nav-item"
              :class="(open || isActive(section)) && 'o-nav-item-active'"
              :aria-expanded="open"
            >
              {{ section.label }}
              <CountBadge :count="sectionCount(section)" />
            </button>
          </template>
        </Dropdown>
      </template>
    </nav>

    <div class="flex-1" />

    <!-- Systray -->
    <button
      v-if="!session.isRetailer"
      type="button"
      class="o-nav-item"
      aria-label="Search (Ctrl K)"
      title="Search (Ctrl K)"
      @click="$emit('open-search')"
    >
      <span class="lucide-search size-[18px]" aria-hidden="true" />
    </button>
    <RouterLink
      v-if="!session.isRetailer"
      :to="{ name: 'Notifications' }"
      class="o-nav-item relative"
      :class="route.name === 'Notifications' && 'o-nav-item-active'"
      :aria-label="unread ? `Notifications, ${unread} unread` : 'Notifications'"
    >
      <span class="lucide-bell size-[18px]" aria-hidden="true" />
      <span
        v-if="unread"
        class="absolute right-0.5 top-1.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-odoo-primary px-1 text-[10px] font-semibold leading-none text-white"
      >
        {{ unread }}
      </span>
    </RouterLink>
    <!-- Inside the Shopify admin: no account menu (no logout or desk there) -->
    <UserMenu v-if="!embedded" />
  </header>
</template>

<script setup>
import { computed, defineComponent, h } from 'vue'
import { useRoute } from 'vue-router'
import { Dropdown } from 'frappe-ui'
import UserMenu from './UserMenu.vue'
import { isEmbedded } from '@/shopify/embedded'
import { useSessionStore } from '@/stores/session'
import { menuSections } from '@/utils/nav'

const props = defineProps({
  /** frontend_api.get_sidebar_counts resource (AppLayout's useNavCounts). */
  counts: { type: Object, default: null },
})
defineEmits(['open-search', 'open-menu'])

// Served by Frappe at runtime, not bundled by Vite.
const LOGO = '/assets/field_sales_odoo/images/agamsale-logo.png'

const embedded = isEmbedded()
const session = useSessionStore()
const route = useRoute()

const brand = computed(() => session.store.name || 'Field Sales')
const homeRoute = computed(() => (session.isRetailer ? 'MyOrders' : 'Dashboard'))
const sections = computed(() => menuSections((item) => session.canSee(item)))
const unread = computed(() => props.counts?.data?.unread_notifications || 0)

const pages = (section) => section.items.filter((item) => item !== '-')

function countOf(item) {
  return item.count ? props.counts?.data?.[item.count] || 0 : 0
}
// Only alert counts (failed orders) show on the section; plain totals stay in the dropdown.
function sectionCount(section) {
  return pages(section).reduce((n, item) => n + (item.countTheme === 'red' ? countOf(item) : 0), 0)
}

function isActive(section) {
  return pages(section).some((item) => route.name === item.route || route.meta.parent === item.route)
}

function dropdownOptions(section) {
  const groups = [[]]
  for (const item of section.items) {
    if (item === '-') {
      groups.push([])
      continue
    }
    const n = countOf(item)
    groups[groups.length - 1].push({
      label: n ? `${item.label} (${n})` : item.label,
      route: { name: item.route },
      selected: route.name === item.route || route.meta.parent === item.route,
    })
  }
  return groups
    .filter((g) => g.length)
    .map((options, i) => ({ group: `${section.label}-${i}`, hideLabel: true, options }))
}

/** Odoo's small purple counter beside a menu label. */
const CountBadge = defineComponent({
  props: { count: { type: Number, default: 0 } },
  setup(p) {
    return () =>
      p.count
        ? h(
            'span',
            {
              class:
                'ml-1.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-odoo-primary px-1 text-[10px] font-semibold leading-none text-white',
            },
            String(p.count),
          )
        : null
  },
})
</script>

<style scoped>
.o-nav-item {
  display: inline-flex;
  align-items: center;
  height: 100%;
  padding: 0 0.625rem;
  white-space: nowrap;
  color: var(--o-text);
}
.o-nav-item:hover,
.o-nav-item:focus-visible {
  background-color: var(--o-border-light);
  outline: none;
}
.o-nav-item-active {
  background-color: var(--o-border-light);
  color: var(--o-text-strong);
  font-weight: 500;
}
</style>
