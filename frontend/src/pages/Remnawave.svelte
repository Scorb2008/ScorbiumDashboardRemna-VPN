<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.js';
  import { toasts } from '../lib/stores.js';
  import Spinner from '../components/Spinner.svelte';
  import StatsCard from '../components/StatsCard.svelte';

  let stats = $state(null);
  let nodes = $state([]);
  let users = $state([]);
  let loading = $state(true);
  let activeTab = $state('overview');

  onMount(async () => {
    try {
      const [sysStats, nodeData, userData] = await Promise.allSettled([
        api.get('/remnawave/status'),
        api.get('/remnawave/nodes'),
        api.get('/remnawave/users'),
      ]);
      if (sysStats.status === 'fulfilled') stats = sysStats.value;
      if (nodeData.status === 'fulfilled') nodes = nodeData.value?.nodes || [];
      if (userData.status === 'fulfilled') users = userData.value?.users || [];
    } catch (e) {
      toasts.error('Ошибка загрузки Remnawave: ' + e.message);
    } finally {
      loading = false;
    }
  });

  function formatBytes(bytes) {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let i = 0, val = bytes;
    while (val >= 1024 && i < units.length - 1) { val /= 1024; i++; }
    return val.toFixed(1) + ' ' + units[i];
  }
</script>

<div class="fade-in">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">Remnawave</h1>
    <div class="tabs tabs-boxed">
      <button class="tab" class:tab-active={activeTab === 'overview'} onclick={() => activeTab = 'overview'}>Обзор</button>
      <button class="tab" class:tab-active={activeTab === 'nodes'} onclick={() => activeTab = 'nodes'}>Ноды ({nodes.length})</button>
      <button class="tab" class:tab-active={activeTab === 'users'} onclick={() => activeTab = 'users'}>Пользователи ({users.length})</button>
    </div>
  </div>

  <Spinner {loading} />

  {#if !loading}
    {#if activeTab === 'overview'}
      {#if stats}
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatsCard label="Онлайн" value={stats.online_users} icon="🟢" />
          <StatsCard label="Всего пользователей" value={stats.total_users} icon="👥" />
          <StatsCard label="Нод онлайн" value={stats.nodes_online} icon="🌐" />
          <StatsCard label="CPU" value="{stats.cpu_usage} cores" icon="💻" />
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="stat-card">
            <div class="text-sm text-base-content/50 mb-2">RAM</div>
            <div class="text-xl font-bold">{stats.mem_used ? formatBytes(stats.mem_used) : '—'}</div>
          </div>
          <div class="stat-card">
            <div class="text-sm text-base-content/50 mb-2">Ноды</div>
            <div class="text-xl font-bold">{nodes.length} всего</div>
          </div>
        </div>
      {:else}
        <div class="alert alert-warning">Не удалось загрузить статистику</div>
      {/if}

    {:else if activeTab === 'nodes'}
      {#if nodes.length === 0}
        <div class="text-center py-12 text-base-content/40">Ноды не найдены</div>
      {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {#each nodes as node (node.id)}
            <div class="stat-card">
              <div class="flex items-center gap-2 mb-3">
                <span class="w-2.5 h-2.5 rounded-full" class:bg-success={node.isConnected} class:bg-error={!node.isConnected}></span>
                <span class="font-semibold">{node.name || 'Node #' + node.id}</span>
              </div>
              <div class="text-sm text-base-content/50">{node.address || '—'}</div>
              <div class="text-xs text-base-content/40 mt-2">Port: {node.port || '—'}</div>
            </div>
          {/each}
        </div>
      {/if}

    {:else if activeTab === 'users'}
      {#if users.length === 0}
        <div class="text-center py-12 text-base-content/40">Пользователи не найдены</div>
      {:else}
        <div class="table-container">
          <div class="overflow-x-auto">
            <table class="table table-zebra table-hover">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Статус</th>
                  <th>Трафик</th>
                  <th>Истекает</th>
                </tr>
              </thead>
              <tbody>
                {#each users as u (u.uuid || u.username)}
                  <tr class="fade-in">
                    <td class="font-mono text-sm">{u.username}</td>
                    <td>
                      <span class="badge badge-sm" class:badge-success={u.status === 'ACTIVE'} class:badge-error={u.status !== 'ACTIVE'}>
                        {u.status}
                      </span>
                    </td>
                    <td>{formatBytes(u.userTraffic?.usedTrafficBytes || 0)}</td>
                    <td class="text-sm">{u.expireAt || '∞'}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
      {/if}
    {/if}
  {/if}
</div>
