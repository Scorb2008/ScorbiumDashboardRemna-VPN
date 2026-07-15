<script>
  import { toasts } from '../lib/stores.js';
</script>

{#if $toasts.length > 0}
  <div class="fixed bottom-5 right-5 z-[100] flex flex-col gap-2 max-w-sm">
    {#each $toasts as toast (toast.id)}
      <div class="alert animate-slide-up shadow-lg {toast.type === 'success' ? 'alert-success' : toast.type === 'error' ? 'alert-error' : toast.type === 'warning' ? 'alert-warning' : 'alert-info'}">
        <span class="text-sm">{toast.message}</span>
        <button class="btn btn-ghost btn-xs btn-circle" onclick={() => toasts.remove(toast.id)}>✕</button>
      </div>
    {/each}
  </div>
{/if}
