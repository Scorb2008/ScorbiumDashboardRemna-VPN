<script>
  import Icon from './Icon.svelte';

  let { show = $bindable(false), onConfirm = () => {}, onCancel = () => {}, title = 'Подтверждение', message = '', confirmText = 'Удалить', danger = true, children = null } = $props();
</script>

{#if show}
  <div
    role="dialog"
    aria-modal="true"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in"
    onclick={(e) => e.target === e.currentTarget && onCancel()}>
    <div class="bg-surface-2 border border-surface-4/50 rounded-[14px] p-6 max-w-sm w-full mx-4 animate-scale-in shadow-2xl">
      <div class="w-10 h-10 rounded-full {danger ? 'bg-[#ef4444]/10' : 'bg-surface-3'} flex items-center justify-center mx-auto mb-4">
        <Icon name={danger ? 'alertTriangle' : 'info'} size={20} class="{danger ? 'text-[#ef4444]' : 'text-muted'}" />
      </div>
      <h3 id="confirm-dialog-title" class="text-[15px] font-semibold text-center mb-1.5">{title}</h3>
      <p class="text-[13px] text-muted text-center mb-6 leading-relaxed">{message}</p>
      {#if children}
        <div class="mb-4">{@render children()}</div>
      {/if}
      <div class="flex gap-3 justify-center">
        <button class="btn btn-secondary" onclick={onCancel}>Отмена</button>
        <button class="btn {danger ? 'btn-danger' : 'btn-primary'}" onclick={onConfirm}>{confirmText}</button>
      </div>
    </div>
  </div>
{/if}