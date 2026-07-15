<script>
  let { label = '', value = '', icon = '', subtitle = '', gradient = 'gradient-primary' } = $props();
</script>

<div class="stat-card animate-slide-up">
  <div class="flex items-start justify-between">
    <div class="space-y-1">
      <p class="text-xs font-medium text-base-content/50 uppercase tracking-wider">{label}</p>
      <p class="text-2xl font-bold">{value}</p>
      {#if subtitle}
        <p class="text-xs text-base-content/40">{subtitle}</p>
      {/if}
    </div>
    {#if icon}
      <div class="w-11 h-11 rounded-xl {gradient} flex items-center justify-center shadow-lg">
        <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d={icon} />
        </svg>
      </div>
    {/if}
  </div>
</div>
