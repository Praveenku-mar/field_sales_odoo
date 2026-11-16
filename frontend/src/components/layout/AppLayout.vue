<template>
  <!-- Odoo web client frame: the navbar with the app's menus across the top, the page under
       it at full width. Phones open the menus from a drawer. -->
  <div class="flex h-full flex-col overflow-hidden bg-desk-bg">
    <!-- Inside the Shopify admin the admin's own sidebar carries the navigation -->
    <EmbeddedNav v-if="embedded" />
    <TopBar :counts="counts" @open-search="searchOpen = true" @open-menu="menuOpen = true" />
    <main class="min-h-0 flex-1 overflow-y-auto">
      <slot />
    </main>
    <MobileMenu v-model="menuOpen" :counts="counts" />
    <CommandPalette v-model="searchOpen" />
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import TopBar from './TopBar.vue'
import MobileMenu from './MobileMenu.vue'
import { useNavCounts } from '@/composables/useNavCounts'
import CommandPalette from './CommandPalette.vue'
import EmbeddedNav from '@/shopify/EmbeddedNav.vue'
import { isEmbedded } from '@/shopify/embedded'

const embedded = isEmbedded()

const counts = useNavCounts()
const menuOpen = ref(false)
const searchOpen = ref(false)

// Ctrl+K / Cmd+K opens the command palette from anywhere.
function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    searchOpen.value = !searchOpen.value
  }
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>
