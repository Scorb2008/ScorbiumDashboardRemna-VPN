<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.js';
  import { toasts } from '../lib/stores.js';
  import Spinner from '../components/Spinner.svelte';
  import Modal from '../components/Modal.svelte';

  let tickets = $state([]);
  let loading = $state(true);
  let filter = $state('all');
  let showReplyModal = $state(false);
  let selectedTicket = $state(null);
  let replyText = $state('');

  onMount(loadTickets);

  async function loadTickets() {
    loading = true;
    try {
      const params = { limit: 100 };
      if (filter !== 'all') params.status = filter;
      tickets = await api.getTickets(params);
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    } finally {
      loading = false;
    }
  }

  async function openTicket(ticket) {
    try {
      selectedTicket = await api.getTicket(ticket.id);
      showReplyModal = true;
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    }
  }

  async function handleReply() {
    if (!replyText.trim()) return;
    try {
      await api.replyTicket(selectedTicket.id, replyText);
      toasts.success('Ответ отправлен');
      replyText = '';
      showReplyModal = false;
      await loadTickets();
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    }
  }

  async function changeStatus(ticket, status) {
    try {
      await api.updateTicketStatus(ticket.id, status);
      toasts.success('Статус обновлён');
      await loadTickets();
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    }
  }

  function statusBadge(status) {
    const map = {
      open: 'badge-warning',
      in_progress: 'badge-info',
      closed: 'badge-ghost',
    };
    return map[status] || 'badge-ghost';
  }

  function priorityBadge(priority) {
    const map = {
      low: 'badge-ghost',
      medium: 'badge-warning',
      high: 'badge-error',
      critical: 'badge-error',
    };
    return map[priority] || 'badge-ghost';
  }

  $effect(() => {
    filter;
    loadTickets();
  });
</script>

<div class="fade-in">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">Поддержка</h1>
    <select bind:value={filter} class="select select-bordered select-sm">
      <option value="all">Все</option>
      <option value="open">Открытые</option>
      <option value="in_progress">В работе</option>
      <option value="closed">Закрытые</option>
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
              <th>Тема</th>
              <th>Пользователь</th>
              <th>Приоритет</th>
              <th>Статус</th>
              <th>Дата</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {#if tickets.length === 0}
              <tr>
                <td colspan="7" class="text-center py-8 text-base-content/40">Нет тикетов</td>
              </tr>
            {:else}
              {#each tickets as t (t.id)}
                <tr class="fade-in">
                  <td class="font-mono text-sm">#{t.id}</td>
                  <td class="font-medium max-w-[200px] truncate">{t.subject}</td>
                  <td>{t.user_id}</td>
                  <td><span class="badge badge-sm {priorityBadge(t.priority)}">{t.priority}</span></td>
                  <td><span class="badge badge-sm {statusBadge(t.status)}">{t.status}</span></td>
                  <td class="text-sm">{t.created_at ? new Date(t.created_at).toLocaleString('ru-RU') : '—'}</td>
                  <td>
                    <div class="flex gap-1">
                      <button class="btn btn-xs btn-ghost" onclick={() => openTicket(t)}>Ответить</button>
                      {#if t.status !== 'closed'}
                        <button class="btn btn-xs btn-ghost" onclick={() => changeStatus(t, 'closed')}>Закрыть</button>
                      {/if}
                    </div>
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

<Modal bind:open={showReplyModal} title="Тикет #{selectedTicket?.id}: {selectedTicket?.subject}" size="lg">
  {#if selectedTicket}
    <div class="space-y-4">
      {#if selectedTicket.messages}
        <div class="space-y-3 max-h-64 overflow-y-auto">
          {#each selectedTicket.messages as msg}
              <div class="p-3 rounded-lg {msg.from_user ? 'bg-base-300' : 'bg-primary/10'}">
              <div class="text-xs text-base-content/40 mb-1">
                {msg.from_user ? 'Пользователь' : 'Админ'} · {msg.created_at}
              </div>
              <div class="text-sm">{msg.text}</div>
            </div>
          {/each}
        </div>
        <div class="divider"></div>
      {/if}
      <div class="form-control">
        <label class="label"><span class="label-text">Ответ</span></label>
        <textarea
          bind:value={replyText}
          class="textarea textarea-bordered h-24"
          placeholder="Напишите ответ..."></textarea>
      </div>
      <div class="flex justify-end">
        <button class="btn btn-primary btn-sm" onclick={handleReply} disabled={!replyText.trim()}>
          Отправить
        </button>
      </div>
    </div>
  {/if}
</Modal>
