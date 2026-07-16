<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDate } from '../lib/utils.js';
  import Table from '../components/Table.svelte';
  import Spinner from '../components/Spinner.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';
  import Icon from '../components/Icon.svelte';

  let keys = $state([]);
  let loading = $state(true);
  let search = $state('');
  let confirmDelete = $state(false);
  let deleteTarget = $state(null);
  let confirmRevoke = $state(false);
  let revokeTarget = $state(null);

  async function loadKeys() {
    loading = true;
    try { keys = await api.getVpnKeys({ limit: 1000 }); }
    catch (e) { toasts.error('Ошибка загрузки ключей: ' + e.message); }
    finally { loading = false; }
  }

  onMount(loadKeys);

  let filteredKeys = $derived(
    search
      ? keys.filter(k =>
          (k.user_username || '').toLowerCase().includes(search.toLowerCase()) ||
          (k.user_full_name || '').toLowerCase().includes(search.toLowerCase()) ||
          String(k.user_id).includes(search) ||
          String(k.id).includes(search))
      : keys
  );

  function askDelete(key) { deleteTarget = key; confirmDelete = true; }
  function askRevoke(key) { revokeTarget = key; confirmRevoke = true; }

  async function doDelete() {
    if (!deleteTarget) return;
    try { await api.deleteVpnKey(deleteTarget.id); toasts.success('Ключ удалён'); await loadKeys(); }
    catch (e) { toasts.error(e.message); }
    confirmDelete = false; deleteTarget = null;
  }

  async function doRevoke() {
    if (!revokeTarget) return;
    try { await api.revokeVpnKey(revokeTarget.id); toasts.success('Ключ отозван'); await loadKeys(); }
    catch (e) { toasts.error(e.message); }
    confirmRevoke = false; revokeTarget = null;
  }

  function statusBadge(key) {
    if (key.is_active === false) return 'badge-danger';
    if (key.expire_at && new Date(key.expire_at) < new Date()) return 'badge-danger';
    return 'badge-success';
  }
  function statusText(key) {
    if (key.is_active === false) return 'Неактивен';
    if (key.expire_at && new Date(key.expire_at) < new Date()) return 'Истёк';
    return 'Активен';
  }

  const columns = [
    { key: 'id', label: 'ID', sortable: true },
    { key: 'user_id', label: 'Пользователь', sortable: true, render: (r) => `<div><span class="font-medium">${r.user_full_name || '—'}</span><br><span class="text-xs text-muted">${r.user_username ? '@'+r.user_username : 'ID: '+r.user_id}</span></div>` },
    { key: 'traffic_used', label: 'Трафик', sortable: true, render: (r) => `<span class="font-mono text-xs">${r.traffic_used ? (r.traffic_used / 1024 / 1024 / 1024).toFixed(2)+' ГБ' : '0'}</span>` },
    { key: 'expire_at', label: 'Истекает', sortable: true, render: (r) => r.expire_at ? `<span class="text-xs text-muted">${formatDate(r.expire_at)}</span>` : '<span class="text-xs text-muted">Бессрочно</span>' },
    { key: 'device_limit', label: 'Устр.', sortable: true, render: (r) => `${r.device_limit ?? '—'}` },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">VPN Ключи</h1>
      <p class="text-sm text-muted mt-1">{filteredKeys.length} ключей</p>
    </div>
    <input type="text" bind:value={search} placeholder="Поиск по имени, username, ID..." class="input w-full sm:w-80" />
  </div>

  <Table columns={columns} data={filteredKeys}>
    {#snippet actions(row)}
      <span class="badge {statusBadge(row)}">{statusText(row)}</span>
      <button class="btn btn-ghost text-accent hover:text-accent-hover" onclick={() => askRevoke(row)} title="Отозвать"><Icon name="shield-off" class="w-3.5 h-3.5" /></button>
      <button class="btn btn-ghost text-danger hover:text-danger-hover" onclick={() => askDelete(row)} title="Удалить"><Icon name="trash-2" class="w-3.5 h-3.5" /></button>
    {/snippet}
  </Table>
</div>

<ConfirmDialog bind:open={confirmDelete} title="Удалить ключ?" message={`Вы уверены, что хотите удалить ключ #${deleteTarget?.id}? Это действие необратимо.`} confirmText="Удалить" danger onConfirm={doDelete} />
<ConfirmDialog bind:open={confirmRevoke} title="Отозвать ключ?" message={`Отозвать ключ #${revokeTarget?.id}? Пользователь потеряет доступ.`} confirmText="Отозвать" danger onConfirm={doRevoke} />
