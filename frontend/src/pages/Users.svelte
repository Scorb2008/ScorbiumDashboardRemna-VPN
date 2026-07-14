<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.js';
  import { toasts } from '../lib/stores.js';
  import Table from '../components/Table.svelte';
  import Modal from '../components/Modal.svelte';
  import Spinner from '../components/Spinner.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';

  let users = $state([]);
  let loading = $state(true);
  let search = $state('');
  let showUserModal = $state(false);
  let selectedUser = $state(null);
  let showConfirm = $state(false);
  let confirmAction = $state(null);

  const columns = [
    { key: 'id', label: 'ID', sortable: true },
    { key: 'telegram_id', label: 'Telegram', sortable: true },
    { key: 'username', label: 'Username', sortable: true },
    { key: 'full_name', label: 'Имя', sortable: true },
    { key: 'is_banned', label: 'Статус', sortable: false },
    { key: 'created_at', label: 'Создан', sortable: true },
  ];

  onMount(loadUsers);

  async function loadUsers() {
    loading = true;
    try {
      users = await api.getUsers({ limit: 200 });
    } catch (e) {
      toasts.error('Ошибка загрузки: ' + e.message);
    } finally {
      loading = false;
    }
  }

  async function openUser(user) {
    try {
      selectedUser = await api.getUser(user.id);
      showUserModal = true;
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    }
  }

  async function toggleBan(user) {
    try {
      if (user.is_banned) {
        await api.unbanUser(user.id);
        toasts.success('Пользователь разбанен');
      } else {
        await api.banUser(user.id);
        toasts.success('Пользователь забанен');
      }
      await loadUsers();
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    }
  }

  $effect(() => {
    search;
    loadUsers();
  });

  let filteredUsers = $derived(
    search
      ? users.filter((u) =>
          (u.username || '').toLowerCase().includes(search.toLowerCase()) ||
          String(u.telegram_id).includes(search) ||
          (u.full_name || '').toLowerCase().includes(search.toLowerCase())
        )
      : users
  );
</script>

<div class="fade-in">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">Пользователи</h1>
    <div class="flex gap-2">
      <input
        type="text"
        bind:value={search}
        placeholder="Поиск..."
        class="input input-bordered input-sm w-64" />
    </div>
  </div>

  <Spinner {loading} />

  <Table {columns} data={filteredUsers}>
    {#snippet actions(row)}
      <div class="flex gap-1">
        <span class="badge badge-sm" class:badge-error={row.is_banned} class:badge-success={!row.is_banned}>
          {row.is_banned ? 'Забанен' : 'Активен'}
        </span>
      </div>
    {/snippet}
  </Table>
</div>

<Modal bind:open={showUserModal} title="Пользователь #{selectedUser?.id}" size="lg">
  {#if selectedUser}
    <div class="space-y-3">
      <div class="flex justify-between">
        <span class="text-base-content/50">Telegram ID:</span>
        <span>{selectedUser.telegram_id}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-base-content/50">Username:</span>
        <span>@{selectedUser.username || '—'}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-base-content/50">Имя:</span>
        <span>{selectedUser.full_name || '—'}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-base-content/50">Баланс:</span>
        <span>{selectedUser.balance || 0} ₽</span>
      </div>
      <div class="flex justify-between">
        <span class="text-base-content/50">VPN ключей:</span>
        <span>{selectedUser.vpn_keys_count || 0}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-base-content/50">Платежей:</span>
        <span>{selectedUser.payments_count || 0}</span>
      </div>
      <div class="flex justify-between">
        <span class="text-base-content/50">Создан:</span>
        <span>{selectedUser.created_at}</span>
      </div>
      <div class="divider"></div>
      <div class="flex gap-2">
        <button
          class="btn btn-sm {selectedUser.is_banned ? 'btn-success' : 'btn-error'}"
          onclick={() => { toggleBan(selectedUser); showUserModal = false; }}>
          {selectedUser.is_banned ? 'Разбанить' : 'Забанить'}
        </button>
      </div>
    </div>
  {/if}
</Modal>

<ConfirmDialog bind:show={showConfirm} onConfirm={confirmAction} title="Подтвердить" message="Вы уверены?" />
