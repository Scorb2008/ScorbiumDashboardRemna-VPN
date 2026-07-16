<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDateTime } from '../lib/utils.js';
  import Spinner from '../components/Spinner.svelte';
  import Table from '../components/Table.svelte';
  import Icon from '../components/Icon.svelte';

  let status = $state(null);
  let nodes = $state([]);
  let loading = $state(true);

  async function loadRemnawave() {
    loading = true;
    try {
      const [s, n] = await Promise.all([
        api.getRemnawaveStatus(),
        api.getRemnawaveNodes()
      ]);
      status = s;
      nodes = Array.isArray(n) ? n : (n.items || []);
    } catch (e) { toasts.error('Ошибка загрузки: ' + e.message); }
    finally { loading = false; }
  }

  onMount(loadRemnawave);

  function formatBytes(bytes) {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  const nodeColumns = [
    { key: 'name', label: 'Название', sortable: true, render: (r) => `<span class="font-medium">${r.name || r.id || '—'}</span>` },
    { key: 'address', label: 'Адрес', sortable: true, render: (r) => `<span class="font-mono text-xs text-zinc-400">${r.address || r.ip || '—'}</span>` },
    { key: 'status', label: 'Статус', sortable: true, render: (r) => `<span class="badge ${(r.is_active !== false && r.status !== 'offline') ? 'badge-success' : 'badge-danger'}">${(r.is_active !== false && r.status !== 'offline') ? 'Онлайн' : 'Оффлайн'}</span>` },
    { key: 'users_count', label: 'Пользователей', sortable: true, render: (r) => `${r.users_count ?? r.user_count ?? 0}` },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">Remnawave</h1>
      <p class="text-sm text-muted mt-1">Состояние VPN панели</p>
    </div>
    <button class="btn btn-secondary" onclick={loadRemnawave}><Icon name="refresh-cw" class="w-4 h-4" /> Обновить</button>
  </div>

  {#if status}
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {#each [
        ['Статус', status.status || (status.is_online ? 'Онлайн' : 'Оффлайн'), status.is_online !== false ? 'text-green-400' : 'text-red-400'],
        ['Узлов', nodes.length, ''],
        ['Пользователей', status.users_count ?? status.total_users ?? '—', ''],
        ['Версия', status.version || status.app_version || '—', ''],
      ] as [label, value, cls]}
        <div class="card p-4 text-center">
          <p class="text-2xl font-bold {cls}">{value}</p>
          <p class="text-[11px] text-muted mt-1">{label}</p>
        </div>
      {/each}
    </div>

    {#if nodes.length > 0}
      <div>
        <h2 class="text-[17px] font-semibold mb-3">Узлы</h2>
        <Table columns={nodeColumns} data={nodes} />
      </div>
    {/if}

    {#if status.raw}
      <div class="card p-5">
        <h3 class="text-[15px] font-semibold mb-3">Детали</h3>
        <pre class="text-[12px] text-muted font-mono overflow-x-auto whitespace-pre-wrap">{JSON.stringify(status.raw, null, 2)}</pre>
      </div>
    {/if}
  {:else if !loading}
    <div class="card p-12 flex flex-col items-center gap-3 text-center">
      <Icon name="wifi-off" class="w-10 h-10 text-muted" />
      <p class="text-[15px] font-medium">Не удалось подключиться</p>
      <p class="text-[13px] text-muted">Проверьте настройки Remnawave</p>
    </div>
  {/if}
</div>
