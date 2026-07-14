<script>
  let { label = '', value = '', icon = '', color = 'primary', subtitle = '' } = $props();
</script>

<div class="stat-card">
  <div class="flex items-start justify-between">
    <div>
      <div class="text-sm text-base-content/50 mb-1">{label}</div>
      <div class="text-2xl font-bold">{value}</div>
      {#if subtitle}
        <div class="text-xs text-base-content/40 mt-1">{subtitle}</div>
      {/if}
    </div>
    {#if icon}
      <div class="text-3xl opacity-30">{icon}</div>
    {/if}
  </div>
</div>
