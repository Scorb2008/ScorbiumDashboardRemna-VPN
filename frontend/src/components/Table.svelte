<script>
  let { columns = [], data = [], onSort = null, sortCol = null, sortDir = 'asc', actions = null, emptyText = 'Нет данных', onRowClick = null } = $props();

  function handleSort(col) {
    if (!col.sortable || !onSort) return;
    onSort(col.key);
  }
</script>

<div class="card overflow-hidden">
  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-surface-4/50">
          {#each columns as col}
            <th
              class="px-5 py-3 text-left text-[11px] font-medium text-muted uppercase tracking-wider {col.sortable ? 'cursor-pointer hover:text-accent select-none' : ''}"
              onclick={() => handleSort(col)}>
              <div class="flex items-center gap-1">
                {col.label}
                {#if sortCol === col.key}
                  <span class="text-accent text-xs">{sortDir === 'asc' ? '↑' : '↓'}</span>
                {/if}
              </div>
            </th>
          {/each}
          {#if actions}
            <th class="px-5 py-3 w-1"></th>
          {/if}
        </tr>
      </thead>
      <tbody>
        {#if data.length === 0}
          <tr>
            <td colspan={actions ? columns.length + 1 : columns.length} class="px-5 py-16 text-center">
              <div class="flex flex-col items-center gap-2 text-muted/50">
                <p class="text-sm">{emptyText}</p>
              </div>
            </td>
          </tr>
        {:else}
          {#each data as row, i (row.id || i)}
            <tr
              class="border-b border-surface-4/30 transition-colors {onRowClick ? 'cursor-pointer hover:bg-surface-3/50' : ''}"
              onclick={() => onRowClick?.(row)}>
              {#each columns as col}
                <td class="px-5 py-3">
                  {#if col.render}
                    {@html col.render(row)}
                  {:else}
                    <span class="text-[13px]">{row[col.key] ?? '—'}</span>
                  {/if}
                </td>
              {/each}
              {#if actions}
                <td class="px-5 py-3" onclick={(e) => e.stopPropagation()}>
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
