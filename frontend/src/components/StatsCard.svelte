<script>
  import Icon from './Icon.svelte';

  let { label = '', value = '', icon = '', subtitle = '', trend = null } = $props();
</script>

<div class="stat-card animate-slide-up">
  <div class="flex items-start justify-between">
    <div class="space-y-1">
      <p class="text-[11px] font-medium text-muted uppercase tracking-wider">{label}</p>
      <p class="text-[28px] font-bold leading-none tracking-tight">{value}</p>
      {#if subtitle}
        <div class="flex items-center gap-1.5">
          {#if trend === 'up'}
            <Icon name="trendingUp" size={14} class="text-[#22c55e]" />
          {:else if trend === 'down'}
            <Icon name="trendingDown" size={14} class="text-[#ef4444]" />
          {/if}
          <p class="text-xs text-muted">{subtitle}</p>
        </div>
      {/if}
    </div>
    {#if icon}
      <div class="w-10 h-10 rounded-[10px] bg-surface-3 border border-surface-4/50 flex items-center justify-center">
        <Icon name={icon} size={18} class="text-muted" />
      </div>
    {/if}
  </div>
</div>
