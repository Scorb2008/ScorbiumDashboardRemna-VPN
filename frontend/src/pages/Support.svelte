<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.js';
  import { toasts } from '../lib/stores.js';
  import { formatDateTime, truncate } from '../lib/utils.js';
  import Modal from '../components/Modal.svelte';
  import Spinner from '../components/Spinner.svelte';

  let tickets = $state([]);
  let loading = $state(true);
  let statusFilter = $state('');
  let selectedTicket = $state(null);
  let showModal = $state(false);
  let replyText = $state('');
  let sendingReply = $state(false);

  async function loadTickets() {
    loading = true;
    try {
      tickets = await api.getTickets({ limit: 100, status: statusFilter || undefined });
    } catch (e) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  onMount(loadTickets);

  $effect(() => {
    statusFilter;
    loadTickets();
  });

  function openTicket(ticket) {
    selectedTicket = ticket;
    showModal = true;
  }

  async function handleReply() {
    if (!replyText.trim() || !selectedTicket) return;
    sendingReply = true;
    try {
      await api.replyTicket(selectedTicket.id, replyText);
      toasts.success('Ответ отправлен');
      replyText = '';
      selectedTicket = await api.getTicket(selectedTicket.id);
      await loadTickets();
    } catch (e) {
      toasts.error(e.message);
    } finally {
      sendingReply = false;
    }
  }

  async function handleClose() {
    if (!selectedTicket) return;
    try {
      await api.updateTicketStatus(selectedTicket.id, 'closed');
      toasts.success('Тикет закрыт');
      showModal = false;
      await loadTickets();
    } catch (e) {
      toasts.error(e.message);
    }
  }

  function statusBadge(status) {
    const map = { open: 'badge-warning', in_progress: 'badge-info', closed: 'badge-ghost' };
    return map[status] || 'badge-ghost';
  }

  function statusLabel(s) {
    const map = { open: 'Открыт', in_progress: 'В работе', closed: 'Закрыт' };
    return map[s] || s;
  }

  function priorityBadge(p) {
    const map = { low: 'badge-ghost', medium: 'badge-warning', high: 'badge-error' };
    return map[p] || 'badge-ghost';
  }
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold">Поддержка</h1>
      <p class="text-sm text-base-content/40 mt-1">{tickets.length} тикетов</p>
    </div>
    <select bind:value={statusFilter} class="select select-bordered select-sm input-glass">
      <option value="">Все статусы</option>
      <option value="open">Открытые</option>
      <option value="in_progress">В работе</option>
      <option value="closed">Закрытые</option>
    </select>
  </div>

  <div class="space-y-2">
    {#if tickets.length === 0}
      <div class="card p-12 text-center text-base-content/30">
        <svg class="w-12 h-12 mx-auto mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1"><path stroke-linecap="round" stroke-linejoin="round" d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
        <p>Нет тикетов</p>
      </div>
    {:else}
      {#each tickets as ticket, i (ticket.id)}
        <button
          class="card w-full p-4 text-left hover:shadow-lg hover:shadow-primary/5 transition-all animate-fade-in cursor-pointer"
          style="animation-delay: {i * 30}ms"
          onclick={() => openTicket(ticket)}>
          <div class="flex items-center gap-4">
            <div class="flex-shrink-0">
              <span class="badge badge-sm badge-glow {statusBadge(ticket.status)}">{statusLabel(ticket.status)}</span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <h3 class="font-medium truncate">{ticket.subject}</h3>
                <span class="badge badge-sm {priorityBadge(ticket.priority)}">{ticket.priority}</span>
              </div>
              <p class="text-xs text-base-content/40 mt-0.5">#{ticket.id} &middot; User #{ticket.user_id} &middot; {formatDateTime(ticket.created_at || ticket.messages?.[0]?.created_at)}</p>
            </div>
            <div class="flex-shrink-0 text-base-content/20">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
            </div>
          </div>
        </button>
      {/each}
    {/if}
  </div>
</div>

<Modal bind:open={showModal} title={selectedTicket?.subject || 'Тикет'} size="lg">
  {#if selectedTicket}
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <span class="text-sm text-base-content/50">#{selectedTicket.id} &middot; User #{selectedTicket.user_id}</span>
        <div class="flex gap-2">
          <span class="badge badge-sm {priorityBadge(selectedTicket.priority)}">{selectedTicket.priority}</span>
          {#if selectedTicket.status !== 'closed'}
            <button class="btn btn-xs btn-ghost text-error" onclick={handleClose}>Закрыть тикет</button>
          {/if}
        </div>
      </div>

      <div class="divider my-0"></div>

      <div class="space-y-3 max-h-64 overflow-y-auto">
        {#each selectedTicket.messages || [] as msg}
          <div class="p-3 rounded-xl {msg.is_admin ? 'bg-primary/5 border border-primary/10 ml-8' : 'bg-base-300/50 mr-8'}">
            <div class="text-xs text-base-content/40 mb-1">
              {msg.is_admin ? 'Админ' : 'Пользователь'} &middot; {formatDateTime(msg.created_at)}
            </div>
            <p class="text-sm whitespace-pre-wrap">{msg.text}</p>
          </div>
        {/each}
      </div>

      {#if selectedTicket.status !== 'closed'}
        <div class="divider my-0"></div>
        <div class="flex gap-2">
          <textarea
            bind:value={replyText}
            class="textarea textarea-bordered input-glass flex-1 h-20"
            placeholder="Ваш ответ..."
            onkeydown={(e) => { if (e.key === 'Enter' && e.ctrlKey) handleReply(); }}></textarea>
          <button
            class="btn btn-primary btn-glow self-end"
            disabled={!replyText.trim() || sendingReply}
            onclick={handleReply}>
            {#if sendingReply}
              <span class="loading loading-spinner loading-sm"></span>
            {:else}
              Отправить
            {/if}
          </button>
        </div>
        <p class="text-xs text-base-content/30">Ctrl+Enter для отправки</p>
      {/if}
    </div>
  {/if}
</Modal>
