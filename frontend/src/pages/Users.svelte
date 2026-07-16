<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDate, formatDateTime } from '../lib/utils.js';
  import Table from '../components/Table.svelte';
  import Modal from '../components/Modal.svelte';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';

  let users = $state([]);
  let loading = $state(true);
  let search = $state('');
  let selectedUser = $state(null);
  let showModal = $state(false);
  let userDetail = $state(null);
  let detailLoading = $state(false);

  async function loadUsers() {
    loading = true;
    try { users = await api.getUsers({ limit: 500 }); }
    catch (e) { toasts.error('Ошибка загрузки: ' + e.message); }
    finally { loading = false; }
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
    try { userDetail = await api.getUser(user.id); }
    catch (e) { toasts.error('Ошибка загрузки деталей'); }
    finally { detailLoading = false; }
  }

  async function handleBan() {
    if (!selectedUser) return;
    try {
      if (selectedUser.is_banned) { await api.unbanUser(selectedUser.id); toasts.success('Пользователь разбанен'); }
      else { await api.banUser(selectedUser.id); toasts.success('Пользователь забанен'); }
      await loadUsers(); showModal = false;
    } catch (e) { toasts.error(e.message); }
  }

  const columns = [
    { key: 'id', label: 'ID', sortable: true },
    { key: 'username', label: 'Username', sortable: true, render: (r) => `<span class="font-mono text-xs text-zinc-400">@${r.username || '—'}</span>` },
    { key: 'full_name', label: 'Имя', sortable: true },
    { key: 'created_at', label: 'Создан', sortable: true, render: (r) => `<span class="text-xs text-muted">${formatDate(r.created_at)}</span>` },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">Пользователи</h1>
      <p class="text-sm text-muted mt-1">{filteredUsers.length} из {users.length}</p>
    </div>
    <input type="text" bind:value={search} placeholder="Поиск по ID, username, имени..." class="input w-full sm:w-80" />
  </div>

  <Table columns={columns} data={filteredUsers} onRowClick={openDetail}>
    {#snippet actions(row)}
      <span class="badge {row.is_banned ? 'badge-danger' : 'badge-success'}">
        {row.is_banned ? 'Забанен' : 'Активен'}
      </span>
    {/snippet}
  </Table>
</div>

<Modal bind:open={showModal} title="Профиль пользователя" size="lg">
  {#if detailLoading}
    <div class="flex justify-center py-8"><div class="w-6 h-6 border-2 border-surface-4 border-t-accent rounded-full animate-spin"></div></div>
  {:else if userDetail}
    <div class="space-y-4">
      <div class="flex items-center gap-4">
        <div class="w-12 h-12 rounded-[12px] bg-surface-3 border border-surface-4 flex items-center justify-center text-lg font-bold">
          {(userDetail.full_name || userDetail.username || '?')[0].toUpperCase()}
        </div>
        <div>
          <h3 class="text-[15px] font-semibold">{userDetail.full_name || 'Без имени'}</h3>
          <p class="text-xs text-muted">{userDetail.username ? `@${userDetail.username}` : ''} &middot; ID: {userDetail.id}</p>
        </div>
      </div>

      <div class="border-t border-surface-4/50"></div>

      <div class="grid grid-cols-2 gap-3">
        <div class="bg-surface-3 rounded-[10px] p-4 text-center">
          <p class="text-2xl font-bold">{userDetail.vpn_keys_count ?? 0}</p>
          <p class="text-[11px] text-muted mt-1">VPN Ключей</p>
        </div>
        <div class="bg-surface-3 rounded-[10px] p-4 text-center">
          <p class="text-2xl font-bold">{userDetail.payments_count ?? 0}</p>
          <p class="text-[11px] text-muted mt-1">Платежей</p>
        </div>
      </div>

      <div class="space-y-0 text-[13px]">
        {#each [
          ['Статус', userDetail.is_banned ? 'Забанен' : 'Активен', userDetail.is_banned ? 'badge-danger' : 'badge-success'],
          ['Баланс', `${userDetail.balance ?? 0} RUB`, null],
          ['Язык', userDetail.language || '—', null],
          ['Автопродление', userDetail.autorenew ? 'Вкл' : 'Выкл', null],
          ['Создан', formatDateTime(userDetail.created_at), null],
          ['Последний вход', formatDateTime(userDetail.last_seen), null],
        ] as [label, value, badge]}
          <div class="flex justify-between py-2.5 border-b border-surface-4/30">
            <span class="text-muted">{label}</span>
            {#if badge}
              <span class="badge {badge}">{value}</span>
            {:else}
              <span>{value}</span>
            {/if}
          </div>
        {/each}
      </div>

      <div class="border-t border-surface-4/50"></div>

      <button onclick={handleBan} class="btn {selectedUser?.is_banned ? 'btn-primary' : 'btn-danger'} w-full">
        {selectedUser?.is_banned ? 'Разбанить' : 'Забанить'}
      </button>
    </div>
  {/if}
</Modal>
