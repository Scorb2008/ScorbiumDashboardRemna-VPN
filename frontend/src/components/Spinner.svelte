<script>
  let { loading = false } = $props();
</script>

{#if loading}
  <div class="fixed inset-0 z-[200] flex items-center justify-center bg-surface-1/80 backdrop-blur-sm">
    <div class="flex flex-col items-center gap-3">
      <div class="w-6 h-6 border-2 border-surface-4 border-t-accent rounded-full animate-spin"></div>
      <p class="text-xs text-muted">Загрузка...</p>
    </div>
  </div>
{/if}
