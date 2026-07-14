<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.js';
  import { toasts } from '../lib/stores.js';
  import Spinner from '../components/Spinner.svelte';

  let payments = $state([]);
  let loading = $state(true);
  let filter = $state('all');

  onMount(loadPayments);

  async function loadPayments() {
    loading = true;
    try {
      const params = { limit: 200 };
      if (filter !== 'all') params.status = filter;
      payments = await api.getPayments(params);
    } catch (e) {
      toasts.error('Ошибка загрузки: ' + e.message);
    } finally {
      loading = false;
    }
  }

  async function handleRefund(payment) {
    try {
      await api.refundPayment(payment.id);
      toasts.success(`Возврат #${payment.id} выполнен`);
      await loadPayments();
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    }
  }

  function statusColor(status) {
    const map = {
      succeeded: 'badge-success',
      pending: 'badge-warning',
      cancelled: 'badge-ghost',
      refunded: 'badge-info',
    };
    return map[status] || 'badge-ghost';
  }

  $effect(() => {
    filter;
    loadPayments();
  });
</script>

<div class="fade-in">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">Платежи</h1>
    <select bind:value={filter} class="select select-bordered select-sm">
      <option value="all">Все</option>
      <option value="succeeded">Оплачен</option>
      <option value="pending">Ожидает</option>
      <option value="cancelled">Отменён</option>
      <option value="refunded">Возврат</option>
    </select>
  </div>

  <Spinner {loading} />

  {#if !loading}
    <div class="table-container">
      <div class="overflow-x-auto">
        <table class="table table-zebra table-hover">
          <thead>
            <tr>
              <th>ID</th>
              <th>Пользователь</th>
              <th>Тариф</th>
              <th>Сумма</th>
              <th>Провайдер</th>
              <th>Статус</th>
              <th>Дата</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {#if payments.length === 0}
              <tr>
                <td colspan="8" class="text-center py-8 text-base-content/40">Нет платежей</td>
              </tr>
            {:else}
              {#each payments as p (p.id)}
                <tr class="fade-in">
                  <td class="font-mono text-sm">#{p.id}</td>
                  <td>{p.user_id}</td>
                  <td>{p.plan_id ?? '—'}</td>
                  <td class="font-semibold">{p.amount} {p.currency}</td>
                  <td><span class="badge badge-outline badge-sm">{p.provider}</span></td>
                  <td>
                    <span class="badge badge-sm {statusColor(p.status)}">{p.status}</span>
                  </td>
                  <td class="text-sm">{p.created_at ? new Date(p.created_at).toLocaleString('ru-RU') : '—'}</td>
                  <td>
                    {#if p.status === 'succeeded'}
                      <button class="btn btn-xs btn-warning" onclick={() => handleRefund(p)}>
                        Возврат
                      </button>
                    {/if}
                  </td>
                </tr>
              {/each}
            {/if}
          </tbody>
        </table>
      </div>
    </div>
  {/if}
</div>
