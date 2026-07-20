<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import Spinner from '../components/Spinner.svelte';
  import Table from '../components/Table.svelte';
  import Icon from '../components/Icon.svelte';

  let baseUrl = $state('');
  let connected = $state(false);
  let stats = $state(null);
  let nodes = $state([]);
  let nodesStats = $state(null);
  let remnawaveUsers = $state([]);
  let squads = $state([]);
  let loading = $state(true);
  let activeTab = $state('nodes');
  let connectionError = $state('');
  let actionLoading = $state({});
  let confirmAction = $state(null);
  let actionTarget = $state(null);

  let proxyMethod = $state('GET');
  let proxyPath = $state('api/system/stats');
  let proxyBody = $state('');
  let proxyResponse = $state(null);
  let proxyLoading = $state(false);
  let proxyError = $state('');
  let proxyHistory = $state([]);

  async function remnawaveProxy(method, path, body) {
    const queryPath = path.replace(/^\//, '');
    const opts = {};
    if (method !== 'GET' && body) opts.body = body;
    return await api.request(method, `/remnawave/proxy/${queryPath}`, opts);
  }

  async function loadAll() {
    loading = true;
    try {
      const connectData = await api.getRemnawaveConnect();
      baseUrl = connectData.base_url || '';

      const [s, n, u, sq, ns] = await Promise.all([
        api.getRemnawaveStats().catch(() => ({ connected: false })),
        api.getRemnawaveNodes().catch(() => ({ nodes: [] })),
        remnawaveProxy('GET', 'api/users?start=0&size=200')
          .then(d => d?.users || d?.response?.users || [])
          .catch(() => []),
        api.getRemnawaveSquads().catch(() => ({ squads: [] })),
        api.getRemnawaveNodesStats().catch(() => ({ nodes: [], system: {}, recap: {} })),
      ]);

      connected = s.connected !== false;
      stats = s;
      nodes = n.nodes || [];
      nodesStats = ns;
      remnawaveUsers = u;
      squads = sq.squads || [];
      connectionError = s.error || '';
    } catch (e) {
      toasts.error('Ошибка подключения к Remnawave: ' + e.message);
      connected = false;
      connectionError = e.message;
    } finally {
      loading = false;
    }
  }

  onMount(loadAll);

  async function doUserAction(action, username) {
    actionLoading = { ...actionLoading, [`${action}:${username}`]: true };
    try {
      if (action === 'revoke') await api.remnawaveRevoke(username);
      else if (action === 'enable') await api.remnawaveEnable(username);
      else if (action === 'disable') await api.remnawaveDisable(username);
      else if (action === 'reset-traffic') await api.remnawaveResetTraffic(username);
      else if (action === 'delete') await api.remnawaveDelete(username);
      toasts.success(`${action} выполнен для ${username}`);
      await loadAll();
    } catch (e) { toasts.error(e.message); }
    finally { actionLoading = { ...actionLoading, [`${action}:${username}`]: false }; }
  }

  async function callDirect() {
    if (!proxyPath.trim()) return;
    proxyLoading = true;
    proxyError = '';
    proxyResponse = null;
    try {
      const body = (proxyMethod !== 'GET') && proxyBody.trim()
        ? JSON.parse(proxyBody.trim()) : undefined;
      const res = await remnawaveProxy(proxyMethod, proxyPath.trim(), body);
      proxyResponse = res;
      proxyHistory = [
        { method: proxyMethod, path: proxyPath.trim(), time: new Date().toLocaleTimeString('ru-RU') },
        ...proxyHistory,
      ].slice(0, 20);
    } catch (e) { proxyError = e.message; }
    finally { proxyLoading = false; }
  }

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

  function loadColor(pct) {
    if (pct >= 90) return 'bg-danger';
    if (pct >= 70) return 'bg-warning';
    return 'bg-accent';
  }

  let totalTraffic = $derived(nodes.reduce((s, n) => s + (n.traffic_used || 0), 0));

  const nodeColumns = [
    { key: 'name', label: 'Название', sortable: true, render: (r) => `<span class="font-medium text-[13px]">${r.name || '—'}</span>` },
    { key: 'address', label: 'Адрес', sortable: true, render: (r) => `<span class="font-mono text-xs text-muted">${r.address || '—'}</span>` },
    { key: 'status', label: 'Статус', sortable: true, render: (r) => {
      const on = r.is_connected;
      return `<span class="badge ${on ? 'badge-success' : 'badge-danger'} text-[11px]">${on ? 'Online' : 'Offline'}</span>`;
    }},
    { key: 'users_count', label: 'Юзеров', sortable: true, render: (r) => `<span class="text-[13px] font-medium">${r.users_count || 0}</span>` },
    { key: 'traffic', label: 'Трафик', sortable: true, render: (r) => `<span class="text-xs text-muted">${formatBytes(r.traffic_used)}</span>` },
    { key: 'country_code', label: 'Локация', sortable: true, render: (r) => r.country_code ? `<span class="text-xs">${r.country_code}</span>` : `<span class="text-xs text-muted">—</span>` },
    { key: 'protocol', label: 'Протокол', sortable: true, render: (r) => `<span class="text-xs text-muted">${r.protocol || '—'}</span>` },
  ];

  const userColumns = [
    { key: 'username', label: 'Username', sortable: true, render: (r) => `<code class="font-mono text-xs text-accent">${r.username || '—'}</code>` },
    { key: 'status', label: 'Статус', sortable: true, render: (r) => {
      const active = r.status === 'ACTIVE' || r.status === 'active' || r.isActive === true;
      return `<span class="badge ${active ? 'badge-success' : 'badge-danger'} text-[11px]">${r.status || 'unknown'}</span>`;
    }},
    { key: 'traffic', label: 'Трафик', sortable: true, render: (r) => {
      const used = r.usedTrafficBytes ?? r.trafficUsedBytes ?? 0;
      const limit = r.dataLimitBytes ?? r.trafficLimitBytes ?? 0;
      return `<span class="text-xs text-muted">${formatBytes(used)}${limit ? ' / ' + formatBytes(limit) : ''}</span>`;
    }},
    { key: 'expire_at', label: 'Истекает', sortable: true, render: (r) => {
      const date = r.expireAt || r.expire_at;
      if (!date) return '<span class="text-xs text-muted">—</span>';
      const d = new Date(date);
      const now = Date.now();
      const diff = d.getTime() - now;
      const cls = diff < 0 ? 'text-danger' : diff < 86400000 * 3 ? 'text-warning' : 'text-muted';
      return `<span class="text-xs ${cls}">${d.toLocaleDateString('ru-RU')}</span>`;
    }},
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">VPN Инфраструктура</h1>
      <p class="text-sm text-muted mt-1">Remnawave — управление узлами и мониторинг</p>
    </div>
    <button class="btn btn-secondary" onclick={loadAll} disabled={loading}>
      <Icon name="refresh-cw" class="w-4 h-4" />
      Обновить
    </button>
  </div>

  {#if baseUrl}
    <div class="card p-3 flex items-center gap-2.5 text-xs text-muted">
      <Icon name="link" class="w-3.5 h-3.5" />
      Панель: <code class="font-mono text-accent">{baseUrl}</code>
      <span class="w-1.5 h-1.5 rounded-full {connected ? 'bg-success' : 'bg-danger'} ml-1"></span>
    </div>
  {/if}

  {#if connected}
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="stat-card">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-8 h-8 rounded-[8px] bg-success/10 flex items-center justify-center">
            <Icon name="users" class="w-4 h-4 text-success" />
          </div>
        </div>
        <p class="text-2xl font-bold">{stats?.online_users ?? 0}</p>
        <p class="text-[11px] text-muted mt-0.5">Онлайн</p>
      </div>
      <div class="stat-card">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-8 h-8 rounded-[8px] bg-accent/10 flex items-center justify-center">
            <Icon name="server" class="w-4 h-4 text-accent" />
          </div>
        </div>
        <p class="text-2xl font-bold">{nodes.length}</p>
        <p class="text-[11px] text-muted mt-0.5">Узлов</p>
      </div>
      <div class="stat-card">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-8 h-8 rounded-[8px] bg-warning/10 flex items-center justify-center">
            <Icon name="hard-drive" class="w-4 h-4 text-warning" />
          </div>
        </div>
        <p class="text-2xl font-bold">{stats?.total_users ?? remnawaveUsers.length}</p>
        <p class="text-[11px] text-muted mt-0.5">Всего юзеров</p>
      </div>
      <div class="stat-card">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-8 h-8 rounded-[8px] bg-accent/10 flex items-center justify-center">
            <Icon name="database" class="w-4 h-4 text-accent" />
          </div>
        </div>
        <p class="text-2xl font-bold">{formatBytes(totalTraffic)}</p>
        <p class="text-[11px] text-muted mt-0.5">Трафик</p>
      </div>
    </div>

    <div class="flex gap-1 bg-surface-2 p-1 rounded-[10px] w-fit overflow-x-auto whitespace-nowrap">
      {#each [
        { id: 'nodes', label: 'Узлы', icon: 'server' },
        { id: 'load', label: 'Загрузка', icon: 'activity' },
        { id: 'users', label: 'Пользователи', icon: 'users' },
        { id: 'squads', label: 'Скуады', icon: 'shield' },
        { id: 'api', label: 'API', icon: 'terminal' },
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

    {#if activeTab === 'nodes'}
      {#if nodes.length > 0}
        <div class="space-y-3">
          {#each nodes as node}
            <div class="card p-4">
              <div class="flex items-center justify-between gap-4 mb-3">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-[10px] flex items-center justify-center {node.is_connected ? 'bg-success/10' : 'bg-danger/10'}">
                    <Icon name="server" class="w-5 h-5 {node.is_connected ? 'text-success' : 'text-danger'}" />
                  </div>
                  <div>
                    <p class="text-[14px] font-semibold">{node.name || 'Узел'}</p>
                    <p class="text-[11px] text-muted font-mono">{node.address || '—'}{node.port ? ':' + node.port : ''}</p>
                  </div>
                </div>
                <span class="badge {node.is_connected ? 'badge-success' : 'badge-danger'}">{node.is_connected ? 'Online' : 'Offline'}</span>
              </div>
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div class="bg-surface-2/50 rounded-[8px] p-2.5">
                  <p class="text-[11px] text-muted">Пользователей</p>
                  <p class="text-lg font-bold mt-0.5">{node.users_count || 0}</p>
                </div>
                <div class="bg-surface-2/50 rounded-[8px] p-2.5">
                  <p class="text-[11px] text-muted">Трафик</p>
                  <p class="text-lg font-bold mt-0.5">{formatBytes(node.traffic_used)}</p>
                </div>
                <div class="bg-surface-2/50 rounded-[8px] p-2.5">
                  <p class="text-[11px] text-muted">Локация</p>
                  <p class="text-lg font-bold mt-0.5">{node.country_code || '—'}</p>
                </div>
                <div class="bg-surface-2/50 rounded-[8px] p-2.5">
                  <p class="text-[11px] text-muted">Протокол</p>
                  <p class="text-lg font-bold mt-0.5">{node.protocol || '—'}</p>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="card p-10 flex flex-col items-center gap-3 text-center">
          <Icon name="server" class="w-10 h-10 text-muted" />
          <p class="text-[15px] font-medium">Нет данных об узлах</p>
          <p class="text-[13px] text-muted">Узлы Remnawave не найдены</p>
          <button class="btn btn-secondary mt-2" onclick={loadAll}>Обновить</button>
        </div>
      {/if}

    {:else if activeTab === 'load'}
      <div class="space-y-4">
        {#if nodesStats?.system}
          {@const sys = nodesStats.system}
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="card p-5">
              <div class="flex items-center gap-2.5 mb-4">
                <Icon name="cpu" class="w-4 h-4 text-accent" />
                <h3 class="text-[14px] font-semibold">CPU Панели</h3>
              </div>
              <div class="flex items-end gap-3">
                <p class="text-3xl font-bold">{sys.cpu_cores ?? 0}<span class="text-lg text-muted"> cores</span></p>
              </div>
              {#if sys.cpu_model}
                <p class="text-[11px] text-muted mt-2">{sys.cpu_model}</p>
              {/if}
            </div>
            <div class="card p-5">
              <div class="flex items-center gap-2.5 mb-4">
                <Icon name="hard-drive" class="w-4 h-4 text-warning" />
                <h3 class="text-[14px] font-semibold">Память Панели</h3>
              </div>
              <div class="flex items-end gap-3">
                <p class="text-3xl font-bold">{sys.mem_total ? Math.round((sys.mem_used / sys.mem_total) * 100) : 0}<span class="text-lg text-muted">%</span></p>
                <p class="text-xs text-muted mb-1">{formatBytes(sys.mem_used)} / {formatBytes(sys.mem_total)}</p>
              </div>
              <div class="mt-3 h-2 bg-surface-3 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all {loadColor(sys.mem_total ? (sys.mem_used / sys.mem_total) * 100 : 0)}" style="width: {sys.mem_total ? Math.min((sys.mem_used / sys.mem_total) * 100, 100) : 0}%"></div>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="card p-5">
              <div class="flex items-center gap-2.5 mb-3">
                <Icon name="wifi" class="w-4 h-4 text-success" />
                <h3 class="text-[14px] font-semibold">Узлы</h3>
              </div>
              <div class="flex items-end gap-2">
                <p class="text-3xl font-bold text-success">{sys.nodes_online ?? 0}</p>
                <p class="text-sm text-muted mb-1">/ {sys.nodes_total ?? nodes.length} онлайн</p>
              </div>
              <div class="mt-3 flex gap-1.5 flex-wrap">
                {#each nodes as n}
                  <div class="w-2.5 h-2.5 rounded-full {n.is_connected ? 'bg-success' : 'bg-danger'}" title="{n.name}: {n.is_connected ? 'Online' : 'Offline'}"></div>
                {/each}
              </div>
            </div>
            <div class="card p-5">
              <div class="flex items-center gap-2.5 mb-3">
                <Icon name="clock" class="w-4 h-4 text-accent" />
                <h3 class="text-[14px] font-semibold">Аптайм</h3>
              </div>
              <p class="text-3xl font-bold">{formatUptime(sys.uptime)}</p>
              {#if sys.uptime}
                <p class="text-xs text-muted mt-2">Панель работает без перезагрузки</p>
              {/if}
            </div>
          </div>
        {/if}

        {#if nodesStats?.recap}
          {@const rp = nodesStats.recap}
          {#if rp.version || rp.total_nodes}
            <div class="card p-5">
              <div class="flex items-center gap-2.5 mb-3">
                <Icon name="info" class="w-4 h-4 text-accent" />
                <h3 class="text-[14px] font-semibold">Remnawave</h3>
              </div>
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div class="bg-surface-2/50 rounded-[8px] p-2.5">
                  <p class="text-[11px] text-muted">Версия</p>
                  <p class="text-lg font-bold mt-0.5">{rp.version || '—'}</p>
                </div>
                <div class="bg-surface-2/50 rounded-[8px] p-2.5">
                  <p class="text-[11px] text-muted">Узлов (всего)</p>
                  <p class="text-lg font-bold mt-0.5">{rp.total_nodes || 0}</p>
                </div>
                <div class="bg-surface-2/50 rounded-[8px] p-2.5">
                  <p class="text-[11px] text-muted">CPU ядер узлов</p>
                  <p class="text-lg font-bold mt-0.5">{rp.nodes_cpu_cores || 0}</p>
                </div>
                <div class="bg-surface-2/50 rounded-[8px] p-2.5">
                  <p class="text-[11px] text-muted">RAM узлов</p>
                  <p class="text-lg font-bold mt-0.5">{formatBytes(rp.nodes_ram)}</p>
                </div>
              </div>
            </div>
          {/if}
        {/if}

        {#if nodesStats?.nodes?.length > 0}
          <div class="card p-5">
            <h3 class="text-[14px] font-semibold mb-4">Нагрузка по узлам</h3>
            <div class="space-y-4">
              {#each nodesStats.nodes as node}
                <div class="bg-surface-2/50 rounded-[10px] p-4">
                  <div class="flex items-center justify-between gap-3 mb-3">
                    <div class="flex items-center gap-2.5">
                      <div class="w-8 h-8 rounded-[8px] {node.is_connected ? 'bg-success/10' : 'bg-danger/10'} flex items-center justify-center">
                        <Icon name="server" class="w-4 h-4 {node.is_connected ? 'text-success' : 'text-danger'}" />
                      </div>
                      <div>
                        <p class="text-[13px] font-semibold">{node.name || 'Узел'}</p>
                        <p class="text-[10px] text-muted font-mono">{node.address || '—'}</p>
                      </div>
                    </div>
                    <div class="flex items-center gap-2">
                      <span class="badge {node.is_online ? 'badge-success' : 'badge-danger'} text-[10px]">{node.is_online ? 'Online' : 'Offline'}</span>
                      {#if node.is_xray_running}
                        <span class="badge badge-accent text-[10px]">Xray</span>
                      {/if}
                    </div>
                  </div>
                  <div class="grid grid-cols-2 sm:grid-cols-5 gap-2 text-center">
                    <div class="bg-surface-3/50 rounded-[6px] p-2">
                      <p class="text-[10px] text-muted">CPU</p>
                      <p class="text-sm font-bold mt-0.5">{node.cpu_count || 0} cores</p>
                      {#if node.cpu_model}
                        <p class="text-[9px] text-muted truncate" title={node.cpu_model}>{node.cpu_model}</p>
                      {/if}
                    </div>
                    <div class="bg-surface-3/50 rounded-[6px] p-2">
                      <p class="text-[10px] text-muted">RAM</p>
                      <p class="text-sm font-bold mt-0.5">{node.total_ram || '—'}</p>
                    </div>
                    <div class="bg-surface-3/50 rounded-[6px] p-2">
                      <p class="text-[10px] text-muted">Онлайн</p>
                      <p class="text-sm font-bold mt-0.5">{node.users_online || 0}</p>
                    </div>
                    <div class="bg-surface-3/50 rounded-[6px] p-2">
                      <p class="text-[10px] text-muted">Трафик</p>
                      <p class="text-sm font-bold mt-0.5">{formatBytes(node.traffic_used)}</p>
                      {#if node.traffic_limit}
                        <p class="text-[9px] text-muted">/ {formatBytes(node.traffic_limit)}</p>
                      {/if}
                    </div>
                    <div class="bg-surface-3/50 rounded-[6px] p-2">
                      <p class="text-[10px] text-muted">Xray uptime</p>
                      <p class="text-sm font-bold mt-0.5">{node.xray_uptime || '—'}</p>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {:else}
          <div class="card p-10 flex flex-col items-center gap-3 text-center">
            <Icon name="activity" class="w-10 h-10 text-muted" />
            <p class="text-[15px] font-medium">Нет данных о нагрузке узлов</p>
            <button class="btn btn-secondary mt-2" onclick={loadAll}>Обновить</button>
          </div>
        {/if}

        {#if nodesStats?.system}
          <div class="card p-5">
            <h3 class="text-[14px] font-semibold mb-3">Системные данные</h3>
            <pre class="text-[11px] text-muted font-mono overflow-x-auto whitespace-pre-wrap max-h-64 overflow-y-auto bg-surface-2/50 rounded-[8px] p-3">{JSON.stringify({ system: nodesStats.system, recap: nodesStats.recap }, null, 2)}</pre>
          </div>
        {/if}
      </div>

    {:else if activeTab === 'users'}
      {#if remnawaveUsers.length > 0}
        <div class="space-y-2">
          {#each remnawaveUsers as user}
            {@const username = user.username || user.shortUuid || '—'}
            {@const isActive = user.status === 'ACTIVE' || user.status === 'active'}
            <div class="card p-4 flex flex-col sm:flex-row sm:items-center gap-3">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <code class="font-mono text-xs text-accent">{username}</code>
                  <span class="badge {isActive ? 'badge-success' : 'badge-danger'} text-[10px]">{user.status || 'unknown'}</span>
                </div>
                <div class="flex gap-4 mt-1 text-[11px] text-muted">
                  <span>Трафик: {formatBytes(user.usedTrafficBytes ?? 0)}{user.dataLimitBytes ? ' / ' + formatBytes(user.dataLimitBytes) : ''}</span>
                  {#if user.expireAt}
                    <span>Истекает: {new Date(user.expireAt).toLocaleDateString('ru-RU')}</span>
                  {/if}
                </div>
              </div>
              <div class="flex gap-1.5 shrink-0 flex-wrap">
                {#if isActive}
                  <button class="btn btn-ghost btn-xs text-warning" onclick={() => doUserAction('disable', username)}
                    disabled={actionLoading[`disable:${username}`]} title="Отключить">
                    <Icon name="pause" class="w-3 h-3" /> Откл.
                  </button>
                  <button class="btn btn-ghost btn-xs text-accent" onclick={() => doUserAction('reset-traffic', username)}
                    disabled={actionLoading[`reset-traffic:${username}`]} title="Сбросить трафик">
                    <Icon name="refreshCw" class="w-3 h-3" />
                  </button>
                  <button class="btn btn-ghost btn-xs text-danger" onclick={() => doUserAction('revoke', username)}
                    disabled={actionLoading[`revoke:${username}`]} title="Отозвать подписку">
                    <Icon name="shieldOff" class="w-3 h-3" /> Отозвать
                  </button>
                {:else}
                  <button class="btn btn-ghost btn-xs text-success" onclick={() => doUserAction('enable', username)}
                    disabled={actionLoading[`enable:${username}`]} title="Включить">
                    <Icon name="play" class="w-3 h-3" /> Вкл.
                  </button>
                {/if}
                <button class="btn btn-ghost btn-xs text-danger" onclick={() => doUserAction('delete', username)}
                  disabled={actionLoading[`delete:${username}`]} title="Удалить">
                  <Icon name="trash-2" class="w-3 h-3" />
                </button>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="card p-10 flex flex-col items-center gap-3 text-center">
          <Icon name="users" class="w-10 h-10 text-muted" />
          <p class="text-[15px] font-medium">Нет данных о пользователях</p>
          <p class="text-[13px] text-muted">Пользователи Remnawave не найдены</p>
          <button class="btn btn-secondary mt-2" onclick={loadAll}>Обновить</button>
        </div>
      {/if}

    {:else if activeTab === 'squads'}
      {#if squads.length > 0}
        <div class="space-y-2">
          {#each squads as squad}
            <div class="card p-4 flex items-center justify-between gap-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-[10px] bg-accent/10 flex items-center justify-center">
                  <Icon name="shield" class="w-5 h-5 text-accent" />
                </div>
                <div>
                  <p class="text-[14px] font-semibold">{squad.name}</p>
                  <p class="text-[11px] text-muted">{squad.inbound_tags?.join(', ') || '—'}</p>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <div class="text-right">
                  <p class="text-lg font-bold">{squad.total_users || 0}</p>
                  <p class="text-[10px] text-muted">юзеров</p>
                </div>
                <span class="badge {squad.is_disabled ? 'badge-danger' : 'badge-success'} text-[10px]">{squad.is_disabled ? 'Откл.' : 'Активен'}</span>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="card p-10 flex flex-col items-center gap-3 text-center">
          <Icon name="shield" class="w-10 h-10 text-muted" />
          <p class="text-[15px] font-medium">Нет данных о скуадах</p>
          <p class="text-[13px] text-muted">Скуады Remnawave не найдены</p>
          <button class="btn btn-secondary mt-2" onclick={loadAll}>Обновить</button>
        </div>
      {/if}

    {:else if activeTab === 'api'}
      <div class="space-y-4">
        <div class="card p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-[15px] font-semibold">API Remnawave (прокси)</h3>
            <p class="text-[11px] text-muted">Запросы проходят через бэкенд</p>
          </div>
          <div class="flex flex-col sm:flex-row gap-2 mb-3">
            <div class="flex gap-2">
              <select bind:value={proxyMethod} class="select w-24 text-xs font-mono">
                <option>GET</option>
                <option>POST</option>
                <option>PUT</option>
                <option>PATCH</option>
                <option>DELETE</option>
              </select>
              <input type="text" bind:value={proxyPath} class="input flex-1 font-mono text-xs" placeholder="api/system/stats" />
            </div>
            <button class="btn btn-primary" onclick={callDirect} disabled={proxyLoading || !proxyPath.trim()}>
              {#if proxyLoading}
                <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              {:else}
                <Icon name="terminal" class="w-4 h-4" />
              {/if}
              Выполнить
            </button>
          </div>
          {#if proxyMethod === 'POST' || proxyMethod === 'PUT' || proxyMethod === 'PATCH'}
            <div class="mb-3">
              <textarea bind:value={proxyBody} class="textarea w-full h-24 font-mono text-xs" placeholder="JSON body"></textarea>
            </div>
          {/if}
          {#if proxyError}
            <div class="bg-danger/10 border border-danger/20 rounded-[10px] p-3.5">
              <p class="text-[13px] text-danger font-medium">Ошибка</p>
              <p class="text-xs text-danger/80 mt-0.5">{proxyError}</p>
            </div>
          {/if}
          {#if proxyResponse}
            <div>
              <div class="flex items-center justify-between mb-2">
                <p class="text-xs text-muted">Ответ:</p>
                <button class="btn btn-xs btn-ghost" onclick={() => navigator.clipboard.writeText(JSON.stringify(proxyResponse, null, 2))}>
                  <Icon name="copy" class="w-3 h-3" /> Копировать
                </button>
              </div>
              <pre class="bg-surface-2 rounded-[10px] p-3.5 text-[11px] font-mono text-muted overflow-x-auto max-h-96 overflow-y-auto">{JSON.stringify(proxyResponse, null, 2)}</pre>
            </div>
          {/if}
        </div>

        {#if proxyHistory.length > 0}
          <div class="card p-5">
            <h3 class="text-[15px] font-semibold mb-3">История запросов</h3>
            <div class="space-y-1 max-h-48 overflow-y-auto">
              {#each proxyHistory as h, i}
                <div class="flex items-center gap-2.5 py-1.5 px-2.5 rounded-[7px] {i === 0 ? 'bg-surface-3' : ''}">
                  <span class="font-mono text-[11px] font-bold text-accent min-w-[4ch]">{h.method}</span>
                  <span class="font-mono text-xs text-muted flex-1 truncate">{h.path}</span>
                  <span class="text-[10px] text-muted">{h.time}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <div class="card p-5">
          <h3 class="text-[15px] font-semibold mb-3">Доступные эндпоинты</h3>
          <div class="space-y-1.5 text-[12px] font-mono">
            {#each [
              { method: 'GET', path: 'api/system/stats', desc: 'Статистика системы' },
              { method: 'GET', path: 'api/nodes', desc: 'Список узлов' },
              { method: 'GET', path: 'api/users?start=0&size=50', desc: 'Пользователи' },
              { method: 'GET', path: 'api/users/by-username/{username}', desc: 'Поиск пользователя' },
              { method: 'POST', path: 'api/users', desc: 'Создать пользователя' },
              { method: 'POST', path: 'api/users/{uuid}/actions/revoke', desc: 'Отозвать ключ' },
              { method: 'POST', path: 'api/users/{uuid}/actions/reset-traffic', desc: 'Сбросить трафик' },
              { method: 'GET', path: 'api/internal-squads', desc: 'Список скуадов' },
            ] as ep}
              <button class="w-full flex items-center gap-2.5 py-1.5 px-2.5 rounded-[7px] hover:bg-surface-2 transition-colors" onclick={() => { proxyMethod = ep.method; proxyPath = ep.path; proxyBody = ''; activeTab = 'api'; }}>
                <span class="font-bold text-[11px] text-accent min-w-[4ch]">{ep.method}</span>
                <span class="text-muted flex-1 truncate">{ep.path}</span>
                <span class="text-muted/60 text-[11px]">{ep.desc}</span>
              </button>
            {/each}
          </div>
        </div>
      </div>
    {/if}
  {:else if !loading}
    <div class="card p-12 flex flex-col items-center gap-3 text-center">
      <div class="w-14 h-14 rounded-[12px] bg-danger/10 flex items-center justify-center">
        <Icon name="wifiOff" class="w-7 h-7 text-danger" />
      </div>
      <p class="text-[17px] font-semibold">Не удалось подключиться к Remnawave</p>
      <p class="text-[13px] text-muted max-w-md">{connectionError || 'Проверьте настройки в .env (REMNAWAVE_URL_PANEL + REMNAWAVE_ADMIN_TOKEN)'}</p>
      <button class="btn btn-primary mt-2" onclick={loadAll}>
        <Icon name="refreshCw" class="w-4 h-4" />
        Повторить
      </button>
    </div>
  {/if}
</div>
