<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDateTime, esc } from '../lib/utils.js';
  import Table from '../components/Table.svelte';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';

  let items = $state([]);
  let total = $state(0);
  let loading = $state(true);
  let limit = $state(50);
  let offset = $state(0);
  let actionFilter = $state('');
  let dateFrom = $state('');
  let dateTo = $state('');

  async function loadLogs() {
    loading = true;
    try {
      const params = { limit, offset };
      if (actionFilter) params.action = actionFilter;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await api.getAuditLogs(params);
      items = res.items || [];
      total = res.total || 0;
    } catch (e) {
      toasts.error('Ошибка загрузки журнала: ' + e.message);
    } finally {
      loading = false;
    }
  }

  onMount(loadLogs);

  function prevPage() {
    offset = Math.max(0, offset - limit);
    loadLogs();
  }
  function nextPage() {
    if (offset + limit < total) { offset += limit; loadLogs(); }
  }

  const ACTION_LABELS = {
    admin_login: 'Вход в панель',
    admin_create: 'Создание админа',
    admin_update: 'Обновление админа',
    admin_delete: 'Удаление админа',
    settings_update: 'Обновление настроек',
    user_ban: 'Бан пользователя',
    user_unban: 'Разбан пользователя',
    key_revoke: 'Отзыв ключа',
    key_activate: 'Активация ключа',
    key_deactivate: 'Деактивация ключа',
    subscription_give: 'Выдача подписки',
    broadcast_send: 'Рассылка',
    database_clear: 'Очистка БД',
    database_export: 'Экспорт БД',
  };

  const ACTION_BADGE = {
    admin_login: 'badge-accent',
    admin_create: 'badge-success',
    admin_update: 'badge-warning',
    admin_delete: 'badge-danger',
    settings_update: 'badge-warning',
    user_ban: 'badge-danger',
    user_unban: 'badge-success',
    key_revoke: 'badge-danger',
    key_activate: 'badge-success',
    key_deactivate: 'badge-warning',
    subscription_give: 'badge-success',
    broadcast_send: 'badge-accent',
    database_clear: 'badge-danger',
    database_export: 'badge-accent',
  };

  const columns = [
    { key: 'id', label: 'ID', sortable: false, render: (r) => `<span class="font-mono text-xs text-muted">#${r.id}</span>` },
    { key: 'created_at', label: 'Дата', sortable: false, render: (r) => `<span class="text-xs">${formatDateTime(r.created_at)}</span>` },
    { key: 'admin_username', label: 'Админ', sortable: false, render: (r) => `<div><span class="font-medium">${esc(r.admin_username) || '—'}</span><br><span class="text-[11px] text-muted">${esc(r.admin_role)}</span></div>` },
    { key: 'action', label: 'Действие', sortable: false, render: (r) => `<span class="badge ${ACTION_BADGE[r.action] || ''} text-[11px]">${ACTION_LABELS[r.action] || esc(r.action)}</span>` },
    { key: 'target_type', label: 'Объект', sortable: false, render: (r) => r.target_type ? `<span class="text-xs">${esc(r.target_type)} #${r.target_id ?? ''}</span>` : `<span class="text-xs text-muted">—</span>` },
    { key: 'details', label: 'Детали', sortable: false, render: (r) => `<span class="text-xs text-muted truncate block max-w-[300px]" title="${esc(r.details || '')}">${esc(r.details || '—')}</span>` },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">Журнал действий</h1>
      <p class="text-sm text-muted mt-1">{total} записей</p>
    </div>
    <div class="flex gap-3 w-full sm:w-auto">
      <select bind:value={actionFilter} class="select w-full sm:w-48" onchange={() => { offset = 0; loadLogs(); }}>
        <option value="">Все действия</option>
        {#each Object.entries(ACTION_LABELS) as [key, label]}
          <option value={key}>{label}</option>
        {/each}
      </select>
      <input type="date" bind:value={dateFrom} class="input w-full sm:w-44" onchange={() => { offset = 0; loadLogs(); }} />
      <input type="date" bind:value={dateTo} class="input w-full sm:w-44" onchange={() => { offset = 0; loadLogs(); }} />
    </div>
  </div>

  <Table {columns} data={items} emptyText="Журнал пуст" />

  {#if total > limit}
    <div class="flex items-center justify-between text-sm text-muted">
      <span>Показано {offset + 1}–{Math.min(offset + limit, total)} из {total}</span>
      <div class="flex gap-2">
        <button class="btn btn-secondary text-xs" onclick={prevPage} disabled={offset === 0}>← Назад</button>
        <button class="btn btn-secondary text-xs" onclick={nextPage} disabled={offset + limit >= total}>Далее →</button>
      </div>
    </div>
  {/if}
</div>
