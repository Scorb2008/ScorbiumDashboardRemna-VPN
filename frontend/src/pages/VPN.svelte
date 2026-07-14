<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.js';
  import { toasts } from '../lib/stores.js';
  import Table from '../components/Table.svelte';
  import Spinner from '../components/Spinner.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';

  let keys = $state([]);
  let loading = $state(true);
  let syncing = $state(false);
  let search = $state('');
  let showConfirm = $state(false);
  let pendingAction = $state(null);
  let pendingMessage = $state('');

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'user_id', label: 'Пользователь' },
    { key: 'name', label: 'Название' },
    { key: 'remnawave_key_id', label: 'Panel ID' },
    { key: 'status', label: 'Статус' },
    { key: 'expires_at', label: 'Истекает' },
    { key: 'download', label: 'Трафик' },
  ];

  onMount(loadKeys);

  async function loadKeys() {
    loading = true;
    try {
      keys = await api.getSubscriptions({ limit: 500 });
    } catch (e) {
      toasts.error('Ошибка загрузки: ' + e.message);
    } finally {
      loading = false;
    }
  }

  async function handleSync() {
    syncing = true;
    try {
      const result = await api.syncKeys();
      toasts.success(`Синхронизация: ${result.synced} ключей, ${result.errors} ошибок`);
      await loadKeys();
    } catch (e) {
      toasts.error('Ошибка синхронизации: ' + e.message);
    } finally {
      syncing = false;
    }
  }

  function confirmRevoke(key) {
    pendingMessage = `Отозвать ключ #${key.id} для пользователя ${key.user_id}?`;
    pendingAction = () => doRevoke(key.id);
    showConfirm = true;
  }

  async function doRevoke(id) {
    try {
      await api.revokeKey(id);
      toasts.success('Ключ отозван');
      await loadKeys();
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    }
  }

  function confirmDelete(key) {
    pendingMessage = `Удалить ключ #${key.id} из Remnawave? Это необратимо.`;
    pendingAction = () => doDelete(key.id);
    showConfirm = true;
  }

  async function doDelete(id) {
    try {
      await api.deleteKey(id);
      toasts.success('Ключ удалён');
      await loadKeys();
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    }
  }

  async function handleExpireOutdated() {
    try {
      const result = await api.expireOutdated();
      toasts.success(`Истекших ключей: ${result.expired}`);
      await loadKeys();
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    }
  }

  let filteredKeys = $derived(
    search
      ? keys.filter((k) =>
          String(k.id).includes(search) ||
          String(k.user_id).includes(search) ||
          (k.name || '').toLowerCase().includes(search.toLowerCase()) ||
          (k.remnawave_key_id || '').toLowerCase().includes(search.toLowerCase())
        )
      : keys
  );

  function formatBytes(bytes) {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let i = 0;
    let val = bytes;
    while (val >= 1024 && i < units.length - 1) { val /= 1024; i++; }
    return val.toFixed(1) + ' ' + units[i];
  }

  function statusBadge(status) {
    const map = {
      active: 'badge-success',
      expired: 'badge-warning',
      revoked: 'badge-error',
    };
    return map[status] || 'badge-ghost';
  }
</script>

<div class="fade-in">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">VPN Ключи</h1>
    <div class="flex gap-2">
      <input
        type="text"
        bind:value={search}
        placeholder="Поиск..."
        class="input input-bordered input-sm w-48" />
      <button class="btn btn-sm btn-outline" onclick={handleExpireOutdated} disabled={loading}>
        Истекшие
      </button>
      <button class="btn btn-sm btn-primary" onclick={handleSync} disabled={syncing}>
        {#if syncing}
          <span class="loading loading-spinner loading-sm"></span>
        {:else}
          🔄
        {/if}
        Синхронизация
      </button>
    </div>
  </div>

  <Spinner {loading} />

  {#if !loading}
    <div class="table-container">
      <div class="overflow-x-auto">
        <table class="table table-zebra table-hover">
          <thead>
            <tr>
              {#each columns as col}
                <th>{col.label}</th>
              {/each}
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {#if filteredKeys.length === 0}
              <tr>
                <td colspan={columns.length + 1} class="text-center py-8 text-base-content/40">
                  Нет ключей
                </td>
              </tr>
            {:else}
              {#each filteredKeys as key (key.id)}
                <tr class="fade-in">
                  <td class="font-mono text-sm">#{key.id}</td>
                  <td>{key.user_id}</td>
                  <td class="max-w-[150px] truncate">{key.name || '—'}</td>
                  <td class="font-mono text-xs max-w-[120px] truncate">{key.remnawave_key_id || '—'}</td>
                  <td>
                    <span class="badge badge-sm {statusBadge(key.status)}">
                      {key.status}
                    </span>
                  </td>
                  <td class="text-sm">
                    {key.expires_at ? new Date(key.expires_at).toLocaleDateString('ru-RU') : '∞'}
                  </td>
                  <td class="text-sm">{formatBytes(key.download)}</td>
                  <td>
                    <div class="flex gap-1">
                      {#if key.status === 'active'}
                        <button
                          class="btn btn-xs btn-warning"
                          onclick={() => confirmRevoke(key)}>
                          Отозвать
                        </button>
                      {/if}
                      <button
                        class="btn btn-xs btn-error btn-outline"
                        onclick={() => confirmDelete(key)}>
                          Удалить
                        </button>
                    </div>
                  </td>
                </tr>
              {/each}
            {/if}
          </tbody>
        </table>
      </div>
    </div>
  {/if}
</div>

<ConfirmDialog bind:show={showConfirm} onConfirm={pendingAction} title="Подтвердить" message={pendingMessage} />
