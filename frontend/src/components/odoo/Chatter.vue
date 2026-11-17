<template>
  <!-- Odoo's chatter (o-mail-Chatter): "Log note" opens the composer; under it the record's
       timeline, newest first, grouped by day — notes, system messages, field changes
       ("Price: 100 → 125") and emails. Text only: nothing in a message renders as markup. -->
  <section class="rounded border border-odoo-line bg-white" aria-label="Chatter">
    <div class="flex items-center gap-2 border-b border-odoo-hover px-3 py-2">
      <Button
        :label="composerOpen ? 'Close' : 'Log note'"
        :variant="composerOpen ? 'subtle' : 'solid'"
        size="sm"
        @click="toggleComposer"
      />
      <span class="flex-1" />
      <Button variant="ghost" size="sm" icon="lucide-refresh-cw" aria-label="Refresh" :loading="timeline.loading" @click="timeline.reload()" />
    </div>

    <form v-if="composerOpen" class="border-b border-odoo-hover p-3" @submit.prevent="post">
      <label :for="inputId" class="sr-only">Log an internal note</label>
      <textarea
        :id="inputId"
        ref="input"
        v-model="note"
        rows="3"
        maxlength="5000"
        class="w-full resize-y rounded border border-odoo-line p-2 text-[14px] text-odoo-strong placeholder:text-odoo-muted focus:border-odoo-action focus:ring-0"
        placeholder="Log an internal note…"
        @keydown.ctrl.enter.prevent="post"
        @keydown.meta.enter.prevent="post"
      />
      <div class="mt-2 flex items-center gap-2">
        <Button type="submit" variant="solid" label="Log" :loading="posting" :disabled="!note.trim()" />
        <span class="text-xs text-odoo-muted">Internal: visible to your team, not to the shop. Ctrl+Enter to log.</span>
      </div>
    </form>

    <div class="max-h-[70vh] overflow-y-auto px-3 py-2">
      <p v-if="timeline.error" class="py-4 text-[13px] text-ink-red-6">{{ errorText }}</p>
      <div v-else-if="timeline.loading && !items.length" class="space-y-3 py-3">
        <div v-for="i in 3" :key="i" class="h-10 animate-pulse rounded bg-odoo-hover" />
      </div>
      <p v-else-if="!items.length" class="py-6 text-center text-[13px] text-odoo-muted">No activity yet.</p>

      <template v-for="group in groups" :key="group.day">
        <div class="my-2 flex items-center gap-2 text-xs text-odoo-muted" role="separator">
          <span class="h-px flex-1 bg-odoo-hover" /> {{ group.day }} <span class="h-px flex-1 bg-odoo-hover" />
        </div>
        <article v-for="(item, i) in group.items" :key="`${item.at}-${i}`" class="flex gap-2.5 py-2">
          <Avatar :label="item.by_name || '?'" size="md" class="shrink-0" />
          <div class="min-w-0 flex-1 text-[13px]">
            <div class="flex flex-wrap items-baseline gap-x-2">
              <span class="font-semibold text-odoo-strong">{{ item.by_name || 'System' }}</span>
              <time class="text-xs text-odoo-muted" :datetime="item.at" :title="formatDateTime(item.at)">{{ formatTime(item.at) }}</time>
              <span v-if="item.kind === 'email'" class="text-xs text-odoo-muted">· email</span>
            </div>
            <p v-if="item.kind === 'note'" class="mt-0.5 whitespace-pre-line break-words rounded bg-[#f2f3f5] px-2 py-1.5 text-odoo-text">{{ item.text }}</p>
            <p v-else-if="item.kind === 'info'" class="mt-0.5 whitespace-pre-line break-words text-odoo-muted">{{ item.text }}</p>
            <template v-else-if="item.kind === 'email'">
              <p class="mt-0.5 font-medium text-odoo-text">{{ item.subject }}</p>
              <p class="text-odoo-muted">{{ item.text }}</p>
            </template>
            <ul v-else-if="item.kind === 'change'" class="mt-0.5 space-y-0.5">
              <li v-for="change in item.changes" :key="change.label" class="break-words text-odoo-text">
                <span class="text-odoo-muted">{{ change.from || 'None' }}</span>
                <span class="lucide-arrow-right mx-1 inline-block size-3 align-middle text-odoo-muted" aria-label="changed to" />
                <span class="font-medium">{{ change.to || 'None' }}</span>
                <span class="text-odoo-muted"> ({{ change.label }})</span>
              </li>
            </ul>
          </div>
        </article>
      </template>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { Avatar, Button, createResource, toast } from 'frappe-ui'
import { callMethod } from '@/utils/api'
import { formatDate, formatDateTime, formatTime, relativeDay } from '@/utils/format'

const props = defineProps({
  doctype: { type: String, required: true },
  name: { type: String, required: true },
  /** The record's `modified`: the timeline reloads when the record changes. */
  version: { type: String, default: null },
})

const timeline = createResource({
  url: 'field_sales_odoo.chatter.get_chatter',
  makeParams: () => ({ doctype: props.doctype, name: props.name }),
  auto: true,
})
watch(
  () => props.version,
  (now, before) => before && now !== before && timeline.reload(),
)

const items = computed(() => timeline.data?.items || [])
const errorText = computed(() => String(timeline.error?.messages?.[0] || timeline.error || 'Could not load the history'))

// Grouped by day, as Odoo separates the timeline ("Today", "Yesterday", a date).
const groups = computed(() => {
  const out = []
  for (const item of items.value) {
    const key = String(item.at).slice(0, 10)
    const label = ['Today', 'Yesterday'].includes(relativeDay(key)) ? relativeDay(key) : formatDate(key)
    if (!out.length || out[out.length - 1].key !== key) out.push({ key, day: label, items: [] })
    out[out.length - 1].items.push(item)
  }
  return out
})

const inputId = `chatter-note-${Math.random().toString(36).slice(2, 7)}`
const input = ref(null)
const composerOpen = ref(false)
const note = ref('')
const posting = ref(false)

async function toggleComposer() {
  composerOpen.value = !composerOpen.value
  if (composerOpen.value) {
    await nextTick()
    input.value?.focus()
  }
}

async function post() {
  const text = note.value.trim()
  if (!text || posting.value) return
  posting.value = true
  try {
    await callMethod('field_sales_odoo.chatter.post_note', { doctype: props.doctype, name: props.name, text })
    note.value = ''
    composerOpen.value = false
    toast.success('Note logged')
    timeline.reload()
  } catch {
    // callMethod shows the server's message; the note stays in the box.
  } finally {
    posting.value = false
  }
}
</script>
