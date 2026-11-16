<template>
  <!-- Odoo's user menu at the right of the navbar: the avatar (and name on wide screens),
       with Switch to Desk and Log out. -->
  <Dropdown :options="options" side="bottom" align="end">
    <button
      type="button"
      class="flex h-full items-center gap-2 px-2 text-left text-[14px] text-odoo-text hover:bg-odoo-hover focus:outline-none focus-visible:bg-odoo-hover"
      :aria-label="`Account: ${session.fullName}`"
    >
      <Avatar :label="session.fullName" :image="session.userImage" size="sm" />
      <span class="hidden max-w-40 truncate lg:inline">{{ session.fullName }}</span>
    </button>
  </Dropdown>

  <Dialog v-model="iosHintOpen" title="Add to Home Screen" size="sm">
    <p class="text-p-base text-ink-gray-7">
      In Safari, tap the Share button, then choose Add to Home Screen to install Agamsale.
    </p>
  </Dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Avatar, Dialog, Dropdown } from 'frappe-ui'
import { useInstallPrompt } from '@/composables/useInstallPrompt'
import { useSessionStore } from '@/stores/session'

const session = useSessionStore()
const { canInstall, showIosHint, install } = useInstallPrompt()
const iosHintOpen = ref(false)

const options = computed(() => [
  {
    group: session.user,
    options: [
      canInstall.value && { label: 'Install app', icon: 'lucide-download', onClick: install },
      showIosHint.value && { label: 'Add to Home Screen', icon: 'lucide-download', onClick: () => (iosHintOpen.value = true) },
      // A customer login is a website user: the desk would turn it away.
      !session.isRetailer && { label: 'Switch to Desk', icon: 'lucide-app-window', onClick: () => (window.location.href = '/app') },
      { label: 'Log out', icon: 'lucide-log-out', onClick: () => session.logout() },
    ].filter(Boolean),
  },
])
</script>
