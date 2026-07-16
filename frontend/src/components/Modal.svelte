<script>
  import Icon from './Icon.svelte';

  let { open = $bindable(false), title = '', size = 'md', children } = $props();

  function close() { open = false; }
  function handleKeydown(e) { if (e.key === 'Escape') close(); }

  const sizes = { sm: '24rem', md: '28rem', lg: '32rem', xl: '40rem' };
</script>

{#if open}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in"
    role="dialog"
    onkeydown={handleKeydown}
    onclick={(e) => e.target === e.currentTarget && close()}>
    <div
      class="bg-surface-2 border border-surface-4/50 rounded-[14px] w-full mx-4 max-h-[90vh] flex flex-col animate-scale-in shadow-2xl"
      style="max-width: {sizes[size] || sizes.md}">
      <div class="flex items-center justify-between px-6 py-4 border-b border-surface-4/50">
        <h3 class="text-[15px] font-semibold">{title}</h3>
        <button onclick={close} class="p-1.5 rounded-lg text-muted hover:text-accent hover:bg-surface-3 transition-colors">
          <Icon name="x" size={18} />
        </button>
      </div>
      <div class="p-6 overflow-y-auto flex-1">
        {#if children}
          {@render children()}
        {/if}
      </div>
    </div>
  </div>
{/if}
