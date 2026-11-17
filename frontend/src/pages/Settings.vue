<template>
  <!-- Odoo's Settings: Save / Discard and "Search settings" in the control panel, the app
       sections listed on the left, the chosen section's settings blocks on the right. -->
  <div class="flex h-full flex-col">
    <PageHeader title="Settings" flush>
      <template #actions>
        <template v-if="canEdit && activeForm">
          <Button
            variant="solid"
            label="Save"
            :loading="activeForm.saving"
            :disabled="!activeForm.isDirty || activeForm.testing"
            @click="activeForm.save()"
          />
          <Button
            label="Discard"
            :disabled="!activeForm.isDirty || activeForm.saving || activeForm.testing"
            @click="activeForm.discard()"
          />
        </template>
        <Button
          v-if="canEditStore && tab === 'store'"
          label="Fetch Locations"
          icon-left="lucide-refresh-cw"
          :loading="!!storeForm?.fetchingLocations"
          :disabled="!storeForm"
          @click="storeForm?.fetchLocations()"
        />
        <StatusPill
          v-if="tab === 'store' && storeForm?.titleStatus"
          :status="storeForm.titleStatus.status"
          :label="storeForm.titleStatus.label"
          :icon="storeForm.titleStatus.icon"
        />
      </template>
      <template #search>
        <div class="flex min-h-[32px] items-center gap-2 rounded border border-odoo-line bg-white px-2 focus-within:border-odoo-action">
          <span class="lucide-search size-4 shrink-0 text-odoo-muted" aria-hidden="true" />
          <input
            v-model="query"
            type="search"
            class="h-7 min-w-0 flex-1 border-0 bg-transparent p-0 text-[14px] text-odoo-strong placeholder:text-odoo-muted focus:ring-0"
            placeholder="Search settings…"
            aria-label="Search settings"
          />
        </div>
      </template>
      <template #views>
        <Button variant="ghost" label="Help" icon-left="lucide-circle-help" href="/help" />
        <Button variant="ghost" label="Privacy" icon-left="lucide-shield" href="/privacy" />
      </template>
    </PageHeader>

    <div class="flex min-h-0 flex-1 flex-col md:flex-row">
      <!-- App sections (o_settings_tab) -->
      <nav class="flex shrink-0 overflow-x-auto border-b border-odoo-line bg-white md:w-56 md:flex-col md:overflow-y-auto md:border-b-0 md:border-r" aria-label="Settings sections">
        <button
          v-for="t in TABS"
          :key="t.value"
          type="button"
          class="flex shrink-0 items-center gap-2.5 whitespace-nowrap px-4 py-2.5 text-left text-[14px] focus:outline-none focus-visible:bg-odoo-hover"
          :class="tab === t.value ? 'bg-odoo-hover font-semibold text-odoo-strong md:border-l-[3px] md:border-odoo-action' : 'text-odoo-text hover:bg-[#f2f3f5] md:border-l-[3px] md:border-transparent'"
          :aria-current="tab === t.value ? 'page' : undefined"
          @click="tab = t.value"
        >
          <span :class="[NOT_ADMIN[t.value].icon, 'size-[18px] text-odoo-primary']" aria-hidden="true" />
          {{ t.label }}
        </button>
      </nav>

      <div ref="pane" class="o-settings min-w-0 flex-1 overflow-y-auto bg-white px-4 py-4 sm:px-8">
        <p v-if="query && noMatch" class="py-8 text-center text-odoo-muted">No setting in {{ currentLabel }} matches "{{ query }}".</p>
        <MobilePushSettings v-if="tab === 'mobile-push' && canEdit" ref="mobilePushForm" />
        <!-- Sales Managers may also edit Razorpay; push is System Manager only -->
        <RazorpaySettings v-else-if="tab === 'razorpay' && canEdit" ref="razorpayForm" />
        <!-- Inside the Shopify admin the store's managers edit these (merchant fields only) -->
        <template v-else-if="canEditStore">
          <!-- v-show keeps unsaved Store Connection edits while another tab is open -->
          <StoreConnectionForm v-show="tab === 'store'" ref="storeForm" />
          <InvoiceSettings v-if="tab === 'invoice'" ref="invoiceForm" @saved="refreshStoreForm" />
          <CommissionSettings v-if="tab === 'commission'" ref="commissionForm" @saved="refreshStoreForm" />
          <EmailAccountSettings v-if="tab === 'email'" />
        </template>
        <EmptyState
          v-else
          :icon="NOT_ADMIN[tab].icon"
          :title="NOT_ADMIN[tab].title"
          :description="`Only a ${NOT_ADMIN[tab].who || 'System Manager'} can change ${NOT_ADMIN[tab].what}.`"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button } from 'frappe-ui'
import PageHeader from '@/components/PageHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import StatusPill from '@/components/StatusPill.vue'
import StoreConnectionForm from '@/components/StoreConnectionForm.vue'
import InvoiceSettings from '@/components/InvoiceSettings.vue'
import CommissionSettings from '@/components/CommissionSettings.vue'
import EmailAccountSettings from '@/components/EmailAccountSettings.vue'
import RazorpaySettings from '@/components/RazorpaySettings.vue'
import MobilePushSettings from '@/components/MobilePushSettings.vue'
import { useSessionStore } from '@/stores/session'
import { isEmbedded } from '@/shopify/embedded'

const session = useSessionStore()
const embedded = isEmbedded()
const storeForm = ref(null)
const invoiceForm = ref(null)
const commissionForm = ref(null)
const razorpayForm = ref(null)
const mobilePushForm = ref(null)

const TABS = [
  { label: 'Store', value: 'store' },
  { label: 'Invoicing', value: 'invoice' },
  { label: 'Commission', value: 'commission' },
  { label: 'Emails', value: 'email' },
  { label: 'Payments', value: 'razorpay' },
  { label: 'Notifications', value: 'mobile-push' },
]
const NOT_ADMIN = {
  store: { icon: 'lucide-store', title: 'Store Connection', what: 'the store connection' },
  invoice: { icon: 'lucide-file-text', title: 'Invoice', what: 'the invoice settings' },
  commission: { icon: 'lucide-wallet', title: 'Commission', what: 'the commission settings' },
  email: { icon: 'lucide-mail', title: 'Email Account', what: 'the email account' },
  razorpay: { icon: 'lucide-credit-card', title: 'Razorpay', what: 'the Razorpay settings', who: 'Sales Manager or System Manager' },
  'mobile-push': { icon: 'lucide-bell', title: 'Notification', what: 'the notification settings' },
}
// The form whose Save / Discard the header shows (the Email tab saves in its own dialog).
const FORMS = { store: storeForm, invoice: invoiceForm, commission: commissionForm, razorpay: razorpayForm, 'mobile-push': mobilePushForm }
const activeForm = computed(() => FORMS[tab.value]?.value || null)
// Inside the Shopify admin the store's managers set the store up (merchant fields only, see
// shopify/merchantSettings.js); elsewhere it stays System Manager only.
const canEditStore = computed(() => session.isAdmin || (embedded && session.isManager))
const canEdit = computed(() => tab.value === 'mobile-push' ? session.isAdmin : tab.value === 'razorpay' ? session.isManager : canEditStore.value)

// These forms all edit the Store Connection document: after an Invoice or Commission save, the Store form
// reloads so its next save is not refused as out of date (unless it holds unsaved edits).
function refreshStoreForm() {
  if (storeForm.value && !storeForm.value.isDirty) storeForm.value.discard()
}

// The tab is in the URL (?tab=email), so a refresh or a link opens it.
const route = useRoute()
const router = useRouter()
const tab = computed({
  get: () => (route.query.tab in NOT_ADMIN ? route.query.tab : 'store'),
  set: (value) => router.replace({ query: value === 'store' ? {} : { tab: value } }),
})

// "Search settings": hide the section's settings blocks that do not mention the words.
// The forms are untouched; only blocks (each <section>) are shown or hidden.
const pane = ref(null)
const query = ref('')
const noMatch = ref(false)
const currentLabel = computed(() => TABS.find((t) => t.value === tab.value)?.label || '')
async function applySearch() {
  await nextTick()
  const root = pane.value
  if (!root) return
  const words = query.value.trim().toLowerCase().split(/\s+/).filter(Boolean)
  const sections = [...root.querySelectorAll('section')]
  let shown = 0
  for (const section of sections) {
    const text = section.textContent.toLowerCase()
    const match = words.every((w) => text.includes(w))
    section.style.display = match ? '' : 'none'
    if (match) shown++
  }
  noMatch.value = words.length > 0 && sections.length > 0 && shown === 0
}
watch([query, tab], applySearch)
// The sections' forms load after the tab opens: filter what they add while a search is on.
let observer = null
onMounted(() => {
  observer = new MutationObserver(() => query.value.trim() && applySearch())
  if (pane.value) observer.observe(pane.value, { childList: true, subtree: true })
})
onBeforeUnmount(() => observer?.disconnect())
</script>
