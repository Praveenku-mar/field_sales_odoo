<template>
  <!-- Odoo's form view: the status bar (workflow buttons left, stages right) across the top,
       then the sheet — a white page with the ribbon, the smart buttons and the record. A
       #chatter slot sits beside the sheet on wide screens and under it otherwise. -->
  <div class="o-form pb-8">
    <div
      v-if="$slots.statusbar || stages.length"
      class="-mt-4 flex flex-wrap items-center justify-between gap-2 border-b border-odoo-line bg-white px-4 py-1.5"
    >
      <div class="flex flex-wrap items-center gap-2"><slot name="statusbar" /></div>
      <ol v-if="stages.length" class="o-statusbar flex items-stretch overflow-x-auto" aria-label="Stage">
        <li
          v-for="(stage, i) in stages"
          :key="stage.value"
          class="o-stage"
          :class="[stage.value === current ? 'o-stage-current' : 'o-stage-other', i === 0 && 'o-stage-first']"
          :aria-current="stage.value === current ? 'step' : undefined"
        >
          {{ stage.label }}
        </li>
      </ol>
    </div>

    <div class="mx-auto flex max-w-[1500px] flex-col gap-4 px-3 pt-4 xl:flex-row xl:items-start">
      <div class="min-w-0 flex-1">
        <div v-if="$slots.alerts" class="mx-auto mb-3 max-w-[1140px] space-y-2"><slot name="alerts" /></div>
        <div class="o-form-sheet relative mx-auto max-w-[1140px] overflow-hidden rounded border border-odoo-line bg-white px-4 pb-6 pt-4 shadow-[0_1px_2px_rgba(0,0,0,0.05)] sm:px-8">
          <div v-if="ribbon" class="pointer-events-none absolute right-0 top-0 size-28 overflow-hidden" aria-hidden="true">
            <div
              class="absolute right-[-38px] top-[22px] w-40 rotate-45 py-1 text-center text-[12px] font-bold uppercase tracking-wide text-white shadow"
              :class="RIBBON_TONES[ribbon.tone || 'success']"
            >
              {{ ribbon.label }}
            </div>
          </div>
          <span v-if="ribbon" class="sr-only">{{ ribbon.label }}</span>
          <div v-if="$slots.smart" class="-mx-4 -mt-4 mb-4 flex flex-wrap justify-end border-b border-odoo-hover sm:-mx-8" :class="ribbon && 'pr-20'">
            <slot name="smart" />
          </div>
          <slot />
        </div>
      </div>
      <aside v-if="$slots.chatter" class="w-full min-w-0 xl:w-[420px] xl:shrink-0"><slot name="chatter" /></aside>
    </div>
  </div>
</template>

<script setup>
defineProps({
  /** The record's stages, in order: [{ value, label }]. */
  stages: { type: Array, default: () => [] },
  /** The current stage's value. */
  current: { type: String, default: null },
  /** Corner ribbon: { label, tone: 'success' | 'danger' | 'warning' | 'info' }. */
  ribbon: { type: Object, default: null },
})

const RIBBON_TONES = {
  success: 'bg-[#28a745]',
  danger: 'bg-[#d44c59]',
  warning: 'bg-[#e99d00]',
  info: 'bg-[#017e84]',
}
</script>

<style scoped>
.o-stage {
  position: relative;
  display: flex;
  align-items: center;
  padding: 0.3rem 0.9rem 0.3rem 1.3rem;
  font-size: 13px;
  white-space: nowrap;
  clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 50%, calc(100% - 10px) 100%, 0 100%, 10px 50%);
  margin-left: -6px;
}
.o-stage-first {
  clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 50%, calc(100% - 10px) 100%, 0 100%);
  margin-left: 0;
  padding-left: 0.9rem;
}
.o-stage-other {
  background-color: var(--o-border-light);
  color: var(--o-text-muted);
}
.o-stage-current {
  background-color: var(--o-action);
  color: #fff;
  font-weight: 600;
}
</style>
