<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatPrice, formatDateTime } from '../lib/utils.js';

  let payments = $state([]);
  let loading = $state(true);
  let statusFilter = $state('');
  let offset = $state(0);
  const limit = 50;

  async function loadPayments() {
    loading = true;
    try {
      payments = await api.getPayments({ limit, offset, status: statusFilter || undefined });
    } catch (e) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  let initDone = $state(false);

  onMount(() => { initDone = true; });

  $effect(() => {
    if (!initDone) return;
    const _ = statusFilter;
    offset = 0;
    loadPayments();
  });

  async function handleRefund(payment) {
    try {
      await api.refundPayment(payment.id);
      toasts.success('Возврат выполнен');
      await loadPayments();
    } catch (e) {
      toasts.error(e.message);
    }
  }

  function statusBadge(status) {
    const map = { succeeded: 'badge-success', pending: 'badge-warning', cancelled: 'badge-ghost', refunded: 'badge-info', failed: 'badge-error' };
    return map[status] || 'badge-ghost';
  }

  function statusLabel(s) {
    const map = { succeeded: 'Оплачен', pending: 'Ожидает', cancelled: 'Отменён', refunded: 'Возврат', failed: 'Ошибка' };
    return map[s] || s;
  }

  function providerLabel(p) {
    const map = { yookassa: 'YooKassa', yookassa_sbp: 'СБП', cryptobot: 'CryptoBot', freekassa: 'FreeKassa', aikassa: 'AiKassa', platega: 'Platega', paypalych: 'PayPalych', balance: 'Баланс', topup: 'Пополнение', telegram_stars: 'TG Stars' };
    return map[p] || p;
  }
</script>

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold">Платежи</h1>
      <p class="text-sm text-base-content/40 mt-1">{payments.length} записей</p>
    </div>
    <div class="flex gap-2">
      <select bind:value={statusFilter} class="select select-bordered select-sm input-glass">
        <option value="">Все статусы</option>
        <option value="succeeded">Оплачен</option>
        <option value="pending">Ожидает</option>
        <option value="cancelled">Отменён</option>
        <option value="refunded">Возврат</option>
        <option value="failed">Ошибка</option>
      </select>
    </div>
  </div>

  {#if loading}
    <div class="flex justify-center py-12"><span class="loading loading-spinner loading-lg text-primary"></span></div>
  {:else}
    <div class="card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="table table-zebra">
          <thead>
            <tr>
              <th class="text-xs font-medium uppercase tracking-wider">ID</th>
              <th class="text-xs font-medium uppercase tracking-wider">Пользователь</th>
              <th class="text-xs font-medium uppercase tracking-wider">Сумма</th>
              <th class="text-xs font-medium uppercase tracking-wider">Провайдер</th>
              <th class="text-xs font-medium uppercase tracking-wider">Статус</th>
              <th class="text-xs font-medium uppercase tracking-wider">Дата</th>
              <th class="text-xs font-medium uppercase tracking-wider w-1"></th>
            </tr>
          </thead>
          <tbody>
            {#if payments.length === 0}
              <tr><td colspan="7" class="text-center py-12 text-base-content/30">Нет платежей</td></tr>
            {:else}
              {#each payments as p, i (p.id)}
                <tr class="animate-fade-in" style="animation-delay: {i * 15}ms">
                  <td><span class="font-mono text-xs">#{p.id}</span></td>
                  <td><span class="text-primary font-mono text-xs">#{p.user_id}</span></td>
                  <td><span class="font-medium">{formatPrice(p.amount, p.currency)}</span></td>
                  <td><span class="badge badge-sm badge-outline">{providerLabel(p.provider)}</span></td>
                  <td><span class="badge badge-sm badge-glow {statusBadge(p.status)}">{statusLabel(p.status)}</span></td>
                  <td><span class="text-xs text-base-content/50">{formatDateTime(p.created_at)}</span></td>
                  <td>
                    {#if p.status === 'succeeded'}
                      <button class="btn btn-xs btn-warning btn-ghost" onclick={() => handleRefund(p)}>Возврат</button>
                    {/if}
                  </td>
                </tr>
              {/each}
            {/if}
          </tbody>
        </table>
      </div>
    </div>

    {#if payments.length >= limit}
      <div class="flex justify-center gap-2">
        <button class="btn btn-sm btn-ghost" disabled={offset === 0} onclick={() => { offset -= limit; loadPayments(); }}>Назад</button>
        <span class="btn btn-sm btn-ghost no-animation">Записи {offset + 1}–{offset + payments.length}</span>
        <button class="btn btn-sm btn-ghost" disabled={payments.length < limit} onclick={() => { offset += limit; loadPayments(); }}>Далее</button>
      </div>
    {/if}
  {/if}
</div>
