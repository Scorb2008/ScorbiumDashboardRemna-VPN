<script>
  let { columns = [], data = [], onSort = null, sortCol = null, sortDir = 'asc', actions = null, emptyText = 'Нет данных', onRowClick = null } = $props();

  function handleSort(col) {
    if (!col.sortable || !onSort) return;
    onSort(col.key);
  }
</script>

<div class="card overflow-hidden">
  <div class="overflow-x-auto">
    <table class="table table-zebra">
      <thead>
        <tr>
          {#each columns as col}
            <th
              class="{col.sortable ? 'cursor-pointer hover:bg-base-300/50 select-none' : ''} text-xs font-medium uppercase tracking-wider"
              onclick={() => handleSort(col)}>
              <div class="flex items-center gap-1">
                {col.label}
                {#if sortCol === col.key}
                  <span class="text-primary text-xs">{sortDir === 'asc' ? '↑' : '↓'}</span>
                {/if}
              </div>
            </th>
          {/each}
          {#if actions}
            <th class="text-xs font-medium uppercase tracking-wider w-1"></th>
          {/if}
        </tr>
      </thead>
      <tbody>
        {#if data.length === 0}
          <tr>
            <td colspan={actions ? columns.length + 1 : columns.length} class="text-center py-12">
              <div class="flex flex-col items-center gap-2 text-base-content/30">
                <svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <span class="text-sm">{emptyText}</span>
              </div>
            </td>
          </tr>
        {:else}
          {#each data as row, i (row.id || i)}
            <tr
              class="animate-fade-in {onRowClick ? 'cursor-pointer hover:bg-base-300/30' : ''}"
              style="animation-delay: {i * 15}ms"
              onclick={() => onRowClick?.(row)}>
              {#each columns as col}
                <td>
                  {#if col.render}
                    {@html col.render(row)}
                  {:else}
                    <span class="text-sm">{row[col.key] ?? '—'}</span>
                  {/if}
                </td>
              {/each}
              {#if actions}
                <td onclick={(e) => e.stopPropagation()}>
                  {@render actions(row)}
                </td>
              {/if}
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>
</div>
