<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatPrice, formatDateTime, esc } from '../lib/utils.js';

  function formatPaymentMethod(method) {
    if (!method) return '—';
    const map = { yookassa: 'ЮKassa', cryptobot: 'CryptoBot', stripe: 'Stripe', manual: 'Ручной' };
    return map[method] || method;
  }
  import Table from '../components/Table.svelte';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';

  let payments = $state([]);
  let loading = $state(true);
  let search = $state('');
  let statusFilter = $state('all');

  async function loadPayments() {
    loading = true;
    try { payments = await api.getPayments({ limit: 500 }); }
    catch (e) { toasts.error('Ошибка загрузки: ' + e.message); }
    finally { loading = false; }
  }

  onMount(loadPayments);

  let filteredPayments = $derived(
    payments.filter(p => {
      const matchSearch = !search ||
        (p.user_username || '').toLowerCase().includes(search.toLowerCase()) ||
        (p.user_full_name || '').toLowerCase().includes(search.toLowerCase()) ||
        String(p.id).includes(search) ||
        String(p.user_id).includes(search);
      const matchStatus = statusFilter === 'all' || p.status === statusFilter;
      return matchSearch && matchStatus;
    })
  );

  function statusBadge(status) {
    switch (status) {
      case 'succeeded': return 'badge-success';
      case 'pending': return 'badge-warning';
      case 'canceled': return 'badge-danger';
      case 'waiting_for_capture': return 'badge-accent';
      default: return '';
    }
  }
  function statusText(status) {
    switch (status) {
      case 'succeeded': return 'Оплачен';
      case 'pending': return 'Ожидает';
      case 'canceled': return 'Отменён';
      case 'waiting_for_capture': return 'Подтверждение';
      default: return status;
    }
  }

  const columns = [
    { key: 'id', label: 'ID', sortable: true, render: (r) => `<span class="font-mono text-xs text-zinc-500">#${r.id}</span>` },
    { key: 'user_id', label: 'Пользователь', sortable: true, render: (r) => `<div><span class="font-medium">${esc(r.user_full_name) || '—'}</span><br><span class="text-xs text-muted">${r.user_username ? '@'+esc(r.user_username) : 'ID: '+r.user_id}</span></div>` },
    { key: 'amount', label: 'Сумма', sortable: true, render: (r) => `<span class="font-mono text-xs">${formatPrice(r.amount)}</span>` },
    { key: 'created_at', label: 'Дата', sortable: true, render: (r) => `<span class="text-xs text-muted">${formatDateTime(r.created_at)}</span>` },
    { key: 'payment_method', label: 'Способ', sortable: true, render: (r) => `<span class="text-xs">${formatPaymentMethod(r.payment_method)}</span>` },
    { key: 'plan_name', label: 'Тариф', sortable: true, render: (r) => `<span class="text-xs">${esc(r.plan_name) || '—'}</span>` },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">Платежи</h1>
      <p class="text-sm text-muted mt-1">{filteredPayments.length} из {payments.length}</p>
    </div>
    <div class="flex gap-3 w-full sm:w-auto">
      <select bind:value={statusFilter} class="select w-full sm:w-40">
        <option value="all">Все статусы</option>
        <option value="succeeded">Оплачен</option>
        <option value="pending">Ожидает</option>
        <option value="canceled">Отменён</option>
      </select>
      <input type="text" bind:value={search} placeholder="Поиск..." class="input w-full sm:w-60" />
    </div>
  </div>

  <Table columns={columns} data={filteredPayments}>
    {#snippet actions(row)}
      <span class="badge {statusBadge(row.status)}">{statusText(row.status)}</span>
    {/snippet}
  </Table>
</div>
