import { ref, watch } from 'vue'
import { getPreference, setPreference } from '@/utils/storage'

/**
 * Which view a list page shows ('list' | 'kanban'), remembered per page in this browser.
 * Phones open in kanban, as Odoo does.
 */
export function useViewMode(page) {
  const key = `fs:view:${page}`
  const phone = typeof window !== 'undefined' && window.matchMedia?.('(max-width: 767px)').matches
  const stored = getPreference(key)
  const mode = ref(stored === 'list' || stored === 'kanban' ? stored : phone ? 'kanban' : 'list')
  watch(mode, (value) => setPreference(key, value))
  return mode
}
