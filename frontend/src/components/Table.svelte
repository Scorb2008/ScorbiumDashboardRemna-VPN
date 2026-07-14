<script>
  let {
    columns = [],
    data = [],
    onSort = null,
    sortCol = null,
    sortDir = 'asc',
    actions = null,
  } = $props();

  function handleSort(col) {
    if (!col.sortable) return;
    if (onSort) onSort(col.key);
  }
</script>

<div class="table-container">
  <div class="overflow-x-auto">
    <table class="table table-zebra table-hover">
      <thead>
        <tr>
          {#each columns as col}
            <th
              class:text-cursor-pointer={col.sortable}
              class:hover:bg-base-300={col.sortable}
              onclick={() => handleSort(col)}>
              <div class="flex items-center gap-1">
                {col.label}
                {#if sortCol === col.key}
                  <span class="text-primary">{sortDir === 'asc' ? '↑' : '↓'}</span>
                {/if}
              </div>
            </th>
          {/each}
          {#if actions}
            <th></th>
          {/if}
        </tr>
      </thead>
      <tbody>
        {#if data.length === 0}
          <tr>
            <td colspan={actions ? columns.length + 1 : columns.length} class="text-center py-8 text-base-content/40">
              Нет данных
            </td>
          </tr>
        {:else}
          {#each data as row, i (row.id || i)}
            <tr class="fade-in" style="animation-delay: {i * 20}ms">
              {#each columns as col}
                <td>
                  {#if col.render}
                    {@render col.render(row)}
                  {:else}
                    {row[col.key] ?? '—'}
                  {/if}
                </td>
              {/each}
              {#if actions}
                <td>
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
