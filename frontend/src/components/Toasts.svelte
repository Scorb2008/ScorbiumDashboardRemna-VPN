<script>
  import { toasts } from '../lib/stores.js';
</script>

<div class="toast toast-end z-[100]">
  {#each $toasts as toast (toast.id)}
    <div
      class="alert shadow-lg fade-in text-sm max-w-sm"
      class:alert-success={toast.type === 'success'}
      class:alert-error={toast.type === 'error'}
      class:alert-warning={toast.type === 'warning'}
      class:alert-info={toast.type === 'info'}>
      <span>{toast.message}</span>
      <button class="btn btn-ghost btn-xs" onclick={() => toasts.remove(toast.id)}>✕</button>
    </div>
  {/each}
</div>
