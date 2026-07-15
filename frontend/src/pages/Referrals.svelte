<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.js';
  import { toasts } from '../lib/stores.js';
  import StatsCard from '../components/StatsCard.svelte';
  import Spinner from '../components/Spinner.svelte';

  let stats = $state(null);
  let topReferrers = $state([]);
  let loading = $state(true);

  onMount(async () => {
    try {
      const [statsRes, topRes] = await Promise.allSettled([
        api.getReferralStats(),
        api.getTopReferrers(20),
      ]);
      if (statsRes.status === 'fulfilled') stats = statsRes.value;
      if (topRes.status === 'fulfilled') topReferrers = topRes.value || [];
    } catch (e) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  });
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div>
    <h1 class="text-2xl font-bold">Рефералы</h1>
    <p class="text-sm text-base-content/40 mt-1">Статистика реферальной системы</p>
  </div>

  {#if stats}
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <StatsCard label="Всего рефералов" value={stats.total_referrals ?? stats.total ?? 0} icon="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" gradient="gradient-primary" />
      <StatsCard label="Активных рефереров" value={stats.active_referrers ?? stats.active ?? 0} icon="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" gradient="gradient-success" />
      <StatsCard label="Выплачено бонусов" value={stats.total_bonuses ?? stats.bonuses ?? 0} icon="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" gradient="gradient-info" />
    </div>
  {/if}

  {#if topReferrers.length > 0}
    <div class="card overflow-hidden">
      <div class="card-header">
        <h2 class="font-semibold">Топ рефереров</h2>
        <span class="badge badge-sm">{topReferrers.length}</span>
      </div>
      <div class="overflow-x-auto">
        <table class="table table-zebra">
          <thead>
            <tr>
              <th class="text-xs font-medium uppercase tracking-wider">#</th>
              <th class="text-xs font-medium uppercase tracking-wider">Пользователь</th>
              <th class="text-xs font-medium uppercase tracking-wider">Рефералов</th>
              <th class="text-xs font-medium uppercase tracking-wider">Бонусы</th>
            </tr>
          </thead>
          <tbody>
            {#each topReferrers as ref, i}
              <tr class="animate-fade-in" style="animation-delay: {i * 30}ms">
                <td><span class="text-xs text-base-content/40">{i + 1}</span></td>
                <td>
                  <span class="font-medium">{ref.username || ref.full_name || '—'}</span>
                  <span class="text-xs text-base-content/40 ml-2">#{ref.user_id || ref.id}</span>
                </td>
                <td><span class="badge badge-sm badge-primary">{ref.referral_count ?? ref.count ?? 0}</span></td>
                <td><span class="text-sm text-success font-medium">{ref.total_bonuses ?? ref.bonuses ?? 0} RUB</span></td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {:else if !loading}
    <div class="card p-12 text-center text-base-content/30">
      <p>Нет данных о рефералах</p>
    </div>
  {/if}
</div>
