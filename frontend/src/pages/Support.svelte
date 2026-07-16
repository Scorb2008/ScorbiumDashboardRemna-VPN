<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDateTime } from '../lib/utils.js';
  import Table from '../components/Table.svelte';
  import Spinner from '../components/Spinner.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';
  import Icon from '../components/Icon.svelte';

  let tickets = $state([]);
  let loading = $state(true);
  let search = $state('');
  let statusFilter = $state('all');
  let confirmClose = $state(false);
  let closeTarget = $state(null);

  async function loadTickets() {
    loading = true;
    try { tickets = await api.getSupportTickets({ limit: 200 }); }
    catch (e) { toasts.error('Ошибка загрузки: ' + e.message); }
    finally { loading = false; }
  }

  onMount(loadTickets);

  let filteredTickets = $derived(
    tickets.filter(t => {
      const matchSearch = !search ||
        (t.user_username || '').toLowerCase().includes(search.toLowerCase()) ||
        (t.subject || '').toLowerCase().includes(search.toLowerCase()) ||
        String(t.id).includes(search);
      const matchStatus = statusFilter === 'all' || t.status === statusFilter;
      return matchSearch && matchStatus;
    })
  );

  function statusBadge(status) {
    switch (status) {
      case 'open': return 'badge-success';
      case 'answered': return 'badge-accent';
      case 'closed': return '';
      default: return '';
    }
  }

  function askClose(ticket) { closeTarget = ticket; confirmClose = true; }
  async function doClose() {
    if (!closeTarget) return;
    try { await api.closeTicket(closeTarget.id); toasts.success('Тикет закрыт'); await loadTickets(); }
    catch (e) { toasts.error(e.message); }
    confirmClose = false; closeTarget = null;
  }

  const columns = [
    { key: 'id', label: 'ID', sortable: true, render: (r) => `<span class="font-mono text-xs text-zinc-500">#${r.id}</span>` },
    { key: 'user_id', label: 'Пользователь', sortable: true, render: (r) => `<div><span class="font-medium">${r.user_full_name || '—'}</span><br><span class="text-xs text-muted">${r.user_username ? '@'+r.user_username : 'ID: '+r.user_id}</span></div>` },
    { key: 'subject', label: 'Тема', sortable: true, render: (r) => `<span class="font-medium">${r.subject || 'Без темы'}</span>` },
    { key: 'messages_count', label: 'Сообщений', sortable: true, render: (r) => `${r.messages_count ?? 0}` },
    { key: 'created_at', label: 'Создан', sortable: true, render: (r) => `<span class="text-xs text-muted">${formatDateTime(r.created_at)}</span>` },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">Поддержка</h1>
      <p class="text-sm text-muted mt-1">{filteredTickets.length} тикетов</p>
    </div>
    <div class="flex gap-3 w-full sm:w-auto">
      <select bind:value={statusFilter} class="select w-full sm:w-40">
        <option value="all">Все</option>
        <option value="open">Открытые</option>
        <option value="answered">Отвеченные</option>
        <option value="closed">Закрытые</option>
      </select>
      <input type="text" bind:value={search} placeholder="Поиск..." class="input w-full sm:w-60" />
    </div>
  </div>

  <Table columns={columns} data={filteredTickets}>
    {#snippet actions(row)}
      <span class="badge {statusBadge(row.status)}">{row.status === 'open' ? 'Открыт' : row.status === 'answered' ? 'Отвечен' : 'Закрыт'}</span>
      {#if row.status !== 'closed'}
        <button class="btn btn-ghost text-danger hover:text-danger-hover" onclick={() => askClose(row)} title="Закрыть"><Icon name="x-circle" class="w-3.5 h-3.5" /></button>
      {/if}
    {/snippet}
  </Table>
</div>

<ConfirmDialog bind:open={confirmClose} title="Закрыть тикет?" message={`Закрыть тикет #${closeTarget?.id}?`} confirmText="Закрыть" danger onConfirm={doClose} />
