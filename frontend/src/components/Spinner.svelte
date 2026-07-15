<script>
  let { loading = false } = $props();
</script>

{#if loading}
  <div class="fixed inset-0 z-[200] flex items-center justify-center bg-base-100/80 backdrop-blur-sm">
    <div class="flex flex-col items-center gap-4">
      <span class="loading loading-spinner loading-lg text-primary"></span>
      <p class="text-sm text-base-content/50">Загрузка...</p>
    </div>
  </div>
{/if}
