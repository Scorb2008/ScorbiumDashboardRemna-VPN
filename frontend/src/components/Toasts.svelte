<script>
  import { toasts } from '../lib/stores.js';
  import Icon from './Icon.svelte';

  const colors = {
    success: 'bg-[#22c55e]/10 border-[#22c55e]/30 text-[#22c55e]',
    error: 'bg-[#ef4444]/10 border-[#ef4444]/30 text-[#ef4444]',
    warning: 'bg-[#eab308]/10 border-[#eab308]/30 text-[#eab308]',
    info: 'bg-surface-3 border-surface-4 text-muted',
  };

  const icons = {
    success: 'check',
    error: 'x',
    warning: 'alertTriangle',
    info: 'info',
  };
</script>

{#if $toasts.length > 0}
  <div class="fixed bottom-5 right-5 z-[100] flex flex-col gap-2 max-w-sm">
    {#each $toasts as toast (toast.id)}
      <div class="flex items-center gap-3 px-4 py-3 rounded-[12px] border shadow-lg animate-slide-up {colors[toast.type] || colors.info}">
        <Icon name={icons[toast.type] || 'info'} size={16} class="shrink-0" />
        <span class="text-sm flex-1">{toast.message}</span>
        <button class="shrink-0 p-1 rounded-md hover:bg-white/10 transition-colors" onclick={() => toasts.remove(toast.id)}>
          <Icon name="x" size={14} />
        </button>
      </div>
    {/each}
  </div>
{/if}
