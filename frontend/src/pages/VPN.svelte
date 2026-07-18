<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDate, formatPrice, esc } from '../lib/utils.js';
  import Table from '../components/Table.svelte';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';
  import Modal from '../components/Modal.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';

  let subscriptions = $state([]);
  let loading = $state(true);
  let search = $state('');

  let showGiveModal = $state(false);
  let plans = $state([]);
  let users = $state([]);
  let plansLoading = $state(false);
  let usersLoading = $state(false);
  let giveUserId = $state('');
  let givePlanId = $state('');
  let giveDays = $state(30);
  let userSearch = $state('');

  let confirmDelete = $state(false);
  let deleteTarget = $state(null);

  async function loadSubscriptions() {
    loading = true;
    try { subscriptions = await api.getSubscriptions({ limit: 500 }); }
    catch (e) { toasts.error('Ошибка загрузки подписок: ' + e.message); }
    finally { loading = false; }
  }

  async function loadPlans() {
    plansLoading = true;
    try { plans = await api.getPlans({}); }
    catch (e) { toasts.error('Ошибка загрузки тарифов'); }
    finally { plansLoading = false; }
  }

  async function loadUsers() {
    usersLoading = true;
    try { users = await api.getUsers({ limit: 500 }); }
    catch (e) { toasts.error('Ошибка загрузки пользователей'); }
    finally { usersLoading = false; }
  }

  onMount(() => {
    loadSubscriptions();
    loadPlans();
    loadUsers();
  });

  let filteredSubscriptions = $derived(
    search
      ? subscriptions.filter(s =>
          (s.user_username || '').toLowerCase().includes(search.toLowerCase()) ||
          (s.user_full_name || '').toLowerCase().includes(search.toLowerCase()) ||
          String(s.user_id).includes(search) ||
          String(s.id).includes(search))
      : subscriptions
  );

  let filteredUsers = $derived(
    userSearch
      ? users.filter(u =>
          (u.username || '').toLowerCase().includes(userSearch.toLowerCase()) ||
          (u.full_name || '').toLowerCase().includes(userSearch.toLowerCase()) ||
          String(u.id).includes(userSearch))
      : users
  );

  function openGiveModal() {
    giveUserId = '';
    givePlanId = '';
    giveDays = 30;
    userSearch = '';
    showGiveModal = true;
  }

  function handlePlanChange() {
    if (!givePlanId) return;
    const plan = plans.find(p => p.id == givePlanId);
    if (plan && plan.duration_days) {
      giveDays = plan.duration_days;
    }
  }

  async function handleGive() {
    const userId = giveUserId ? parseInt(giveUserId) : null;
    if (!userId) return toasts.warning('Выберите пользователя');
    if (!giveDays || giveDays < 1) return toasts.warning('Укажите количество дней');
    try {
      await api.giveSubscription(userId, givePlanId ? parseInt(givePlanId) : 0, parseInt(giveDays));
      toasts.success('Подписка выдана');
      showGiveModal = false;
      await loadSubscriptions();
    } catch (e) { toasts.error(e.message); }
  }

  async function handleActivate(id) {
    try {
      await api.activateSubscription(id);
      toasts.success('Подписка активирована');
      await loadSubscriptions();
    } catch (e) { toasts.error(e.message); }
  }

  async function handleDeactivate(id) {
    try {
      await api.deactivateSubscription(id);
      toasts.success('Подписка деактивирована');
      await loadSubscriptions();
    } catch (e) { toasts.error(e.message); }
  }

  function askDelete(sub) {
    deleteTarget = sub;
    confirmDelete = true;
  }

  async function doDelete() {
    if (!deleteTarget) return;
    try {
      await api.deleteSubscription(deleteTarget.id);
      toasts.success('Подписка удалена');
      await loadSubscriptions();
    } catch (e) { toasts.error(e.message); }
    confirmDelete = false;
    deleteTarget = null;
  }

  function statusBadge(status) {
    switch (status) {
      case 'active': return 'badge-success';
      case 'expired': return 'badge-danger';
      case 'revoked': return 'badge-warning';
      default: return '';
    }
  }

  function statusText(status) {
    switch (status) {
      case 'active': return 'Активна';
      case 'expired': return 'Истекла';
      case 'revoked': return 'Отозвана';
      default: return status;
    }
  }

  const columns = [
    { key: 'id', label: 'ID', sortable: true, render: (r) => `<span class="font-mono text-xs text-zinc-500">#${r.id}</span>` },
    { key: 'user_id', label: 'Пользователь', sortable: true, render: (r) => `<div><span class="font-medium">${esc(r.user_full_name) || '—'}</span><br><span class="text-xs text-muted">${r.user_username ? '@'+esc(r.user_username) : 'ID: '+r.user_id}</span></div>` },
    { key: 'plan_name', label: 'Тариф', sortable: true, render: (r) => `<span class="text-xs">${esc(r.plan_name) || '—'}</span>` },
    { key: 'expires_at', label: 'Истекает', sortable: true, render: (r) => r.expires_at ? `<span class="text-xs text-muted">${formatDate(r.expires_at)}</span>` : '<span class="text-xs text-muted">—</span>' },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">Подписки</h1>
      <p class="text-sm text-muted mt-1">{filteredSubscriptions.length} из {subscriptions.length}</p>
    </div>
    <div class="flex gap-3 w-full sm:w-auto">
      <button class="btn btn-primary" onclick={openGiveModal}>
        <Icon name="plus" class="w-4 h-4" /> Выдать подписку
      </button>
      <input type="text" bind:value={search} placeholder="Поиск по имени, username, ID..." class="input w-full sm:w-60" />
    </div>
  </div>

  <Table columns={columns} data={filteredSubscriptions}>
    {#snippet actions(row)}
      <span class="badge {statusBadge(row.status)}">{statusText(row.status)}</span>
      {#if row.status !== 'active'}
        <button class="btn btn-ghost text-success hover:text-success-hover" onclick={() => handleActivate(row.id)} title="Активировать"><Icon name="play" class="w-3.5 h-3.5" /></button>
      {/if}
      {#if row.status === 'active'}
        <button class="btn btn-ghost text-warning hover:text-warning-hover" onclick={() => handleDeactivate(row.id)} title="Деактивировать"><Icon name="pause" class="w-3.5 h-3.5" /></button>
      {/if}
      <button class="btn btn-ghost text-danger hover:text-danger-hover" onclick={() => askDelete(row)} title="Удалить"><Icon name="trash-2" class="w-3.5 h-3.5" /></button>
    {/snippet}
  </Table>
</div>

<Modal bind:open={showGiveModal} title="Выдать подписку" size="md">
  <form class="space-y-4" onsubmit={(e) => { e.preventDefault(); handleGive(); }}>
    <div class="space-y-1">
      <label class="label"><span class="label-text">Пользователь</span></label>
      <input
        type="text"
        bind:value={userSearch}
        class="input w-full mb-2"
        placeholder="Поиск пользователей..."
      />
      <select bind:value={giveUserId} class="select w-full" disabled={usersLoading} size={5}>
        <option value="">— Выберите пользователя —</option>
        {#each filteredUsers as user (user.id)}
          <option value={user.id}>
            {user.full_name || 'Без имени'} {user.username ? `(@${user.username})` : ''} — ID: {user.id}
          </option>
        {/each}
      </select>
    </div>
    <div class="space-y-1">
      <label class="label"><span class="label-text">Тариф</span></label>
      <select bind:value={givePlanId} class="select w-full" onchange={handlePlanChange} disabled={plansLoading}>
        <option value="">Без тарифа</option>
        {#each plans as plan (plan.id)}
          <option value={plan.id}>{plan.name} — {formatPrice(plan.price)}</option>
        {/each}
      </select>
    </div>
    <div class="space-y-1">
      <label class="label"><span class="label-text">Дней</span></label>
      <input type="number" bind:value={giveDays} class="input w-full" min="1" required />
    </div>
    <div class="flex gap-3 pt-2">
      <button type="button" class="btn btn-secondary flex-1" onclick={() => showGiveModal = false}>Отмена</button>
      <button type="submit" class="btn btn-primary flex-1">Выдать</button>
    </div>
  </form>
</Modal>

<ConfirmDialog
  bind:show={confirmDelete}
  title="Удалить подписку?"
  message={`Удалить подписку #${deleteTarget?.id} пользователя ${deleteTarget?.user_full_name || '—'}?`}
  confirmText="Удалить"
  danger
  onConfirm={doDelete}
  onCancel={() => { confirmDelete = false; deleteTarget = null; }}
/>
