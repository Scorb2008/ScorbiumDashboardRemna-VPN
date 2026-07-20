<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDate, formatDateTime, formatPrice, esc } from '../lib/utils.js';
  import Table from '../components/Table.svelte';
  import Modal from '../components/Modal.svelte';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';

  let users = $state([]);
  let loading = $state(true);
  let search = $state('');
  let offset = $state(0);
  let limit = $state(50);
  let total = $state(0);

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

  let massActionsOpen = $state(false);
  let selectedUsers = $state(new Set());
  let plans = $state([]);
  let plansLoading = $state(false);
  let bulkBalanceValue = $state('');
  let giveKeyPlanId = $state('');
  let giveKeyDays = $state('30');
  let bulkSaving = $state(false);

  async function loadUsers() {
    loading = true;
    try {
      const res = await api.getUsers({ limit, offset });
      users = res.items || [];
      total = res.total || 0;
    }
    catch (e) { toasts.error('Ошибка загрузки: ' + e.message); }
    finally { loading = false; }
  }

  async function loadPlans() {
    plansLoading = true;
    try { plans = await api.getPlans({}); }
    catch (e) { toasts.error('Ошибка загрузки тарифов'); }
    finally { plansLoading = false; }
  }

  onMount(() => {
    loadUsers();
    loadPlans();
  });

  let filteredUsers = $derived(
    search
      ? users.filter(u =>
          (u.username || '').toLowerCase().includes(search.toLowerCase()) ||
          (u.full_name || '').toLowerCase().includes(search.toLowerCase()) ||
          String(u.id).includes(search))
      : users
  );

  let allSelected = $derived(
    filteredUsers.length > 0 && selectedUsers.size === filteredUsers.length
  );
  let someSelected = $derived(
    filteredUsers.length > 0 && selectedUsers.size > 0 && !allSelected
  );

  function toggleSelectAll() {
    if (allSelected) {
      selectedUsers = new Set();
    } else {
      selectedUsers = new Set(filteredUsers.map(u => u.id));
    }
  }

  function toggleUser(id) {
    const next = new Set(selectedUsers);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    selectedUsers = next;
  }

  function clearSelection() {
    selectedUsers = new Set();
  }

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
        { icon: 'keyRound', text: 'Последняя активность', date: formatDateTime(userDetail.last_seen) },
      ];
    }
    catch (e) { toasts.error('Ошибка загрузки деталей'); }
    finally { detailLoading = false; }
  }

  let confirmBan = $state(false);
  let confirmBulkBan = $state(false);
  let confirmBulkBalance = $state(false);

  async function loadKeys() {
    if (!selectedUser) return;
    keysLoading = true;
    try { userKeys = await api.getUserKeys(selectedUser.id); }
    catch (e) { toasts.error('Ошибка загрузки ключей'); }
    finally { keysLoading = false; }
  }

  async function loadPayments() {
    if (!selectedUser) return;
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
      confirmBan = false;
      await loadUsers();
    } catch (e) { toasts.error(e.message); }
  }

  async function handleBulkBalance() {
    const ids = Array.from(selectedUsers);
    if (ids.length === 0) return toasts.warning('Выберите пользователей');
    const val = parseFloat(bulkBalanceValue);
    if (isNaN(val)) return toasts.error('Введите число');
    bulkSaving = true;
    confirmBulkBalance = false;
    try {
      await api.bulkAction(ids, 'set_balance', bulkBalanceValue);
      toasts.success(`Баланс установлен для ${ids.length} пользователей`);
      clearSelection();
      await loadUsers();
    } catch (e) { toasts.error(e.message); }
    finally { bulkSaving = false; }
  }

  async function handleBulkBan() {
    const ids = Array.from(selectedUsers);
    if (ids.length === 0) return;
    bulkSaving = true;
    confirmBulkBan = false;
    try {
      await api.bulkAction(ids, 'ban');
      toasts.success(`Забанено ${ids.length} пользователей`);
      clearSelection();
      await loadUsers();
    } catch (e) { toasts.error(e.message); }
    finally { bulkSaving = false; }
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
    { key: 'username', label: 'Username', sortable: true, render: (r) => `<span class="font-mono text-xs text-zinc-400">@${esc(r.username) || '—'}</span>` },
    { key: 'full_name', label: 'Имя', sortable: true },
    { key: 'balance', label: 'Баланс', sortable: true, render: (r) => `<span class="text-xs font-medium">${formatPrice(r.balance ?? 0)}</span>` },
    { key: 'created_at', label: 'Создан', sortable: true, render: (r) => `<span class="text-xs text-muted">${formatDate(r.created_at)}</span>` },
  ];

  function statusColor(val) {
    if (val === 'active' || val === 'Активен') return 'badge-success';
    if (val === 'banned' || val === 'Забанен' || val === 'expired') return 'badge-danger';
    return 'badge-warning';
  }

  async function handleBulkAction(action, value = '') {
    const ids = Array.from(selectedUsers);
    if (ids.length === 0) return toasts.warning('Выберите пользователей');
    bulkSaving = true;
    try {
      await api.bulkAction(ids, action, value);
      toasts.success(`Действие "${action}" выполнено для ${ids.length} пользователей`);
      clearSelection();
      await loadUsers();
    } catch (e) { toasts.error(e.message); }
    finally { bulkSaving = false; }
  }

  async function handleBulkGiveKey() {
    const ids = Array.from(selectedUsers);
    if (ids.length === 0) return toasts.warning('Выберите пользователей');
    if (!giveKeyPlanId) return toasts.warning('Выберите тариф');
    const days = parseInt(giveKeyDays) || 30;
    bulkSaving = true;
    let success = 0;
    let failed = 0;
    for (const userId of ids) {
      try {
        await api.giveKey(userId, giveKeyPlanId, days);
        success++;
      } catch (e) {
        failed++;
      }
    }
    if (success > 0) toasts.success(`Ключи выданы ${success} пользователям`);
    if (failed > 0) toasts.error(`Ошибка у ${failed} пользователей`);
    clearSelection();
    bulkSaving = false;
    if (success > 0) await loadUsers();
  }

  function toggleMassActions() {
    massActionsOpen = !massActionsOpen;
    if (!massActionsOpen) clearSelection();
  }
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">Пользователи</h1>
      <p class="text-sm text-muted mt-1">{filteredUsers.length} из {users.length}</p>
    </div>
    <div class="flex gap-3 w-full sm:w-auto">
      <button onclick={toggleMassActions} class="btn btn-sm {massActionsOpen ? 'btn-primary' : 'btn-secondary'}">
        <Icon name="checkCircle" size={16} class={massActionsOpen ? 'text-white' : 'text-muted'} />
        Массовые действия
        {#if massActionsOpen}
          <Icon name="chevronUp" size={14} />
        {:else}
          <Icon name="chevronDown" size={14} />
        {/if}
      </button>
      <a href="/api/v1/database/export/users" class="btn btn-sm btn-secondary" target="_blank">
        <Icon name="download" size={16} />
        CSV
      </a>
      <input type="text" bind:value={search} placeholder="Поиск по ID, username, имени..." class="input w-full sm:w-80" />
    </div>
  </div>

  {#if massActionsOpen}
    <!-- Mass Actions Panel -->
    <div class="card overflow-hidden">
      <div class="p-4 border-b border-surface-4/30 flex items-center justify-between bg-surface-3/30">
        <div class="flex items-center gap-3">
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={allSelected}
              indeterminate={someSelected}
              onchange={toggleSelectAll}
              class="w-4 h-4 rounded border-surface-4 bg-surface-3 accent-accent"
            />
            <span class="text-[13px] font-medium">Выбрать всех</span>
          </label>
          <span class="text-xs text-muted">Выбрано: {selectedUsers.size}</span>
        </div>
        {#if selectedUsers.size > 0}
          <button onclick={clearSelection} class="btn btn-ghost btn-xs text-muted">Очистить</button>
        {/if}
      </div>

      {#if filteredUsers.length === 0}
        <div class="px-5 py-16 text-center text-sm text-muted">Пользователи не найдены</div>
      {:else}
        <div class="divide-y divide-surface-4/20 max-h-[500px] overflow-y-auto">
          {#each filteredUsers as user (user.id)}
            <div
              class="flex items-center gap-3 px-5 py-3 transition-colors hover:bg-surface-3/40 cursor-pointer"
              onclick={() => toggleUser(user.id)}>
              <input
                type="checkbox"
                checked={selectedUsers.has(user.id)}
                onchange={() => toggleUser(user.id)}
                onclick={(e) => e.stopPropagation()}
                class="w-4 h-4 rounded border-surface-4 bg-surface-3 accent-accent shrink-0"
              />
              <div class="w-8 h-8 rounded-[10px] bg-gradient-to-br from-accent to-accent/60 flex items-center justify-center text-sm font-bold text-white shrink-0">
                {(user.full_name || user.username || '?')[0].toUpperCase()}
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="text-[13px] font-medium">{user.full_name || 'Без имени'}</span>
                  <span class="text-[11px] font-mono text-zinc-500">#{user.id}</span>
                  {#if user.username}
                    <span class="text-[11px] text-zinc-400">@{user.username}</span>
                  {/if}
                </div>
                <div class="flex items-center gap-3 mt-0.5">
                  <span class="text-xs font-medium">{formatPrice(user.balance ?? 0)}</span>
                  <span class="text-[10px] text-muted">{formatDate(user.created_at)}</span>
                </div>
              </div>
              <span class="badge {user.is_banned ? 'badge-danger' : 'badge-success'} text-[10px]">
                {user.is_banned ? 'Забанен' : 'Активен'}
              </span>
            </div>
          {/each}
        </div>
      {/if}

      <!-- Bulk Action Controls -->
      <div class="p-4 border-t border-surface-4/30 bg-surface-3/20">
        <div class="flex flex-col sm:flex-row gap-3 items-start sm:items-end">
          <!-- Balance -->
          <div class="flex items-center gap-2">
            <input
              type="number"
              step="0.01"
              bind:value={bulkBalanceValue}
              placeholder="Сумма"
              class="input w-28"
            />
            <button
              onclick={() => confirmBulkBalance = true}
              disabled={bulkSaving || !bulkBalanceValue || selectedUsers.size === 0}
              class="btn btn-primary btn-sm whitespace-nowrap">
              <Icon name="wallet" size={14} />
              Установить баланс
            </button>
          </div>

          <div class="flex items-center gap-2 flex-wrap">
            <!-- Ban -->
            <button
              onclick={() => confirmBulkBan = true}
              disabled={bulkSaving || selectedUsers.size === 0}
              class="btn btn-danger btn-sm">
              <Icon name="userX" size={14} />
              Забанить
            </button>

            <!-- Unban -->
            <button
              onclick={() => handleBulkAction('unban')}
              disabled={bulkSaving || selectedUsers.size === 0}
              class="btn btn-sm"
              class:btn-secondary={true}>
              <Icon name="userCheck" size={14} />
              Разбанить
            </button>

            <!-- Give Key -->
            <div class="flex items-center gap-2">
              <select bind:value={giveKeyPlanId} class="select w-36 text-xs" disabled={plansLoading}>
                <option value="">Тариф...</option>
                {#each plans as plan}
                  <option value={plan.id}>{plan.name}</option>
                {/each}
              </select>
              <input
                type="number"
                bind:value={giveKeyDays}
                placeholder="Дни"
                class="input w-16"
                min="1"
              />
              <button
                onclick={handleBulkGiveKey}
                disabled={bulkSaving || selectedUsers.size === 0 || !giveKeyPlanId}
                class="btn btn-success btn-sm">
                <Icon name="keyRound" size={14} />
                {bulkSaving ? '...' : 'Выдать ключ'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}

  {#if massActionsOpen}
    <!-- Count when mass actions is open (no table shown) -->
    <p class="text-xs text-muted text-center">Таблица скрыта в режиме массовых действий</p>
  {:else}
    <Table columns={columns} data={filteredUsers} onRowClick={openDetail}>
      {#snippet actions(row)}
        <span class="badge {row.is_banned ? 'badge-danger' : 'badge-success'}">
          {row.is_banned ? 'Забанен' : 'Активен'}
        </span>
      {/snippet}
    </Table>
    {#if total > limit}
      <div class="flex items-center justify-between text-sm text-muted px-1">
        <span>Показано {offset + 1}–{Math.min(offset + limit, total)} из {total}</span>
        <div class="flex gap-2">
          <button class="btn btn-secondary text-xs" onclick={() => { offset = Math.max(0, offset - limit); loadUsers(); }} disabled={offset === 0}>← Назад</button>
          <button class="btn btn-secondary text-xs" onclick={() => { if (offset + limit < total) { offset += limit; loadUsers(); } }} disabled={offset + limit >= total}>Далее →</button>
        </div>
      </div>
    {/if}
  {/if}
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
          {tab === 'overview' ? 'Обзор' : tab === 'keys' ? 'Подписки' : tab === 'payments' ? 'Платежи' : 'Сообщение'}
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
            <p class="text-[11px] text-muted mt-0.5">Подписок</p>
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
            ['Последняя активность', formatDateTime(userDetail.last_seen)],
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
          <button onclick={() => userDetail.is_banned ? handleBan() : (confirmBan = true)} class="btn {userDetail.is_banned ? 'btn-primary' : 'btn-danger'} btn-sm flex-1">
            {userDetail.is_banned ? 'Разбанить' : 'Забанить'}
          </button>
        </div>
      </div>

    <!-- Tab: VPN Keys -->
    {:else if profileTab === 'keys'}
      {#if keysLoading}
        <div class="flex justify-center py-8"><div class="w-6 h-6 border-2 border-surface-4 border-t-accent rounded-full animate-spin"></div></div>
      {:else if userKeys.length === 0}
        <div class="text-center py-8 text-muted text-sm">Нет подписок</div>
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

<ConfirmDialog bind:show={confirmBan} title="Забанить пользователя?" message="Пользователь потеряет доступ к боту и получит уведомление." confirmText="Забанить" onConfirm={handleBan} />

<ConfirmDialog bind:show={confirmBulkBan} title="Забанить пользователей?" message="Выбранные пользователи потеряют доступ к боту." confirmText="Забанить" onConfirm={handleBulkBan} />

<ConfirmDialog bind:show={confirmBulkBalance} title="Установить баланс?" message="Баланс будет установлен для всех выбранных пользователей." confirmText="Применить" danger={false} onConfirm={handleBulkBalance} />
