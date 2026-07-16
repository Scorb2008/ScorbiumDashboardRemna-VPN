<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import Spinner from '../components/Spinner.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';
  import Icon from '../components/Icon.svelte';

  let stats = $state(null);
  let loading = $state(true);
  let exporting = $state(false);
  let confirmClear = $state(false);
  let cleared = $state(false);

  async function loadStats() {
    loading = true;
    try { stats = await api.getDatabaseStats(); }
    catch (e) { toasts.error('Ошибка загрузки статистики: ' + e.message); }
    finally { loading = false; }
  }

  onMount(loadStats);

  async function handleExport(format) {
    exporting = true;
    try {
      const res = await api.exportDatabase(format);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `backup_${new Date().toISOString().slice(0, 10)}.${format === 'gz' ? 'sql.gz' : 'sql'}`;
      a.click();
      URL.revokeObjectURL(url);
      toasts.success('Бэкап скачан');
    } catch (e) { toasts.error('Ошибка экспорта: ' + e.message); }
    finally { exporting = false; }
  }

  async function doClear() {
    try {
      await api.clearDatabase();
      toasts.success('База данных очищена');
      cleared = true;
      await loadStats();
    } catch (e) { toasts.error('Ошибка: ' + e.message); }
    confirmClear = false;
  }
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div>
    <h1 class="text-[28px] font-bold tracking-tight text-text">База данных</h1>
    <p class="text-sm text-muted mt-1">Управление, резервное копирование и обслуживание</p>
  </div>

  {#if stats}
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="stat-card">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-8 h-8 rounded-[8px] bg-accent/10 flex items-center justify-center">
            <Icon name="users" class="w-4 h-4 text-accent" />
          </div>
        </div>
        <p class="text-2xl font-bold">{stats.users}</p>
        <p class="text-[11px] text-muted mt-0.5">Пользователей</p>
      </div>
      <div class="stat-card">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-8 h-8 rounded-[8px] bg-accent/10 flex items-center justify-center">
            <Icon name="key-round" class="w-4 h-4 text-accent" />
          </div>
        </div>
        <p class="text-2xl font-bold">{stats.vpn_keys}</p>
        <p class="text-[11px] text-muted mt-0.5">VPN ключей</p>
      </div>
      <div class="stat-card">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-8 h-8 rounded-[8px] bg-warning/10 flex items-center justify-center">
            <Icon name="wallet" class="w-4 h-4 text-warning" />
          </div>
        </div>
        <p class="text-2xl font-bold">{stats.payments}</p>
        <p class="text-[11px] text-muted mt-0.5">Платежей</p>
      </div>
      <div class="stat-card">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-8 h-8 rounded-[8px] bg-success/10 flex items-center justify-center">
            <Icon name="headset" class="w-4 h-4 text-success" />
          </div>
        </div>
        <p class="text-2xl font-bold">{stats.tickets}</p>
        <p class="text-[11px] text-muted mt-0.5">Тикетов</p>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div class="card p-5 space-y-4">
        <h3 class="text-[15px] font-semibold">Резервное копирование</h3>
        <p class="text-[13px] text-muted">Экспорт базы данных в SQL или gzip формат</p>
        <div class="flex gap-3">
          <button class="btn btn-secondary flex-1" onclick={() => handleExport('sql')} disabled={exporting}>
            <Icon name="download" class="w-4 h-4" />
            {exporting ? 'Экспорт...' : 'SQL'}
          </button>
          <button class="btn btn-secondary flex-1" onclick={() => handleExport('gz')} disabled={exporting}>
            <Icon name="archive" class="w-4 h-4" />
            {exporting ? 'Экспорт...' : 'SQL + GZip'}
          </button>
        </div>
      </div>

      <div class="card p-5 space-y-4">
        <h3 class="text-[15px] font-semibold text-danger">Опасная зона</h3>
        <p class="text-[13px] text-muted">Удаление всех пользовательских данных. Администраторы и настройки сохраняются.</p>
        <button class="btn btn-danger w-full" onclick={() => confirmClear = true} disabled={cleared}>
          <Icon name="trash-2" class="w-4 h-4" />
          {cleared ? 'Данные удалены' : 'Очистить базу данных'}
        </button>
      </div>
    </div>

    <div class="card p-5 space-y-3">
      <h3 class="text-[15px] font-semibold">Информация</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-[13px]">
        <div class="bg-surface-2 rounded-[10px] p-3.5">
          <p class="text-muted text-xs mb-1">PostgreSQL</p>
          <p class="font-medium">База данных PostgreSQL</p>
        </div>
        <div class="bg-surface-2 rounded-[10px] p-3.5">
          <p class="text-muted text-xs mb-1">Alembic</p>
          <p class="font-medium">Миграции через Alembic</p>
        </div>
      </div>
    </div>
  {/if}
</div>

<ConfirmDialog
  bind:open={confirmClear}
  title="Очистить базу данных?"
  message="Это удалит ВСЕХ пользователей, VPN ключи, платежи, тикеты и реферальные связи. Администраторы и настройки сохраняются."
  confirmText="Очистить всё"
  danger
  onConfirm={doClear} />
