<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import Spinner from '../components/Spinner.svelte';
  import Table from '../components/Table.svelte';
  import Icon from '../components/Icon.svelte';

  let status = $state(null);
  let nodes = $state([]);
  let remnawaveUsers = $state([]);
  let loading = $state(true);
  let activeTab = $state('overview');

  async function loadAll() {
    loading = true;
    try {
      const [s, n, u] = await Promise.all([
        api.getRemnawaveStatus().catch(() => null),
        api.getRemnawaveNodes().catch(() => []),
        api.getRemnawaveUsers().catch(() => []),
      ]);
      status = s;
      nodes = Array.isArray(n) ? n : (n?.nodes || []);
      remnawaveUsers = Array.isArray(u) ? u : (u?.users || []);
    } catch (e) {
      toasts.error('Ошибка загрузки Remnawave: ' + e.message);
    } finally {
      loading = false;
    }
  }

  onMount(loadAll);

  function formatBytes(bytes) {
    if (!bytes && bytes !== 0) return '—';
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  function formatUptime(seconds) {
    if (!seconds) return '—';
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const parts = [];
    if (d > 0) parts.push(`${d}д`);
    if (h > 0) parts.push(`${h}ч`);
    parts.push(`${m}м`);
    return parts.join(' ');
  }

  const nodeColumns = [
    { key: 'name', label: 'Название', sortable: true, render: (r) => `<span class="font-medium text-[13px]">${r.name || r.address || '—'}</span>` },
    { key: 'address', label: 'Адрес', sortable: true, render: (r) => `<span class="font-mono text-xs text-muted">${r.address || r.ip || '—'}</span>` },
    { key: 'status', label: 'Статус', sortable: true, render: (r) => {
      const online = r.is_active !== false && r.status !== 'offline' && r.is_online !== false;
      return `<span class="badge ${online ? 'badge-success' : 'badge-danger'}">${online ? 'Online' : 'Offline'}</span>`;
    }},
    { key: 'users_count', label: 'Пользователей', sortable: true, render: (r) => `<span class="text-[13px] font-medium">${r.users_count ?? r.userCount ?? r.user_count ?? 0}</span>` },
    { key: 'load', label: 'Нагрузка', sortable: true, render: (r) => {
      const cpu = r.cpu ?? r.cpu_usage;
      const mem = r.mem ?? r.mem_usage ?? r.ram_usage;
      return `<span class="text-xs text-muted">${cpu != null ? 'CPU: ' + cpu + '%' : ''}${mem != null ? ' MEM: ' + mem + '%' : ''}${cpu == null && mem == null ? '—' : ''}</span>`;
    }},
  ];

  const userColumns = [
    { key: 'username', label: 'Username', sortable: true, render: (r) => `<code class="font-mono text-xs text-accent">${r.username || r.shortUuid || '—'}</code>` },
    { key: 'status', label: 'Статус', sortable: true, render: (r) => {
      const active = r.status === 'active' || r.is_active === true || r.isActive === true;
      const expired = r.status === 'expired' || r.is_expired === true;
      return `<span class="badge ${active ? 'badge-success' : expired ? 'badge-danger' : 'badge-warning'}">${r.status || (active ? 'active' : 'disabled')}</span>`;
    }},
    { key: 'traffic', label: 'Трафик', sortable: true, render: (r) => {
      const used = r.used_traffic_bytes ?? r.trafficUsedBytes ?? r.data_limit_bytes ?? 0;
      const total = r.data_limit_bytes ?? r.dataLimitBytes ?? 0;
      return `<span class="text-xs text-muted">${formatBytes(used)}${total ? ' / ' + formatBytes(total) : ''}</span>`;
    }},
    { key: 'expire_at', label: 'Истекает', sortable: true, render: (r) => {
      const date = r.expire_at || r.expireAt || r.expiration_date;
      if (!date) return '<span class="text-xs text-muted">—</span>';
      const d = new Date(date);
      return `<span class="text-xs text-muted">${d.toLocaleDateString('ru-RU')}</span>`;
    }},
    { key: 'node', label: 'Узел', sortable: true, render: (r) => {
      const node = r.node_name || r.nodeName || r.node?.name || r.node?.address || (r.subscription_url ? 'подкл.' : '');
      return `<span class="text-xs text-muted">${node || '—'}</span>`;
    }},
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight text-text">Remnawave</h1>
      <p class="text-sm text-muted mt-1">Состояние VPN панели и управление</p>
    </div>
    <button class="btn btn-secondary" onclick={loadAll} disabled={loading}>
      <Icon name="refresh-cw" class="w-4 h-4" />
      Обновить
    </button>
  </div>

  {#if status}
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="stat-card">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-8 h-8 rounded-[8px] bg-accent/10 flex items-center justify-center">
            <Icon name="power" class="w-4 h-4 text-accent" />
          </div>
        </div>
        <p class="text-2xl font-bold {status.connected ? 'text-success' : 'text-danger'}">{status.connected ? 'Online' : 'Offline'}</p>
        <p class="text-[11px] text-muted mt-0.5">Статус подключения</p>
      </div>
      <div class="stat-card">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-8 h-8 rounded-[8px] bg-success/10 flex items-center justify-center">
            <Icon name="users" class="w-4 h-4 text-success" />
          </div>
        </div>
        <p class="text-2xl font-bold">{status.stats?.users_active ?? status.stats?.online_users ?? remnawaveUsers.length}</p>
        <p class="text-[11px] text-muted mt-0.5">Активных пользователей</p>
      </div>
      <div class="stat-card">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-8 h-8 rounded-[8px] bg-warning/10 flex items-center justify-center">
            <Icon name="server" class="w-4 h-4 text-warning" />
          </div>
        </div>
        <p class="text-2xl font-bold">{nodes.length}</p>
        <p class="text-[11px] text-muted mt-0.5">Узлов</p>
      </div>
      <div class="stat-card">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-8 h-8 rounded-[8px] bg-accent/10 flex items-center justify-center">
            <Icon name="hard-drive" class="w-4 h-4 text-accent" />
          </div>
        </div>
        <p class="text-2xl font-bold">{formatBytes(status.stats?.total_users ?? 0)}</p>
        <p class="text-[11px] text-muted mt-0.5">Всего пользователей</p>
      </div>
    </div>

    {#if status.stats}
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {#if status.stats.cpu_usage != null}
          <div class="card p-4">
            <p class="text-[11px] text-muted">CPU</p>
            <div class="mt-1.5 flex items-center gap-2">
              <div class="flex-1 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                <div class="h-full rounded-full bg-accent transition-all" style="width: {status.stats.cpu_usage}%"></div>
              </div>
              <span class="text-xs font-medium">{status.stats.cpu_usage}%</span>
            </div>
          </div>
        {/if}
        {#if status.stats.mem_used != null && status.stats.mem_total != null}
          <div class="card p-4">
            <p class="text-[11px] text-muted">Память</p>
            <div class="mt-1.5 flex items-center gap-2">
              @const memPct = Math.round((status.stats.mem_used / status.stats.mem_total) * 100)
              <div class="flex-1 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                <div class="h-full rounded-full bg-warning transition-all" style="width: {memPct}%"></div>
              </div>
              <span class="text-xs font-medium">{memPct}%</span>
            </div>
          </div>
        {/if}
        {#if status.stats.nodes_online != null}
          <div class="card p-4">
            <p class="text-[11px] text-muted">Узлы онлайн</p>
            <p class="text-lg font-bold text-success mt-1">{status.stats.nodes_online}{status.stats.nodes_total != null ? '/' + status.stats.nodes_total : ''}</p>
          </div>
        {/if}
        {#if status.stats.uptime != null}
          <div class="card p-4">
            <p class="text-[11px] text-muted">Аптайм</p>
            <p class="text-lg font-bold mt-1">{formatUptime(status.stats.uptime)}</p>
          </div>
        {/if}
      </div>
    {/if}

    <div class="flex gap-1 bg-surface-2 p-1 rounded-[10px] w-fit">
      {#each [
        { id: 'overview', label: 'Обзор', icon: 'bar-chart-3' },
        { id: 'nodes', label: 'Узлы', icon: 'server' },
        { id: 'users', label: 'Пользователи', icon: 'users' },
      ] as tab}
        <button
          class="px-3.5 py-1.5 text-xs font-medium rounded-[7px] transition-all {activeTab === tab.id ? 'bg-surface text-text shadow-sm' : 'text-muted hover:text-text'}"
          onclick={() => activeTab = tab.id}>
          <span class="flex items-center gap-1.5">
            <Icon name={tab.icon} class="w-3.5 h-3.5" />
            {tab.label}
          </span>
        </button>
      {/each}
    </div>

    {#if activeTab === 'overview'}
      <div class="card p-5">
        <h3 class="text-[15px] font-semibold mb-3">Детали подключения</h3>
        <pre class="text-[12px] text-muted font-mono overflow-x-auto whitespace-pre-wrap max-h-96 overflow-y-auto">{
          JSON.stringify(status.stats || status, null, 2)
        }</pre>
      </div>
    {:else if activeTab === 'nodes'}
      {#if nodes.length > 0}
        <Table columns={nodeColumns} data={nodes} />
      {:else}
        <div class="card p-10 flex flex-col items-center gap-3 text-center">
          <Icon name="server" class="w-10 h-10 text-muted" />
          <p class="text-[15px] font-medium">Нет данных об узлах</p>
          <p class="text-[13px] text-muted">Узлы Remnawave не найдены или API недоступно</p>
          <button class="btn btn-secondary mt-2" onclick={loadAll}>Обновить</button>
        </div>
      {/if}
    {:else if activeTab === 'users'}
      {#if remnawaveUsers.length > 0}
        <Table columns={userColumns} data={remnawaveUsers} />
      {:else}
        <div class="card p-10 flex flex-col items-center gap-3 text-center">
          <Icon name="users" class="w-10 h-10 text-muted" />
          <p class="text-[15px] font-medium">Нет данных о пользователях</p>
          <p class="text-[13px] text-muted">Пользователи Remnawave не найдены</p>
          <button class="btn btn-secondary mt-2" onclick={loadAll}>Обновить</button>
        </div>
      {/if}
    {/if}
  {:else if !loading}
    <div class="card p-12 flex flex-col items-center gap-3 text-center">
      <div class="w-14 h-14 rounded-[12px] bg-danger/10 flex items-center justify-center">
        <Icon name="wifi-off" class="w-7 h-7 text-danger" />
      </div>
      <p class="text-[17px] font-semibold">Не удалось подключиться к Remnawave</p>
      <p class="text-[13px] text-muted max-w-md">Проверьте настройки подключения к Remnawave панели в файле .env (REMNAWAVE_ADMIN_PANEL, REMNAWAVE_ADMIN_LOGIN/PASSWORD)</p>
      <button class="btn btn-primary mt-2" onclick={loadAll}>
        <Icon name="refresh-cw" class="w-4 h-4" />
        Повторить
      </button>
    </div>
  {/if}
</div>
