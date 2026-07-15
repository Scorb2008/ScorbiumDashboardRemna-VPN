<script>
  let { open = $bindable(false), title = '', size = 'md', children } = $props();

  function close() { open = false; }
  function handleKeydown(e) { if (e.key === 'Escape') close(); }
</script>

{#if open}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in"
    role="dialog"
    onkeydown={handleKeydown}
    onclick={(e) => e.target === e.currentTarget && close()}>
    <div
      class="glass-strong rounded-2xl w-full mx-4 max-h-[90vh] flex flex-col animate-scale-in"
      style="max-width: {size === 'sm' ? '24rem' : size === 'md' ? '28rem' : size === 'lg' ? '32rem' : '40rem'}">
      <div class="flex items-center justify-between p-5 border-b border-base-300/50">
        <h3 class="text-lg font-semibold">{title}</h3>
        <button onclick={close} class="btn btn-ghost btn-sm btn-circle hover:bg-base-300">✕</button>
      </div>
      <div class="p-5 overflow-y-auto flex-1">
        {#if children}
          {@render children()}
        {/if}
      </div>
    </div>
  </div>
{/if}
