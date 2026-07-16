<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import Spinner from '../components/Spinner.svelte';
  import Table from '../components/Table.svelte';
  import Icon from '../components/Icon.svelte';

  let baseUrl = $state('');
  let token = $state('');
  let status = $state(null);
  let nodes = $state([]);
  let remnawaveUsers = $state([]);
  let loading = $state(true);
  let activeTab = $state('overview');

  let proxyMethod = $state('GET');
  let proxyPath = $state('api/system/stats');
  let proxyBody = $state('');
  let proxyResponse = $state(null);
  let proxyLoading = $state(false);
  let proxyError = $state('');
  let proxyHistory = $state([]);

  async function getToken() {
    const data = await api.getRemnawaveConnect();
    baseUrl = data.base_url;
    token = data.token;
  }

  async function remnawaveFetch(method, path, body, retries = 1) {
    if (!token) await getToken();
    const res = await fetch(`${baseUrl}/${path.replace(/^\//, '')}`, {
      method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (res.status === 401 && retries > 0) {
      token = '';
      await getToken();
      return remnawaveFetch(method, path, body, retries - 1);
    }
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`Remnawave ${res.status}: ${text.slice(0, 200)}`);
    }
    if (res.status === 204) return null;
    return res.json();
  }

  async function loadAll() {
    loading = true;
    try {
      await getToken();
      const [s, n, u] = await Promise.all([
        remnawaveFetch('GET', 'api/system/stats').catch(() => null),
        remnawaveFetch('GET', 'api/nodes').then(d => d?.nodes || []).catch(() => []),
        remnawaveFetch('GET', 'api/users?start=0&size=100').then(d => d?.users || []).catch(() => []),
      ]);
      status = s ? { connected: true, stats: s } : { connected: false };
      nodes = n;
      remnawaveUsers = u;
    } catch (e) {
      toasts.error('Ошибка подключения к Remnawave: ' + e.message);
      status = { connected: false, error: e.message };
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
      const body = (proxyMethod === 'POST' || proxyMethod === 'PUT' || proxyMethod === 'PATCH') && proxyBody.trim()
        ? JSON.parse(proxyBody.trim()) : undefined;
      const res = await remnawaveFetch(proxyMethod, proxyPath.trim(), body);
      proxyResponse = res;
      proxyHistory = [{ method: proxyMethod, path: proxyPath.trim(), time: new Date().toLocaleTimeString('ru-RU') }, ...proxyHistory].slice(0, 20);
    } catch (e) {
      proxyError = e.message;
    } finally {
      proxyLoading = false;
    }
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
      <p class="text-sm text-muted mt-1">Прямое подключение к API Remnawave</p>
    </div>
    <button class="btn btn-secondary" onclick={loadAll} disabled={loading}>
      <Icon name="refresh-cw" class="w-4 h-4" />
      Обновить
    </button>
  </div>

  {#if baseUrl}
    <div class="card p-3 flex items-center gap-2.5 text-xs text-muted">
      <Icon name="link" class="w-3.5 h-3.5" />
      Подключено к: <code class="font-mono text-accent">{baseUrl}</code>
      <span class="w-1.5 h-1.5 rounded-full bg-success ml-1"></span>
    </div>
  {/if}

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
        <p class="text-2xl font-bold">{status.stats?.total_users ?? '—'}</p>
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
          {@const memPct = Math.round((status.stats.mem_used / status.stats.mem_total) * 100)}
          <div class="card p-4">
            <p class="text-[11px] text-muted">Память</p>
            <div class="mt-1.5 flex items-center gap-2">
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
        { id: 'api', label: 'Full API', icon: 'terminal' },
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
          <p class="text-[13px] text-muted">Узлы Remnawave не найдены</p>
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
    {:else if activeTab === 'api'}
      <div class="space-y-4">
        <div class="card p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-[15px] font-semibold">Прямой вызов API Remnawave</h3>
            <p class="text-[11px] text-muted">Использует токен из /api/v1/remnawave/connect</p>
          </div>
          <div class="flex gap-2 mb-3">
            <select bind:value={proxyMethod} class="select w-24 text-xs font-mono">
              <option>GET</option>
              <option>POST</option>
              <option>PUT</option>
              <option>PATCH</option>
              <option>DELETE</option>
            </select>
            <input type="text" bind:value={proxyPath} class="input flex-1 font-mono text-xs" placeholder="api/system/stats" />
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
              <pre class="bg-surface-2 rounded-[10px] p-3.5 text-[11px] font-mono text-muted overflow-x-auto max-h-96 overflow-y-auto">{
                JSON.stringify(proxyResponse, null, 2)
              }</pre>
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
          <h3 class="text-[15px] font-semibold mb-3">Доступные эндпоинты Remnawave</h3>
          <p class="text-[13px] text-muted mb-3">Все эндпоинты Remnawave API доступны напрямую через браузер. Примеры:</p>
          <div class="space-y-1.5 text-[12px] font-mono">
            {#each [
              { method: 'GET', path: 'api/system/stats', desc: 'Статистика системы' },
              { method: 'GET', path: 'api/system/health', desc: 'Health check' },
              { method: 'GET', path: 'api/nodes', desc: 'Список узлов' },
              { method: 'GET', path: 'api/users?start=0&size=50', desc: 'Список пользователей' },
              { method: 'GET', path: 'api/users/by-username/{username}', desc: 'Поиск пользователя' },
              { method: 'POST', path: 'api/users', desc: 'Создать пользователя' },
              { method: 'PATCH', path: 'api/users/{uuid}', desc: 'Изменить пользователя' },
              { method: 'POST', path: 'api/users/{uuid}/actions/revoke', desc: 'Отозвать ключ' },
              { method: 'POST', path: 'api/users/{uuid}/actions/reset-traffic', desc: 'Сбросить трафик' },
              { method: 'GET', path: 'api/hosts', desc: 'Список хостов' },
              { method: 'GET', path: 'api/subscription-settings', desc: 'Настройки подписок' },
              { method: 'GET', path: 'api/config-profiles', desc: 'Профили конфигурации' },
              { method: 'GET', path: 'api/snippets', desc: 'Сниппеты' },
              { method: 'GET', path: 'api/internal-squads', desc: 'Внутренние группы' },
              { method: 'GET', path: 'api/external-squads', desc: 'Внешние группы' },
              { method: 'GET', path: 'api/remnawave-settings', desc: 'Настройки Remnawave' },
              { method: 'GET', path: 'api/system/stats/bandwidth', desc: 'Статистика трафика' },
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
        <Icon name="wifi-off" class="w-7 h-7 text-danger" />
      </div>
      <p class="text-[17px] font-semibold">Не удалось подключиться к Remnawave</p>
      <p class="text-[13px] text-muted max-w-md">Проверьте настройки в .env (REMNAWAVE_ADMIN_PANEL + REMNAWAVE_ADMIN_TOKEN или REMNAWAVE_ADMIN_LOGIN/PASSWORD)</p>
      <button class="btn btn-primary mt-2" onclick={loadAll}>
        <Icon name="refresh-cw" class="w-4 h-4" />
        Повторить
      </button>
    </div>
  {/if}
</div>
