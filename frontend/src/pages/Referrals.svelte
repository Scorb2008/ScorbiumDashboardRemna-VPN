<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatPrice, formatDateTime, esc } from '../lib/utils.js';
  import Table from '../components/Table.svelte';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';

  let referrals = $state([]);
  let loading = $state(true);
  let stats = $state({ total_referrals: 0, total_earned: 0 });
  let search = $state('');

  async function loadReferrals() {
    loading = true;
    try {
      const data = await api.getReferrals({ limit: 500 });
      referrals = Array.isArray(data) ? data : (data.items || []);
      stats = data.stats || { total_referrals: referrals.length, total_earned: 0 };
    } catch (e) { toasts.error('Ошибка загрузки: ' + e.message); }
    finally { loading = false; }
  }

  onMount(loadReferrals);

  let filteredReferrals = $derived(
    search
      ? referrals.filter(r =>
          (r.referrer_username || '').toLowerCase().includes(search.toLowerCase()) ||
          (r.referred_username || '').toLowerCase().includes(search.toLowerCase()) ||
          String(r.referrer_id).includes(search) ||
          String(r.referred_id).includes(search))
      : referrals
  );

  const columns = [
    { key: 'referrer_id', label: 'Реферер', sortable: true, render: (r) => `<div><span class="font-medium">${esc(r.referrer_full_name) || '—'}</span><br><span class="text-xs text-muted">${r.referrer_username ? '@'+esc(r.referrer_username) : 'ID: '+r.referrer_id}</span></div>` },
    { key: 'referred_id', label: 'Приглашённый', sortable: true, render: (r) => `<div><span class="font-medium">${esc(r.referred_full_name) || '—'}</span><br><span class="text-xs text-muted">${r.referred_username ? '@'+esc(r.referred_username) : 'ID: '+r.referred_id}</span></div>` },
    { key: 'earned_amount', label: 'Заработок', sortable: true, render: (r) => `<span class="font-mono text-xs">${formatPrice(r.earned_amount || 0)}</span>` },
    { key: 'created_at', label: 'Дата', sortable: true, render: (r) => `<span class="text-xs text-muted">${formatDateTime(r.created_at)}</span>` },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">Реферальная система</h1>
      <p class="text-sm text-muted mt-1">{stats.total_referrals} рефералов &middot; {formatPrice(stats.total_earned)} заработано</p>
    </div>
    <input type="text" bind:value={search} placeholder="Поиск..." class="input w-full sm:w-80" />
  </div>

  {#if filteredReferrals.length === 0 && !loading}
    <div class="card p-12 flex flex-col items-center gap-3 text-center">
      <Icon name="users" class="w-10 h-10 text-muted" />
      <p class="text-[15px] font-medium">Нет данных</p>
      <p class="text-[13px] text-muted">Реферальные связи появятся здесь</p>
    </div>
  {:else}
    <Table columns={columns} data={filteredReferrals} />
  {/if}
</div>
