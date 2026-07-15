<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDate, formatDateTime } from '../lib/utils.js';
  import Table from '../components/Table.svelte';
  import Modal from '../components/Modal.svelte';
  import Spinner from '../components/Spinner.svelte';

  let users = $state([]);
  let loading = $state(true);
  let search = $state('');
  let selectedUser = $state(null);
  let showModal = $state(false);
  let userDetail = $state(null);
  let detailLoading = $state(false);

  async function loadUsers() {
    loading = true;
    try {
      users = await api.getUsers({ limit: 500 });
    } catch (e) {
      toasts.error('Ошибка загрузки: ' + e.message);
    } finally {
      loading = false;
    }
  }

  onMount(loadUsers);

  let filteredUsers = $derived(
    search
      ? users.filter(u =>
          (u.username || '').toLowerCase().includes(search.toLowerCase()) ||
          (u.full_name || '').toLowerCase().includes(search.toLowerCase()) ||
          String(u.id).includes(search))
      : users
  );

  async function openDetail(user) {
    selectedUser = user;
    showModal = true;
    detailLoading = true;
    try {
      userDetail = await api.getUser(user.id);
    } catch (e) {
      toasts.error('Ошибка загрузки деталей');
    } finally {
      detailLoading = false;
    }
  }

  async function handleBan() {
    if (!selectedUser) return;
    try {
      if (selectedUser.is_banned) {
        await api.unbanUser(selectedUser.id);
        toasts.success('Пользователь разбанен');
      } else {
        await api.banUser(selectedUser.id);
        toasts.success('Пользователь забанен');
      }
      await loadUsers();
      showModal = false;
    } catch (e) {
      toasts.error(e.message);
    }
  }

  const columns = [
    { key: 'id', label: 'ID', sortable: true },
    { key: 'username', label: 'Username', sortable: true, render: (r) => `<span class="text-primary font-mono text-xs">@${r.username || '—'}</span>` },
    { key: 'full_name', label: 'Имя', sortable: true, render: (r) => `<span class="text-sm">${r.full_name || '—'}</span>` },
    { key: 'created_at', label: 'Создан', sortable: true, render: (r) => `<span class="text-xs text-base-content/50">${formatDate(r.created_at)}</span>` },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold">Пользователи</h1>
      <p class="text-sm text-base-content/40 mt-1">{filteredUsers.length} из {users.length}</p>
    </div>
    <input
      type="text"
      bind:value={search}
      placeholder="Поиск по ID, username, имени..."
      class="input input-bordered input-glass w-full sm:w-80" />
  </div>

  <Table columns={columns} data={filteredUsers} onRowClick={openDetail}>
    {#snippet actions(row)}
      <span class="badge badge-sm badge-glow {row.is_banned ? 'badge-error' : 'badge-success'}">
        {row.is_banned ? 'Забанен' : 'Активен'}
      </span>
    {/snippet}
  </Table>
</div>

<Modal bind:open={showModal} title="Профиль пользователя" size="lg">
  {#if detailLoading}
    <div class="flex justify-center py-8"><span class="loading loading-spinner loading-md text-primary"></span></div>
  {:else if userDetail}
    <div class="space-y-4">
      <div class="flex items-center gap-4">
        <div class="w-14 h-14 rounded-2xl gradient-primary flex items-center justify-center text-white text-xl font-bold">
          {(userDetail.full_name || userDetail.username || '?')[0].toUpperCase()}
        </div>
        <div>
          <h3 class="text-lg font-semibold">{userDetail.full_name || 'Без имени'}</h3>
          <p class="text-sm text-base-content/50">
            {#if userDetail.username}@{userDetail.username}{/if}
            <span class="mx-2">|</span>
            ID: {userDetail.id}
          </p>
        </div>
      </div>

      <div class="divider"></div>

      <div class="grid grid-cols-2 gap-3">
        <div class="glass rounded-xl p-3 text-center">
          <p class="text-2xl font-bold text-primary">{userDetail.vpn_keys_count ?? 0}</p>
          <p class="text-xs text-base-content/40">VPN Ключей</p>
        </div>
        <div class="glass rounded-xl p-3 text-center">
          <p class="text-2xl font-bold text-secondary">{userDetail.payments_count ?? 0}</p>
          <p class="text-xs text-base-content/40">Платежей</p>
        </div>
      </div>

      <div class="space-y-2 text-sm">
        <div class="flex justify-between py-1.5 border-b border-base-300/50">
          <span class="text-base-content/50">Статус</span>
          <span class="badge badge-sm {userDetail.is_banned ? 'badge-error' : 'badge-success'}">
            {userDetail.is_banned ? 'Забанен' : 'Активен'}
          </span>
        </div>
        <div class="flex justify-between py-1.5 border-b border-base-300/50">
          <span class="text-base-content/50">Баланс</span>
          <span class="font-medium">{userDetail.balance ?? 0} RUB</span>
        </div>
        <div class="flex justify-between py-1.5 border-b border-base-300/50">
          <span class="text-base-content/50">Язык</span>
          <span>{userDetail.language || '—'}</span>
        </div>
        <div class="flex justify-between py-1.5 border-b border-base-300/50">
          <span class="text-base-content/50">Автопродление</span>
          <span>{userDetail.autorenew ? 'Вкл' : 'Выкл'}</span>
        </div>
        <div class="flex justify-between py-1.5 border-b border-base-300/50">
          <span class="text-base-content/50">Создан</span>
          <span>{formatDateTime(userDetail.created_at)}</span>
        </div>
        <div class="flex justify-between py-1.5">
          <span class="text-base-content/50">Последний вход</span>
          <span>{formatDateTime(userDetail.last_seen)}</span>
        </div>
      </div>

      <div class="divider"></div>

      <button onclick={handleBan} class="btn w-full {selectedUser?.is_banned ? 'btn-success' : 'btn-error'}">
        {selectedUser?.is_banned ? 'Разбанить' : 'Забанить'}
      </button>
    </div>
  {/if}
</Modal>
