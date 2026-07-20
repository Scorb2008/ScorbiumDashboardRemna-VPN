<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { formatPrice } from '../lib/utils.js';
  import { wsConnect, getWsState, onWsEvent } from '../lib/ws.svelte.js';
  import StatsCard from '../components/StatsCard.svelte';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';

  let stats = $state(null);
  let loading = $state(true);
  let logoUrl = $state('');
  let error = $state(null);
  let wsState = getWsState();
  let liveEvents = $state([]);

  const EVENT_ICONS = {
    new_user: { icon: 'user-plus', color: 'text-success', bg: 'bg-success/10', label: 'Новый пользователь' },
    new_payment: { icon: 'wallet', color: 'text-accent', bg: 'bg-accent/10', label: 'Новый платёж' },
    expired_sub: { icon: 'alertTriangle', color: 'text-warning', bg: 'bg-warning/10', label: 'Истекла подписка' },
    new_ticket: { icon: 'headset', color: 'text-warning', bg: 'bg-warning/10', label: 'Новый тикет' },
  };

  function formatEventText(event) {
    const d = event.data || {};
    switch (event.type) {
      case 'new_user':
        return `${d.full_name || d.username || 'Пользователь'} (${d.user_id})`;
      case 'new_payment':
        return `${formatPrice(d.amount || 0)} — user #${d.user_id || '?'}`;
      case 'expired_sub':
        return `${d.count || 0} подписок`;
      case 'new_ticket':
        return `${d.subject || 'Тикет'} — user #${d.user_id || '?'}`;
      default:
        return JSON.stringify(d);
    }
  }

  function eventTime(ts) {
    if (!ts) return '';
    try { return new Date(ts).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' }); }
    catch (_) { return ''; }
  }

  onMount(async () => {
    try {
      const [s, settings] = await Promise.all([
        api.getDashboard(),
        api.getSettings().catch(() => ({})),
      ]);
      stats = s;
      logoUrl = settings?.logo_url || '';
    } catch (e) {
      console.error(e);
      error = e.message || 'Ошибка загрузки';
    } finally {
      loading = false;
    }

    wsConnect();
    const unsub = onWsEvent((event) => {
      liveEvents = [event, ...liveEvents].slice(0, 20);
    });
    return unsub;
  });
</script>

<Spinner {loading} />

<div class="page-enter space-y-6">
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-4">
      {#if logoUrl}
        <img src={logoUrl} alt="Logo" class="w-10 h-10 rounded-[12px] object-cover" />
      {/if}
      <div>
        <h1 class="text-[28px] font-bold tracking-tight text-text">Обзор</h1>
        <p class="text-sm text-muted mt-1">Главная панель управления</p>
      </div>
    </div>
    <div class="flex items-center gap-2">
      <div class="w-2 h-2 rounded-full {wsState.connected ? 'bg-success animate-pulse-glow' : 'bg-danger'}"></div>
      <span class="text-xs text-muted">{wsState.connected ? 'Live' : 'Offline'}</span>
    </div>
  </div>

  {#if stats}
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatsCard label="Пользователей" value={stats.total_users ?? 0} icon="users" subtitle="{stats.new_users_today ?? 0} сегодня" trend="up" />
      <StatsCard label="Активных подписок" value={stats.active_subscriptions ?? 0} icon="key-round" subtitle="{stats.subscriptions_today ?? 0} новых" trend={stats.subscriptions_today > 0 ? 'up' : 'neutral'} />
      <StatsCard label="Выручка" value={formatPrice(stats.total_revenue ?? 0)} icon="wallet" subtitle={stats.revenue_trend ? `${stats.revenue_trend}` : 'за всё время'} trend={stats.revenue_trend === 'up' ? 'up' : 'neutral'} />
      <StatsCard label="Открытых тикетов" value={stats.open_tickets ?? 0} icon="headset" subtitle={stats.tickets_today ? `${stats.tickets_today} сегодня` : 'нет открытых'} trend={stats.open_tickets > 0 ? 'up' : 'down'} />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div class="stat-card p-5 relative overflow-hidden">
        <div class="absolute top-0 right-0 w-32 h-32 bg-accent/3 rounded-full -translate-y-1/2 translate-x-1/2"></div>
        <div class="relative">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-[10px] bg-accent/10 flex items-center justify-center">
              <Icon name="bot" size={18} class="text-accent" />
            </div>
            <div>
              <h3 class="text-[15px] font-semibold">Telegram Бот</h3>
              <p class="text-xs text-muted">{stats.bot_username ? '@'+stats.bot_username : 'Не подключён'}</p>
            </div>
          </div>
          <div class="flex items-center gap-4">
            <div class="flex-1">
              <p class="text-[11px] text-muted uppercase tracking-wider mb-1">Пользователей</p>
              <p class="text-2xl font-bold">{stats.connected_users ?? stats.total_users ?? 0}</p>
            </div>
            <div class="flex-1">
              <p class="text-[11px] text-muted uppercase tracking-wider mb-1">Статус</p>
              {#if stats.bot_username}
                <span class="badge badge-success">Активен</span>
              {:else}
                <span class="badge badge-danger">Не подключён</span>
              {/if}
            </div>
            <button class="btn btn-secondary btn-sm" onclick={() => stats.bot_username ? window.open(`https://t.me/${stats.bot_username}`, '_blank') : null} disabled={!stats.bot_username}>
              <Icon name="external-link" class="w-3.5 h-3.5" />
              Перейти
            </button>
          </div>
        </div>
      </div>

      <div class="stat-card p-5">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-[10px] bg-success/10 flex items-center justify-center">
            <Icon name="server" size={18} class="text-success" />
          </div>
          <div>
            <h3 class="text-[15px] font-semibold">Remnawave Панель</h3>
            <p class="text-xs text-muted">VPN инфраструктура</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <p class="text-[11px] text-muted uppercase tracking-wider mb-1">Узлы</p>
            <p class="text-2xl font-bold">{stats.nodes_count ?? stats.nodes_online ?? '—'}</p>
          </div>
          <div>
            <p class="text-[11px] text-muted uppercase tracking-wider mb-1">Загрузка</p>
            <div class="flex items-center gap-2 mt-1">
              <div class="flex-1 h-1.5 bg-surface-3 rounded-full overflow-hidden">
                <div class="h-full rounded-full bg-accent transition-all" style="width: {Math.min(stats.cpu_usage ?? 0, 100)}%"></div>
              </div>
              <span class="text-xs font-medium">{stats.cpu_usage ?? '—'}{stats.cpu_usage != null ? '%' : ''}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="card p-4 flex items-center gap-3">
        <div class="w-9 h-9 rounded-[9px] bg-warning/10 flex items-center justify-center flex-shrink-0">
          <Icon name="alertTriangle" class="w-4 h-4 text-warning" />
        </div>
        <div>
          <p class="text-[11px] text-muted">Ожидают оплаты</p>
          <p class="text-lg font-semibold">{stats.pending_payments ?? 0}</p>
        </div>
      </div>
      <div class="card p-4 flex items-center gap-3">
        <div class="w-9 h-9 rounded-[9px] bg-accent/10 flex items-center justify-center flex-shrink-0">
          <Icon name="users" class="w-4 h-4 text-accent" />
        </div>
        <div>
          <p class="text-[11px] text-muted">Сегодня новых</p>
          <p class="text-lg font-semibold">{stats.new_users_today ?? 0}</p>
        </div>
      </div>
      <div class="card p-4 flex items-center gap-3">
        <div class="w-9 h-9 rounded-[9px] bg-success/10 flex items-center justify-center flex-shrink-0">
          <Icon name="wallet" class="w-4 h-4 text-success" />
        </div>
        <div>
          <p class="text-[11px] text-muted">Выручка сегодня</p>
          <p class="text-lg font-semibold">{formatPrice(stats.revenue_today ?? 0)}</p>
        </div>
      </div>
    </div>

    {#if liveEvents.length > 0}
      <div class="card p-5">
        <div class="flex items-center gap-2 mb-3">
          <div class="w-2 h-2 rounded-full bg-success animate-pulse-glow"></div>
          <h3 class="text-[15px] font-semibold">Live-события</h3>
          <span class="text-[11px] text-muted ml-auto">{liveEvents.length} событий</span>
        </div>
        <div class="space-y-0 divide-y divide-border max-h-64 overflow-y-auto">
          {#each liveEvents as event, i}
            {@const meta = EVENT_ICONS[event.type] || { icon: 'activity', color: 'text-muted', bg: 'bg-surface-3', label: event.type }}
            <div class="flex items-center gap-3 py-2 {i === 0 ? 'animate-fade-in' : ''}">
              <div class="w-7 h-7 rounded-[7px] {meta.bg} flex items-center justify-center flex-shrink-0">
                <Icon name={meta.icon} class="w-3.5 h-3.5 {meta.color}" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-[13px] truncate">{meta.label}: {formatEventText(event)}</p>
              </div>
              <span class="text-[10px] text-muted shrink-0">{eventTime(event.ts)}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    {#if stats.recent_activity?.length}
      <div class="card p-5">
        <h3 class="text-[15px] font-semibold mb-3">Последняя активность</h3>
        <div class="space-y-0 divide-y divide-border">
          {#each stats.recent_activity as activity}
            <div class="flex items-center gap-3 py-2.5">
              <div class="w-7 h-7 rounded-[7px] bg-surface-3 flex items-center justify-center">
                <Icon name={activity.icon || 'activity'} class="w-3.5 h-3.5 text-muted" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-[13px] truncate">{activity.text}</p>
                <p class="text-[11px] text-muted">{activity.time}</p>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  {:else if !loading}
    <div class="card p-12 flex flex-col items-center gap-3 text-center">
      <Icon name="bar-chart-3" class="w-12 h-12 text-muted" />
      <p class="text-[17px] font-semibold">{error ? 'Ошибка загрузки' : 'Нет данных'}</p>
      <p class="text-[13px] text-muted">{error || 'Статистика пока недоступна'}</p>
      {#if error}
        <button onclick={() => window.location.reload()} class="btn btn-primary btn-sm mt-2">Повторить</button>
      {/if}
    </div>
  {/if}
</div>
