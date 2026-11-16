<template>
  <!-- Phones: Odoo's menu drawer. The same sections as the top bar, every page listed under
       its section. -->
  <Teleport to="body">
    <Transition name="o-drawer">
      <div v-if="open" class="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true" aria-label="Menu">
        <div class="absolute inset-0 bg-black/30" @click="close" />
        <nav class="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col overflow-y-auto bg-white shadow-xl">
          <div class="flex h-topbar shrink-0 items-center justify-between border-b border-odoo-line px-4">
            <span class="text-[16px] font-semibold text-odoo-strong">{{ session.store.name || 'Field Sales' }}</span>
            <button type="button" class="p-1 text-odoo-muted" aria-label="Close menu" @click="close">
              <span class="lucide-x size-5" aria-hidden="true" />
            </button>
          </div>
          <div v-for="section in sections" :key="section.label" class="border-b border-odoo-hover py-2">
            <div v-if="pages(section).length > 1" class="px-4 pb-1 pt-1 text-xs font-semibold uppercase tracking-wide text-odoo-muted">
              {{ section.label }}
            </div>
            <RouterLink
              v-for="item in pages(section)"
              :key="item.route"
              :to="{ name: item.route }"
              class="flex items-center gap-3 px-4 py-2.5 text-[15px] text-odoo-text hover:bg-odoo-hover"
              :class="isActive(item) && 'bg-odoo-hover font-medium text-odoo-strong'"
              @click="close"
            >
              <span :class="[item.icon, 'size-5 text-odoo-muted']" aria-hidden="true" />
              <span class="flex-1">{{ item.label }}</span>
              <span v-if="countOf(item)" class="rounded-full bg-odoo-primary px-1.5 text-[11px] font-semibold text-white">{{ countOf(item) }}</span>
            </RouterLink>
          </div>
        </nav>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { menuSections } from '@/utils/nav'

const props = defineProps({
  counts: { type: Object, default: null },
})
const open = defineModel({ type: Boolean, default: false })

const session = useSessionStore()
const route = useRoute()
const sections = computed(() => menuSections((item) => session.canSee(item)))
const pages = (section) => section.items.filter((item) => item !== '-')
const countOf = (item) => (item.count ? props.counts?.data?.[item.count] || 0 : 0)
const isActive = (item) => route.name === item.route || route.meta.parent === item.route

function close() {
  open.value = false
}
// Escape closes it, as any dialog.
function onKey(e) {
  if (open.value && e.key === 'Escape') close()
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
.o-drawer-enter-active,
.o-drawer-leave-active {
  transition: opacity 0.15s ease;
}
.o-drawer-enter-from,
.o-drawer-leave-to {
  opacity: 0;
}
</style>
