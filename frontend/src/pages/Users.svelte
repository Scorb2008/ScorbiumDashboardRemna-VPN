<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDate, formatDateTime, formatPrice } from '../lib/utils.js';
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

  let profileTab = $state('overview');
  let userKeys = $state([]);
  let userPayments = $state([]);
  let keysLoading = $state(false);
  let paymentsLoading = $state(false);

  let balanceEdit = $state('');
  let balanceEditing = $state(false);
  let balanceSaving = $state(false);

  let msgText = $state('');
  let msgSending = $state(false);

  let activityFeed = $state([
    { icon: 'user', text: 'Регистрация', date: null },
    { icon: 'keyRound', text: 'Последнее действие', date: null },
  ]);

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
    profileTab = 'overview';
    detailLoading = true;
    userKeys = [];
    userPayments = [];
    try {
      userDetail = await api.getUser(user.id);
      activityFeed = [
        { icon: 'user', text: 'Регистрация', date: formatDateTime(userDetail.created_at) },
        { icon: 'keyRound', text: 'Последний вход', date: formatDateTime(userDetail.last_seen) },
      ];
    }
    catch (e) { toasts.error('Ошибка загрузки деталей'); }
    finally { detailLoading = false; }
  }

  async function loadKeys() {
    if (userKeys.length > 0 || !selectedUser) return;
    keysLoading = true;
    try { userKeys = await api.getUserKeys(selectedUser.id); }
    catch (e) { toasts.error('Ошибка загрузки ключей'); }
    finally { keysLoading = false; }
  }

  async function loadPayments() {
    if (userPayments.length > 0 || !selectedUser) return;
    paymentsLoading = true;
    try { userPayments = await api.getUserPayments(selectedUser.id); }
    catch (e) { toasts.error('Ошибка загрузки платежей'); }
    finally { paymentsLoading = false; }
  }

  function onTabChange(tab) {
    profileTab = tab;
    if (tab === 'keys') loadKeys();
    if (tab === 'payments') loadPayments();
  }

  async function handleBan() {
    if (!selectedUser) return;
    try {
      if (selectedUser.is_banned) { await api.unbanUser(selectedUser.id); toasts.success('Пользователь разбанен'); }
      else { await api.banUser(selectedUser.id); toasts.success('Пользователь забанен'); }
      selectedUser.is_banned = !selectedUser.is_banned;
      userDetail.is_banned = selectedUser.is_banned;
      await loadUsers();
    } catch (e) { toasts.error(e.message); }
  }

  async function saveBalance() {
    const val = parseFloat(balanceEdit);
    if (isNaN(val)) return toasts.error('Введите число');
    balanceSaving = true;
    try {
      await api.updateUser(selectedUser.id, { balance: val });
      selectedUser.balance = val;
      userDetail.balance = val;
      toasts.success('Баланс обновлён');
      balanceEditing = false;
    } catch (e) { toasts.error(e.message); }
    finally { balanceSaving = false; }
  }

  async function handleSendMsg() {
    if (!msgText.trim() || !selectedUser) return;
    msgSending = true;
    try {
      await api.sendMessage(selectedUser.id, msgText.trim());
      toasts.success('Сообщение отправлено');
      msgText = '';
    } catch (e) { toasts.error(e.message); }
    finally { msgSending = false; }
  }

  const columns = [
    { key: 'id', label: 'ID', sortable: true },
    { key: 'username', label: 'Username', sortable: true, render: (r) => `<span class="font-mono text-xs text-zinc-400">@${r.username || '—'}</span>` },
    { key: 'full_name', label: 'Имя', sortable: true },
    { key: 'balance', label: 'Баланс', sortable: true, render: (r) => `<span class="text-xs font-medium">${formatPrice(r.balance ?? 0)}</span>` },
    { key: 'created_at', label: 'Создан', sortable: true, render: (r) => `<span class="text-xs text-muted">${formatDate(r.created_at)}</span>` },
  ];

  function statusColor(val) {
    if (val === 'active' || val === 'Активен') return 'badge-success';
    if (val === 'banned' || val === 'Забанен' || val === 'expired') return 'badge-danger';
    return 'badge-warning';
  }
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

<Modal bind:open={showModal} title="Профиль пользователя" size="xl">
  {#if detailLoading}
    <div class="flex justify-center py-12"><div class="w-8 h-8 border-2 border-surface-4 border-t-accent rounded-full animate-spin"></div></div>
  {:else if userDetail}
    <!-- Profile Header -->
    <div class="flex items-center gap-5 mb-6 p-4 bg-surface-3/50 rounded-[12px] border border-surface-4/30">
      <div class="w-14 h-14 rounded-[14px] bg-gradient-to-br from-accent to-accent/60 flex items-center justify-center text-xl font-bold text-white shadow-lg shrink-0">
        {(userDetail.full_name || userDetail.username || '?')[0].toUpperCase()}
      </div>
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2 flex-wrap">
          <h3 class="text-[17px] font-semibold">{userDetail.full_name || 'Без имени'}</h3>
          <span class="badge {userDetail.is_banned ? 'badge-danger' : 'badge-success'} text-[10px] px-2 py-0.5">
            {userDetail.is_banned ? 'Забанен' : 'Активен'}
          </span>
        </div>
        <p class="text-sm text-muted mt-0.5">
          {userDetail.username ? `@${userDetail.username}` : 'Нет username'}
          <span class="mx-1.5">&middot;</span>
          ID: {userDetail.id}
          <span class="mx-1.5">&middot;</span>
          {userDetail.language || '—'}
        </p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 border-b border-surface-4/30 mb-5 overflow-x-auto">
      {#each ['overview', 'keys', 'payments', 'message'] as tab}
        <button
          onclick={() => onTabChange(tab)}
          class="px-4 py-2.5 text-[13px] font-medium whitespace-nowrap border-b-2 transition-colors
            {profileTab === tab
              ? 'border-accent text-accent'
              : 'border-transparent text-muted hover:text-white hover:border-surface-4'}">
          {tab === 'overview' ? 'Обзор' : tab === 'keys' ? 'VPN Ключи' : tab === 'payments' ? 'Платежи' : 'Сообщение'}
        </button>
      {/each}
    </div>

    <!-- Tab: Overview -->
    {#if profileTab === 'overview'}
      <div class="space-y-5">
        <!-- Stats Grid -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div class="bg-surface-3 rounded-[10px] p-4 text-center border border-surface-4/20">
            <Icon name="wallet" class="w-5 h-5 text-accent mx-auto mb-2" />
            <p class="text-xl font-bold">{formatPrice(userDetail.balance ?? 0)}</p>
            <p class="text-[11px] text-muted mt-0.5">Баланс</p>
          </div>
          <div class="bg-surface-3 rounded-[10px] p-4 text-center border border-surface-4/20">
            <Icon name="keyRound" class="w-5 h-5 text-success mx-auto mb-2" />
            <p class="text-xl font-bold">{userDetail.vpn_keys_count ?? 0}</p>
            <p class="text-[11px] text-muted mt-0.5">VPN Ключей</p>
          </div>
          <div class="bg-surface-3 rounded-[10px] p-4 text-center border border-surface-4/20">
            <Icon name="creditCard" class="w-5 h-5 text-warning mx-auto mb-2" />
            <p class="text-xl font-bold">{userDetail.payments_count ?? 0}</p>
            <p class="text-[11px] text-muted mt-0.5">Платежей</p>
          </div>
          <div class="bg-surface-3 rounded-[10px] p-4 text-center border border-surface-4/20">
            <Icon name="refreshCw" class="w-5 h-5 text-muted mx-auto mb-2" />
            <p class="text-xl font-bold">{userDetail.autorenew ? 'Да' : 'Нет'}</p>
            <p class="text-[11px] text-muted mt-0.5">Автопродление</p>
          </div>
        </div>

        <!-- Details -->
        <div class="bg-surface-3/50 rounded-[10px] border border-surface-4/20 divide-y divide-surface-4/20">
          {#each [
            ['ID', String(userDetail.id)],
            ['Username', userDetail.username ? `@${userDetail.username}` : '—'],
            ['Имя', userDetail.full_name || '—'],
            ['Язык', userDetail.language || '—'],
            ['Реферальный код', userDetail.referral_code || '—'],
            ['Создан', formatDateTime(userDetail.created_at)],
            ['Последний вход', formatDateTime(userDetail.last_seen)],
          ] as [label, val]}
            <div class="flex justify-between items-center px-4 py-2.5">
              <span class="text-[13px] text-muted">{label}</span>
              <span class="text-[13px] font-medium">{val}</span>
            </div>
          {/each}
        </div>

        <!-- Activity Feed -->
        <div class="bg-surface-3/50 rounded-[10px] border border-surface-4/20 p-4">
          <h4 class="text-[13px] font-semibold mb-3 text-muted">Активность</h4>
          <div class="space-y-3">
            {#each activityFeed as act}
              <div class="flex items-center gap-3">
                <div class="w-7 h-7 rounded-[8px] bg-surface-3 border border-surface-4 flex items-center justify-center shrink-0">
                  <Icon name={act.icon} class="w-3.5 h-3.5 text-muted" />
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-[13px]">{act.text}</p>
                  {#if act.date}
                    <p class="text-[11px] text-muted">{act.date}</p>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        </div>

        <!-- Balance Edit & Ban Actions -->
        <div class="flex flex-col sm:flex-row gap-3">
          {#if balanceEditing}
            <div class="flex items-center gap-2 flex-1">
              <input type="number" step="0.01" bind:value={balanceEdit} class="input flex-1" placeholder="Новый баланс" />
              <button onclick={saveBalance} disabled={balanceSaving} class="btn btn-primary btn-sm">
                {balanceSaving ? '...' : 'Сохранить'}
              </button>
              <button onclick={() => { balanceEditing = false; }} class="btn btn-ghost btn-sm">Отмена</button>
            </div>
          {:else}
            <button onclick={() => { balanceEdit = String(userDetail.balance ?? ''); balanceEditing = true; }} class="btn btn-primary btn-sm flex-1">
              <Icon name="wallet" class="w-3.5 h-3.5" /> Редактировать баланс
            </button>
          {/if}
          <button onclick={handleBan} class="btn {userDetail.is_banned ? 'btn-primary' : 'btn-danger'} btn-sm flex-1">
            {userDetail.is_banned ? 'Разбанить' : 'Забанить'}
          </button>
        </div>
      </div>

    <!-- Tab: VPN Keys -->
    {:else if profileTab === 'keys'}
      {#if keysLoading}
        <div class="flex justify-center py-8"><div class="w-6 h-6 border-2 border-surface-4 border-t-accent rounded-full animate-spin"></div></div>
      {:else if userKeys.length === 0}
        <div class="text-center py-8 text-muted text-sm">Нет VPN ключей</div>
      {:else}
        <div class="space-y-2">
          {#each userKeys as key}
            <div class="flex items-center gap-3 p-3 bg-surface-3/50 rounded-[10px] border border-surface-4/20">
              <div class="w-8 h-8 rounded-[8px] bg-surface-3 border border-surface-4 flex items-center justify-center shrink-0">
                <Icon name="keyRound" class="w-4 h-4 text-accent" />
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="text-[13px] font-medium">{key.short_id || `#${key.id}`}</span>
                  <span class="badge {statusColor(key.status)} text-[10px]">{key.status || 'active'}</span>
                </div>
                {#if key.expires_at}
                  <p class="text-[11px] text-muted mt-0.5">Истекает: {formatDate(key.expires_at)}</p>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}

    <!-- Tab: Payments -->
    {:else if profileTab === 'payments'}
      {#if paymentsLoading}
        <div class="flex justify-center py-8"><div class="w-6 h-6 border-2 border-surface-4 border-t-accent rounded-full animate-spin"></div></div>
      {:else if userPayments.length === 0}
        <div class="text-center py-8 text-muted text-sm">Нет платежей</div>
      {:else}
        <div class="space-y-2">
          {#each userPayments as p}
            <div class="flex items-center gap-3 p-3 bg-surface-3/50 rounded-[10px] border border-surface-4/20">
              <div class="w-8 h-8 rounded-[8px] bg-surface-3 border border-surface-4 flex items-center justify-center shrink-0">
                <Icon name="creditCard" class="w-4 h-4 text-warning" />
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="text-[13px] font-medium">{formatPrice(p.amount)}</span>
                  <span class="badge {statusColor(p.status)} text-[10px]">{p.status || '—'}</span>
                </div>
                <p class="text-[11px] text-muted mt-0.5">{formatDateTime(p.created_at)}</p>
              </div>
            </div>
          {/each}
        </div>
      {/if}

    <!-- Tab: Message -->
    {:else if profileTab === 'message'}
      <div class="space-y-4">
        <p class="text-[13px] text-muted">Отправить сообщение пользователю через Telegram бота</p>
        <textarea bind:value={msgText} class="textarea w-full h-28" placeholder="Текст сообщения..."></textarea>
        <button onclick={handleSendMsg} disabled={msgSending || !msgText.trim()} class="btn btn-primary w-full">
          {#if msgSending}
            <div class="w-4 h-4 border-2 border-surface-4 border-t-white rounded-full animate-spin"></div>
          {:else}
            <Icon name="send" class="w-4 h-4" />
          {/if}
          Отправить
        </button>
      </div>
    {/if}
  {/if}
</Modal>
