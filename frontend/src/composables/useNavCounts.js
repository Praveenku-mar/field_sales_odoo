import { onBeforeUnmount, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'
import { useSessionStore } from '@/stores/session'

/**
 * Menu counts (failed orders, shops) and the bell's unread notifications:
 * frontend_api.get_sidebar_counts. Called once by AppLayout, which hands it to the top bar
 * and the phone menu.
 */
export function useNavCounts() {
  const session = useSessionStore()
  const route = useRoute()

  // A customer login shows no counts, so it never fetches or polls them.
  const counts = createResource({
    url: 'field_sales_odoo.frontend_api.get_sidebar_counts',
    auto: !session.isRetailer,
  })
  const reload = () => !session.isRetailer && counts.reload()

  // Counts change as people work; refresh them when moving between pages.
  watch(() => route.name, reload)

  // The Notifications page announces read/unread changes made without leaving it.
  // There is no realtime connection, so poll while the tab is in view.
  let poll = null
  onMounted(() => {
    window.addEventListener('fs:notifications-changed', reload)
    poll = setInterval(() => document.visibilityState === 'visible' && reload(), 60000)
  })
  onBeforeUnmount(() => {
    window.removeEventListener('fs:notifications-changed', reload)
    clearInterval(poll)
  })

  return counts
}
