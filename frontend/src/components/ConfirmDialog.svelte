<script>
  let { show = $bindable(false), onConfirm = () => {}, onCancel = () => {}, title = 'Подтверждение', message = '', confirmText = 'Удалить', confirmClass = 'btn-error' } = $props();
</script>

{#if show}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in"
    onclick={(e) => e.target === e.currentTarget && onCancel()}>
    <div class="glass-strong rounded-2xl p-6 max-w-sm w-full mx-4 animate-scale-in">
      <div class="w-12 h-12 rounded-full bg-error/10 flex items-center justify-center mx-auto mb-4">
        <svg class="w-6 h-6 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h3 class="text-lg font-semibold text-center mb-2">{title}</h3>
      <p class="text-sm text-base-content/60 text-center mb-6">{message}</p>
      <div class="flex gap-3 justify-center">
        <button class="btn btn-ghost" onclick={onCancel}>Отмена</button>
        <button class="btn {confirmClass}" onclick={onConfirm}>{confirmText}</button>
      </div>
    </div>
  </div>
{/if}
