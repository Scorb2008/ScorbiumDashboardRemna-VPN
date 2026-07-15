<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { formatPrice } from '../lib/utils.js';
  import StatsCard from '../components/StatsCard.svelte';
  import Spinner from '../components/Spinner.svelte';

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

<div class="page-enter space-y-6">
  <div>
    <h1 class="text-2xl font-bold">Dashboard</h1>
    <p class="text-sm text-base-content/40 mt-1">Обзор системы</p>
  </div>

  {#if stats}
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
      <StatsCard label="Пользователей" value={stats.total_users ?? 0} icon="M12 4.354a4 4 0 110 7.292 4 4 0 010-7.292zM15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" gradient="gradient-primary" />
      <StatsCard label="Активных подписок" value={stats.active_subscriptions ?? 0} icon="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" gradient="gradient-success" />
      <StatsCard label="Выручка" value={formatPrice(stats.total_revenue)} icon="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" gradient="gradient-info" />
      <StatsCard label="Ожидают оплаты" value={stats.pending_payments ?? 0} icon="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" gradient="gradient-warning" />
      <StatsCard label="Открытых тикетов" value={stats.open_tickets ?? 0} icon="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" gradient="gradient-error" />
    </div>

    {#if stats.bot_username}
      <div class="card p-5 animate-fade-in">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-info/10 flex items-center justify-center">
            <span class="text-lg">&#x1F4F1;</span>
          </div>
          <div>
            <p class="text-xs text-base-content/40 uppercase tracking-wider">Telegram Bot</p>
            <p class="font-medium">@{stats.bot_username}</p>
          </div>
        </div>
      </div>
    {/if}

    {#if stats.open_tickets > 0}
      <a href="#/support" class="alert alert-warning animate-fade-in cursor-pointer hover:shadow-lg transition-shadow">
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span>Есть {stats.open_tickets} открытых тикетов поддержки</span>
      </a>
    {/if}
  {/if}
</div>
