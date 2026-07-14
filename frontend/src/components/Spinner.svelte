<script>
  let { loading = false } = $props();
</script>

{#if loading}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
    <span class="loading loading-spinner loading-lg text-primary"></span>
  </div>
{/if}
