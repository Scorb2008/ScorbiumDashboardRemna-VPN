<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDateTime, formatBytes } from '../lib/utils.js';
  import Table from '../components/Table.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';
  import Spinner from '../components/Spinner.svelte';

  let keys = $state([]);
  let loading = $state(true);
  let search = $state('');
  let confirmAction = $state(null);

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

  onMount(loadKeys);

  let filteredKeys = $derived(
    search
      ? keys.filter(k =>
          String(k.id).includes(search) ||
          String(k.user_id).includes(search) ||
          (k.name || '').toLowerCase().includes(search.toLowerCase()) ||
          (k.remnawave_key_id || '').includes(search))
      : keys
  );

  function statusBadge(status) {
    if (status === 'active') return 'badge-success';
    if (status === 'expired') return 'badge-warning';
    return 'badge-error';
  }

  function statusLabel(status) {
    if (status === 'active') return 'Активен';
    if (status === 'expired') return 'Истёк';
    return 'Отозван';
  }

  async function handleRevoke(key) {
    try {
      await api.cancelSubscription(key.id);
      toasts.success('Ключ отозван');
      await loadKeys();
    } catch (e) {
      toasts.error(e.message);
    }
    confirmAction = null;
  }

  async function handleDelete(key) {
    try {
      await api.deleteKey(key.id);
      toasts.success('Ключ удалён');
      await loadKeys();
    } catch (e) {
      toasts.error(e.message);
    }
    confirmAction = null;
  }

  async function handleSync() {
    try {
      await api.syncKeys();
      toasts.success('Синхронизация завершена');
      await loadKeys();
    } catch (e) {
      toasts.error('Ошибка синхронизации: ' + e.message);
    }
  }

  async function handleExpire() {
    try {
      const result = await api.expireOutdated();
      toasts.success(`Истекло: ${result.expired}`);
      await loadKeys();
    } catch (e) {
      toasts.error(e.message);
    }
  }

  const columns = [
    { key: 'id', label: 'ID', sortable: true },
    { key: 'user_id', label: 'User ID', sortable: true },
    { key: 'name', label: 'Имя', sortable: true },
    { key: 'status', label: 'Статус', sortable: true, render: (r) => `<span class="badge badge-sm badge-glow ${statusBadge(r.status)}">${statusLabel(r.status)}</span>` },
    { key: 'expires_at', label: 'Истекает', sortable: true, render: (r) => `<span class="text-xs text-base-content/50">${formatDateTime(r.expires_at)}</span>` },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold">VPN Ключи</h1>
      <p class="text-sm text-base-content/40 mt-1">{filteredKeys.length} ключей</p>
    </div>
    <div class="flex gap-2 flex-wrap">
      <button onclick={handleSync} class="btn btn-primary btn-sm btn-glow gap-2">
        Синхронизация
      </button>
      <button onclick={handleExpire} class="btn btn-warning btn-sm gap-2">
        Истекшие
      </button>
      <input type="text" bind:value={search} placeholder="Поиск..." class="input input-bordered input-glass w-60" />
    </div>
  </div>

  <Table columns={columns} data={filteredKeys}>
    {#snippet actions(row)}
      <div class="flex gap-1">
        {#if row.status === 'active'}
          <button class="btn btn-xs btn-warning btn-ghost" onclick={() => confirmAction = { type: 'revoke', key: row }}>Отозвать</button>
        {/if}
        <button class="btn btn-xs btn-error btn-ghost" onclick={() => confirmAction = { type: 'delete', key: row }}>Удалить</button>
      </div>
    {/snippet}
  </Table>
</div>

{#if confirmAction}
  <ConfirmDialog
    show={true}
    title={confirmAction.type === 'revoke' ? 'Отозвать ключ?' : 'Удалить ключ?'}
    message={confirmAction.type === 'revoke'
      ? `Ключ #${confirmAction.key.id} будет отозван. Пользователь потеряет доступ к VPN.`
      : `Ключ #${confirmAction.key.id} будет удалён безвозвратно из Remnawave.`}
    confirmText={confirmAction.type === 'revoke' ? 'Отозвать' : 'Удалить'}
    confirmClass={confirmAction.type === 'revoke' ? 'btn-warning' : 'btn-error'}
    onConfirm={() => confirmAction.type === 'revoke' ? handleRevoke(confirmAction.key) : handleDelete(confirmAction.key)}
    onCancel={() => confirmAction = null} />
{/if}
