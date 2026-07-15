<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatBytes } from '../lib/utils.js';
  import StatsCard from '../components/StatsCard.svelte';
  import Spinner from '../components/Spinner.svelte';

  let activeTab = $state('overview');
  let overview = $state(null);
  let nodes = $state([]);
  let users = $state([]);
  let loading = $state(true);

  const tabs = [
    { id: 'overview', label: 'Обзор' },
    { id: 'nodes', label: 'Ноды' },
    { id: 'users', label: 'Пользователи' },
  ];

  onMount(async () => {
    try {
      const [status, nodesRes, usersRes] = await Promise.allSettled([
        api.get('/remnawave/status'),
        api.get('/remnawave/nodes'),
        api.get('/remnawave/users'),
      ]);
      if (status.status === 'fulfilled') overview = status.value;
      if (nodesRes.status === 'fulfilled') nodes = nodesRes.value || [];
      if (usersRes.status === 'fulfilled') users = usersRes.value || [];
    } catch (e) {
      toasts.error('Ошибка загрузки Remnawave');
    } finally {
      loading = false;
    }
  });

  function onlineNodes() {
    return nodes.filter(n => n.is_connected || n.status === 'online').length;
  }

  function onlineUsers() {
    return overview?.online_users ?? overview?.active_users ?? 0;
  }
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div>
    <h1 class="text-2xl font-bold">Remnawave</h1>
    <p class="text-sm text-base-content/40 mt-1">Панель управления VPN</p>
  </div>

  <div class="flex gap-1 p-1 glass rounded-xl w-fit">
    {#each tabs as tab}
      <button
        class="px-4 py-2 rounded-lg text-sm font-medium transition-all {activeTab === tab.id ? 'bg-primary text-primary-content shadow-sm' : 'text-base-content/60 hover:text-base-content'}"
        onclick={() => activeTab = tab.id}>
        {tab.label}
      </button>
    {/each}
  </div>

  {#if activeTab === 'overview'}
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-fade-in">
      <StatsCard label="Онлайн" value={onlineUsers()} icon="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0" gradient="gradient-success" />
      <StatsCard label="Всего" value={overview?.total_users ?? users.length} icon="M12 4.354a4 4 0 110 7.292 4 4 0 010-7.292zM15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" gradient="gradient-primary" />
      <StatsCard label="Ноды" value="{onlineNodes()}/{nodes.length}" icon="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" gradient="gradient-info" />
      <StatsCard label="RAM" value={overview?.ram_usage ? formatBytes(overview.ram_usage) : '—'} subtitle={overview?.ram_total ? `из ${formatBytes(overview.ram_total)}` : ''} icon="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" gradient="gradient-warning" />
    </div>

    {#if overview?.cpu_cores}
      <div class="card p-5">
        <div class="text-sm text-base-content/50 mb-2">CPU ядер: {overview.cpu_cores}</div>
      </div>
    {/if}
  {/if}

  {#if activeTab === 'nodes'}
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 animate-fade-in">
      {#if nodes.length === 0}
        <div class="col-span-full text-center py-12 text-base-content/30">Нет нод</div>
      {:else}
        {#each nodes as node, i}
          <div class="card p-5 animate-slide-up" style="animation-delay: {i * 50}ms">
            <div class="flex items-start justify-between">
              <div class="flex items-center gap-3">
                <div class="w-3 h-3 rounded-full {node.is_connected ? 'bg-success animate-pulse' : 'bg-error'}"></div>
                <div>
                  <h3 class="font-medium">{node.name || node.id}</h3>
                  <p class="text-xs text-base-content/40 font-mono">{node.address}:{node.port}</p>
                </div>
              </div>
              <span class="badge badge-sm {node.is_connected ? 'badge-success' : 'badge-error'}">
                {node.is_connected ? 'Online' : 'Offline'}
              </span>
            </div>
          </div>
        {/each}
      {/if}
    </div>
  {/if}

  {#if activeTab === 'users'}
    <div class="card overflow-hidden animate-fade-in">
      <div class="overflow-x-auto">
        <table class="table table-zebra">
          <thead>
            <tr>
              <th class="text-xs font-medium uppercase tracking-wider">Имя</th>
              <th class="text-xs font-medium uppercase tracking-wider">Статус</th>
              <th class="text-xs font-medium uppercase tracking-wider">Трафик</th>
              <th class="text-xs font-medium uppercase tracking-wider">Истекает</th>
            </tr>
          </thead>
          <tbody>
            {#if users.length === 0}
              <tr><td colspan="4" class="text-center py-12 text-base-content/30">Нет данных</td></tr>
            {:else}
              {#each users as u, i}
                <tr class="animate-fade-in" style="animation-delay: {i * 15}ms">
                  <td class="font-medium">{u.username || u.name || '—'}</td>
                  <td><span class="badge badge-sm badge-success">{u.status || 'ACTIVE'}</span></td>
                  <td class="text-sm">{formatBytes(u.traffic_used)}</td>
                  <td class="text-xs text-base-content/50">{u.expires_at ? new Date(u.expires_at).toLocaleDateString('ru-RU') : '—'}</td>
                </tr>
              {/each}
            {/if}
          </tbody>
        </table>
      </div>
    </div>
  {/if}
</div>
