<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDateTime } from '../lib/utils.js';
  import Table from '../components/Table.svelte';
  import Spinner from '../components/Spinner.svelte';
  import Modal from '../components/Modal.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';
  import Icon from '../components/Icon.svelte';

  let tickets = $state([]);
  let loading = $state(true);
  let search = $state('');
  let statusFilter = $state('all');
  let confirmClose = $state(false);
  let closeTarget = $state(null);

  let selectedTicket = $state(null);
  let ticketDetail = $state(null);
  let replyText = $state('');
  let sendingReply = $state(false);
  let showTicketModal = $state(false);
  let detailLoading = $state(false);

  let showCreateModal = $state(false);
  let createForm = $state({ user_id: '', subject: '', text: '', priority: 'medium' });

  async function loadTickets() {
    loading = true;
    try { tickets = await api.getTickets({ limit: 200 }); }
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
      case 'closed': return 'badge-neutral';
      default: return '';
    }
  }
  function statusText(status) {
    switch (status) { case 'open': return 'Открыт'; case 'answered': return 'Отвечен'; case 'closed': return 'Закрыт'; default: return status; }
  }

  function priorityBadge(p) {
    switch (p) {
      case 'high': return 'badge-danger';
      case 'medium': return 'badge-warning';
      case 'low': return 'badge-neutral';
      default: return '';
    }
  }

  function askClose(ticket) { closeTarget = ticket; confirmClose = true; }

  async function doClose() {
    if (!closeTarget) return;
    try {
      await api.updateTicketStatus(closeTarget.id, 'closed');
      toasts.success('Тикет закрыт');
      await loadTickets();
      if (selectedTicket?.id === closeTarget.id) ticketDetail.status = 'closed';
    } catch (e) { toasts.error(e.message); }
    confirmClose = false; closeTarget = null;
  }

  async function openTicket(ticket) {
    selectedTicket = ticket;
    showTicketModal = true;
    detailLoading = true;
    replyText = '';
    try {
      ticketDetail = await api.getTicket(ticket.id);
    } catch (e) { toasts.error('Ошибка загрузки тикета'); }
    finally { detailLoading = false; }
  }

  async function sendReply() {
    if (!replyText.trim() || !selectedTicket) return;
    sendingReply = true;
    try {
      await api.replyTicket(selectedTicket.id, replyText.trim(), true);
      toasts.success('Ответ отправлен');
      replyText = '';
      ticketDetail = await api.getTicket(selectedTicket.id);
      await loadTickets();
    } catch (e) { toasts.error('Ошибка: ' + e.message); }
    finally { sendingReply = false; }
  }

  async function changePriority(ticketId, priority) {
    try {
      await api.updateTicketPriority(ticketId, priority);
      toasts.success('Приоритет изменён');
      ticketDetail = await api.getTicket(ticketId);
      await loadTickets();
    } catch (e) { toasts.error(e.message); }
  }

  async function createTicket() {
    try {
      await api.createTicket(createForm);
      toasts.success('Тикет создан');
      showCreateModal = false;
      createForm = { user_id: '', subject: '', text: '', priority: 'medium' };
      await loadTickets();
    } catch (e) { toasts.error(e.message); }
  }

  const columns = [
    { key: 'id', label: 'ID', sortable: true, render: (r) => `<span class="font-mono text-xs text-muted">#${r.id}</span>` },
    { key: 'user_id', label: 'Пользователь', sortable: true, render: (r) => `<div><span class="font-medium text-[13px]">${r.user_full_name || '—'}</span><br><span class="text-xs text-muted">${r.user_username ? '@'+r.user_username : 'ID: '+r.user_id}</span></div>` },
    { key: 'subject', label: 'Тема', sortable: true, render: (r) => `<span class="font-medium text-[13px]">${r.subject || 'Без темы'}</span>` },
    { key: 'priority', label: 'Приоритет', sortable: true, render: (r) => `<span class="badge ${priorityBadge(r.priority)}">${r.priority || '—'}</span>` },
    { key: 'created_at', label: 'Создан', sortable: true, render: (r) => `<span class="text-xs text-muted">${formatDateTime(r.created_at)}</span>` },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight text-text">Поддержка</h1>
      <p class="text-sm text-muted mt-1">{filteredTickets.length} тикетов</p>
    </div>
    <div class="flex gap-2.5 w-full sm:w-auto">
      <button class="btn btn-primary" onclick={() => showCreateModal = true}>
        <Icon name="plus" class="w-4 h-4" />
        Новый тикет
      </button>
      <select bind:value={statusFilter} class="select w-full sm:w-36">
        <option value="all">Все</option>
        <option value="open">Открытые</option>
        <option value="answered">Отвеченные</option>
        <option value="closed">Закрытые</option>
      </select>
      <input type="text" bind:value={search} placeholder="Поиск..." class="input w-full sm:w-48" />
    </div>
  </div>

  <Table columns={columns} data={filteredTickets} onRowClick={openTicket}>
    {#snippet actions(row)}
      <span class="badge {statusBadge(row.status)}">{statusText(row.status)}</span>
      <button class="btn btn-xs btn-ghost {row.status !== 'closed' ? 'text-danger hover:text-danger-hover' : 'text-muted'}" onclick={(e) => { e.stopPropagation(); if (row.status !== 'closed') askClose(row); }} disabled={row.status === 'closed'} title="Закрыть">
        <Icon name="x-circle" class="w-3.5 h-3.5" />
      </button>
    {/snippet}
  </Table>
</div>

<Modal bind:open={showTicketModal} title={ticketDetail?.subject || 'Тикет'} size="lg">
  {#if detailLoading}
    <div class="flex justify-center py-10">
      <div class="w-6 h-6 border-2 border-surface-4 border-t-accent rounded-full animate-spin"></div>
    </div>
  {:else if ticketDetail}
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <span class="badge {statusBadge(ticketDetail.status)}">{statusText(ticketDetail.status)}</span>
          <button class="btn btn-xs btn-ghost" onclick={() => {
            const priorities = ['low', 'medium', 'high'];
            const idx = priorities.indexOf(ticketDetail.priority);
            const next = priorities[(idx + 1) % 3];
            changePriority(ticketDetail.id, next);
          }}>
            <span class="badge {priorityBadge(ticketDetail.priority)}">{ticketDetail.priority || 'medium'}</span>
          </button>
        </div>
        <span class="text-xs text-muted">{formatDateTime(ticketDetail.created_at)}</span>
      </div>

      <div class="flex items-center gap-2.5 pb-2 border-b border-border">
        <div class="w-7 h-7 rounded-[7px] bg-accent/10 flex items-center justify-center text-xs font-bold text-accent">
          {(ticketDetail.user_full_name || ticketDetail.user_username || '?')[0].toUpperCase()}
        </div>
        <div>
          <p class="text-[13px] font-medium">{ticketDetail.user_full_name || '—'}</p>
          <p class="text-[11px] text-muted">{ticketDetail.user_username ? '@'+ticketDetail.user_username : 'ID: '+ticketDetail.user_id}</p>
        </div>
      </div>

      {#if ticketDetail.messages?.length}
        <div class="space-y-3 max-h-80 overflow-y-auto pr-1">
          {#each ticketDetail.messages as msg}
            <div class="flex gap-3 {msg.is_admin ? 'flex-row-reverse' : ''}">
              <div class="w-7 h-7 rounded-full bg-surface-3 flex items-center justify-center text-[10px] font-bold flex-shrink-0">
                {msg.is_admin ? 'A' : 'U'}
              </div>
              <div class="max-w-[80%] {msg.is_admin ? 'bg-accent/10' : 'bg-surface-3'} rounded-[10px] px-3.5 py-2.5">
                <p class="text-[13px]">{msg.text}</p>
                <p class="text-[10px] text-muted mt-1">{formatDateTime(msg.created_at)}</p>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <p class="text-sm text-muted text-center py-6">Нет сообщений</p>
      {/if}

      {#if ticketDetail.status !== 'closed'}
        <div class="border-t border-border pt-3 space-y-2.5">
          <textarea bind:value={replyText} class="textarea w-full h-24" placeholder="Напишите ответ пользователю..."></textarea>
          <div class="flex justify-between items-center">
            <button class="btn btn-ghost btn-sm text-danger" onclick={() => askClose(ticketDetail)}>
              <Icon name="x-circle" class="w-3.5 h-3.5" />
              Закрыть тикет
            </button>
            <button class="btn btn-primary" onclick={sendReply} disabled={!replyText.trim() || sendingReply}>
              {#if sendingReply}
                <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              {:else}
                <Icon name="send" class="w-4 h-4" />
              {/if}
              Отправить
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</Modal>

<Modal bind:open={showCreateModal} title="Новый тикет">
  <form class="space-y-3.5" onsubmit={(e) => { e.preventDefault(); createTicket(); }}>
    <div class="space-y-1">
      <label class="label">ID пользователя</label>
      <input type="number" bind:value={createForm.user_id} class="input w-full" placeholder="ID пользователя" required />
    </div>
    <div class="space-y-1">
      <label class="label">Тема</label>
      <input type="text" bind:value={createForm.subject} class="input w-full" placeholder="Тема обращения" required />
    </div>
    <div class="space-y-1">
      <label class="label">Приоритет</label>
      <select bind:value={createForm.priority} class="select w-full">
        <option value="low">Низкий</option>
        <option value="medium">Средний</option>
        <option value="high">Высокий</option>
      </select>
    </div>
    <div class="space-y-1">
      <label class="label">Текст</label>
      <textarea bind:value={createForm.text} class="textarea w-full h-28" placeholder="Описание проблемы..." required></textarea>
    </div>
    <div class="flex gap-3 pt-1">
      <button type="button" class="btn btn-secondary flex-1" onclick={() => showCreateModal = false}>Отмена</button>
      <button type="submit" class="btn btn-primary flex-1">Создать</button>
    </div>
  </form>
</Modal>

<ConfirmDialog bind:open={confirmClose} title="Закрыть тикет?" message={`Закрыть тикет #${closeTarget?.id}? Пользователь больше не сможет отвечать.`} confirmText="Закрыть" danger onConfirm={doClose} />
