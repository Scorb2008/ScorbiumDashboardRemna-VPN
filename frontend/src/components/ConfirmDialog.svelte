<script>
  let { show = false, onConfirm = null, onCancel = null, title = 'Подтверждение', message = '' } = $props();

  function confirm() {
    onConfirm?.();
    show = false;
  }
  function cancel() {
    onCancel?.();
    show = false;
  }
</script>

{#if show}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm fade-in"
    onclick={(e) => e.target === e.currentTarget && cancel()}>
    <div class="bg-base-200 rounded-2xl shadow-2xl border border-base-300 p-6 max-w-sm w-full mx-4 fade-in">
      <h3 class="text-lg font-semibold mb-2">{title}</h3>
      <p class="text-base-content/60 text-sm mb-5">{message}</p>
      <div class="flex justify-end gap-2">
        <button class="btn btn-ghost btn-sm" onclick={cancel}>Отмена</button>
        <button class="btn btn-error btn-sm" onclick={confirm}>Подтвердить</button>
      </div>
    </div>
  </div>
{/if}
