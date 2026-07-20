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
  let remnawaveUsers = $state([]);
  let loading = $state(true);
  let activeTab = $state('nodes');
  let connectionError = $state('');

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

      const [s, n, u] = await Promise.all([
        api.getRemnawaveStats().catch(() => ({ connected: false })),
        api.getRemnawaveNodes().catch(() => ({ nodes: [] })),
        remnawaveProxy('GET', 'api/users?start=0&size=200')
          .then(d => d?.users || d?.response?.users || [])
          .catch(() => []),
      ]);

      connected = s.connected !== false;
      stats = s;
      nodes = n.nodes || [];
      remnawaveUsers = u;
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
        {#if stats}
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="card p-5">
              <div class="flex items-center gap-2.5 mb-4">
                <Icon name="cpu" class="w-4 h-4 text-accent" />
                <h3 class="text-[14px] font-semibold">CPU</h3>
              </div>
              <div class="flex items-end gap-3">
                <p class="text-3xl font-bold">{stats.cpu_usage ?? 0}<span class="text-lg text-muted">%</span></p>
              </div>
              <div class="mt-3 h-2 bg-surface-3 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all {loadColor(stats.cpu_usage || 0)}" style="width: {Math.min(stats.cpu_usage || 0, 100)}%"></div>
              </div>
            </div>
            <div class="card p-5">
              <div class="flex items-center gap-2.5 mb-4">
                <Icon name="hard-drive" class="w-4 h-4 text-warning" />
                <h3 class="text-[14px] font-semibold">Память</h3>
              </div>
              <div class="flex items-end gap-3">
                <p class="text-3xl font-bold">{stats.mem_total ? Math.round((stats.mem_used / stats.mem_total) * 100) : 0}<span class="text-lg text-muted">%</span></p>
                <p class="text-xs text-muted mb-1">{formatBytes(stats.mem_used)} / {formatBytes(stats.mem_total)}</p>
              </div>
              <div class="mt-3 h-2 bg-surface-3 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all {loadColor(stats.mem_total ? (stats.mem_used / stats.mem_total) * 100 : 0)}" style="width: {stats.mem_total ? Math.min((stats.mem_used / stats.mem_total) * 100, 100) : 0}%"></div>
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
                <p class="text-3xl font-bold text-success">{stats.nodes_online ?? 0}</p>
                <p class="text-sm text-muted mb-1">/ {stats.nodes_total ?? nodes.length} онлайн</p>
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
              <p class="text-3xl font-bold">{formatUptime(stats.uptime)}</p>
              {#if stats.uptime}
                <p class="text-xs text-muted mt-2">Панель работает без перезагрузки</p>
              {/if}
            </div>
          </div>

          {#if nodes.length > 0}
            <div class="card p-5">
              <h3 class="text-[14px] font-semibold mb-3">Нагрузка по узлам</h3>
              <div class="space-y-3">
                {#each nodes as node}
                  <div class="flex items-center gap-3">
                    <span class="text-[13px] font-medium min-w-[120px] truncate">{node.name || node.address}</span>
                    <div class="flex-1 h-2 bg-surface-3 rounded-full overflow-hidden">
                      <div class="h-full rounded-full {node.is_connected ? 'bg-success' : 'bg-danger'}" style="width: {node.is_connected ? '100' : '0'}%"></div>
                    </div>
                    <span class="text-xs text-muted min-w-[4ch] text-right">{node.users_count || 0}</span>
                  </div>
                {/each}
              </div>
              <p class="text-[11px] text-muted mt-3">Показано количество пользователей на узле</p>
            </div>
          {/if}
        {:else}
          <div class="card p-10 flex flex-col items-center gap-3 text-center">
            <Icon name="activity" class="w-10 h-10 text-muted" />
            <p class="text-[15px] font-medium">Нет данных о нагрузке</p>
            <button class="btn btn-secondary mt-2" onclick={loadAll}>Обновить</button>
          </div>
        {/if}

        {#if stats?.raw}
          <div class="card p-5">
            <h3 class="text-[14px] font-semibold mb-3">Сырые данные</h3>
            <pre class="text-[11px] text-muted font-mono overflow-x-auto whitespace-pre-wrap max-h-64 overflow-y-auto bg-surface-2/50 rounded-[8px] p-3">{JSON.stringify(stats.raw, null, 2)}</pre>
          </div>
        {/if}
      </div>

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
