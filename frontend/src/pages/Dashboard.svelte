<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { formatPrice } from '../lib/utils.js';
  import StatsCard from '../components/StatsCard.svelte';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';

  let stats = $state(null);
  let loading = $state(true);

  onMount(async () => {
    try {
      stats = await api.getDashboard();
    } catch (e) {
      console.error(e);
    } finally {
      loading = false;
    }
  });
</script>

<Spinner {loading} />

<div class="space-y-6 page-enter">
  <div>
    <h1 class="text-[28px] font-bold tracking-tight">Dashboard</h1>
    <p class="text-sm text-muted mt-1">Обзор системы</p>
  </div>

  {#if stats}
    <!-- KPI Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatsCard label="Пользователей" value={stats.total_users ?? 0} icon="users" subtitle="{stats.new_users_today ?? 0} сегодня" trend="up" />
      <StatsCard label="Активных подписок" value={stats.active_subscriptions ?? 0} icon="key" />
      <StatsCard label="Выручка" value={formatPrice(stats.total_revenue)} icon="dollarSign" subtitle={stats.revenue_trend || null} trend="up" />
      <StatsCard label="Открытых тикетов" value={stats.open_tickets ?? 0} icon="lifeBuoy" />
    </div>

    <!-- Info cards -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {#if stats.bot_username}
        <div class="card p-6">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-[10px] bg-surface-3 border border-surface-4/50 flex items-center justify-center">
              <Icon name="phone" size={18} class="text-muted" />
            </div>
            <div>
              <h3 class="text-sm font-semibold">Telegram Bot</h3>
              <p class="text-xs text-muted">@{stats.bot_username}</p>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-[11px] text-muted uppercase tracking-wider mb-1">Подключено</p>
              <p class="text-xl font-bold">{stats.connected_users ?? 0}</p>
            </div>
            <div>
              <p class="text-[11px] text-muted uppercase tracking-wider mb-1">Статус</p>
              <span class="badge badge-success">Активен</span>
            </div>
          </div>
        </div>
      {/if}

      {#if stats.pending_payments > 0}
        <div class="card p-6 border-[#eab308]/20">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-[10px] bg-[#eab308]/10 flex items-center justify-center">
              <Icon name="alertTriangle" size={18} class="text-[#eab308]" />
            </div>
            <div>
              <h3 class="text-sm font-semibold">Ожидают оплаты</h3>
              <p class="text-xs text-muted">{stats.pending_payments} платежей требуют внимания</p>
            </div>
          </div>
        </div>
      {/if}

      <div class="card p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-[10px] bg-surface-3 border border-surface-4/50 flex items-center justify-center">
            <Icon name="server" size={18} class="text-muted" />
          </div>
          <div>
            <h3 class="text-sm font-semibold">Панель</h3>
            <p class="text-xs text-muted">Remnawave</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <p class="text-[11px] text-muted uppercase tracking-wider mb-1">Серверы</p>
            <p class="text-xl font-bold">{stats.nodes_count ?? '—'}</p>
          </div>
          <div>
            <p class="text-[11px] text-muted uppercase tracking-wider mb-1">Синхронизация</p>
            <span class="badge badge-success">Активна</span>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>
