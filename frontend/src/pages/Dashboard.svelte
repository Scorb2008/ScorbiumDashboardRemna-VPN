<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.js';
  import { toasts } from '../lib/stores.js';
  import StatsCard from '../components/StatsCard.svelte';
  import Spinner from '../components/Spinner.svelte';

  let stats = $state(null);
  let loading = $state(true);

  onMount(async () => {
    try {
      stats = await api.getDashboard();
    } catch (e) {
      toasts.error('Ошибка загрузки дашборда: ' + e.message);
    } finally {
      loading = false;
    }
  });
</script>

<div class="fade-in">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">Дашборд</h1>
    {#if stats?.bot_username}
      <span class="badge badge-outline">@{stats.bot_username}</span>
    {/if}
  </div>

  <Spinner {loading} />

  {#if stats}
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <StatsCard label="Пользователей" value={stats.total_users} icon="👥" />
      <StatsCard label="Активных подписок" value={stats.active_subscriptions} icon="🔑" color="success" />
      <StatsCard label="Доход" value="{stats.total_revenue} ₽" icon="💰" color="warning" />
      <StatsCard label="Ожидают оплаты" value={stats.pending_payments} icon="⏳" color="info" />
    </div>

    {#if stats.open_tickets > 0}
      <div class="alert alert-warning mb-6">
        <span>🎫 Открытых тикетов: <strong>{stats.open_tickets}</strong></span>
        <a href="#/support" class="btn btn-sm btn-ghost">Перейти</a>
      </div>
    {/if}
  {/if}
</div>
