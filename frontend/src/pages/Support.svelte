<script>
  import { onMount, tick } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDateTime } from '../lib/utils.js';
  import Modal from '../components/Modal.svelte';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';

  let tickets = $state([]);
  let loading = $state(true);
  let search = $state('');
  let statusFilter = $state('all');

  let activeTicketId = $state(null);
  let selectedTicket = $state(null);
  let messages = $state([]);
  let detailLoading = $state(false);

  let replyText = $state('');
  let isSending = $state(false);
  let sendCooldown = $state(false);

  let showCreateModal = $state(false);
  let createForm = $state({ user_id: '', subject: '', text: '', priority: 'medium' });
  let users = $state([]);
  let usersLoading = $state(false);
  let userSearch = $state('');

  let messagesContainer;

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

  let filteredUsers = $derived(
    userSearch
      ? users.filter(u =>
          (u.username || '').toLowerCase().includes(userSearch.toLowerCase()) ||
          (u.full_name || '').toLowerCase().includes(userSearch.toLowerCase()) ||
          String(u.id).includes(userSearch))
      : users
  );

  function statusBadge(status) {
    switch (status) {
      case 'open': return 'bg-[#22c55e]/20 text-[#22c55e]';
      case 'in_progress': return 'bg-[#5b8def]/20 text-[#5b8def]';
      case 'closed': return 'bg-zinc-500/20 text-zinc-400';
      default: return 'bg-zinc-500/20 text-zinc-400';
    }
  }

  function statusText(status) {
    switch (status) {
      case 'open': return 'Открыт';
      case 'in_progress': return 'В работе';
      case 'closed': return 'Закрыт';
      default: return status;
    }
  }

  function priorityBadge(p) {
    switch (p) {
      case 'high': return 'bg-[#ef4450]/20 text-[#ef4450]';
      case 'medium': return 'bg-[#eab308]/20 text-[#eab308]';
      case 'low': return 'bg-zinc-500/20 text-zinc-400';
      default: return 'bg-zinc-500/20 text-zinc-400';
    }
  }

  function priorityText(p) {
    switch (p) {
      case 'high': return 'Высокий';
      case 'medium': return 'Средний';
      case 'low': return 'Низкий';
      default: return p;
    }
  }

  async function loadTickets() {
    loading = true;
    try { tickets = await api.getTickets({ limit: 200 }); }
    catch (e) { toasts.error('Ошибка загрузки: ' + e.message); }
    finally { loading = false; }
  }

  onMount(loadTickets);

  async function selectTicket(ticket) {
    activeTicketId = ticket.id;
    selectedTicket = ticket;
    detailLoading = true;
    replyText = '';
    try {
      const detail = await api.getTicket(ticket.id);
      selectedTicket = detail;
      messages = detail.messages || [];
      await tick();
      requestAnimationFrame(scrollToBottom);
    } catch (e) {
      toasts.error('Ошибка загрузки: ' + e.message);
      messages = [];
    } finally {
      detailLoading = false;
    }
  }

  function scrollToBottom() {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  async function sendReply() {
    if (!replyText.trim() || !activeTicketId || isSending || sendCooldown) return;
    isSending = true;
    try {
      const updated = await api.replyTicket(activeTicketId, replyText.trim(), true);
      replyText = '';
      messages = updated.messages || [];
      selectedTicket = updated;
      await tick();
      requestAnimationFrame(scrollToBottom);
      sendCooldown = true;
      setTimeout(() => { sendCooldown = false; }, 1000);
      await loadTickets();
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    } finally {
      isSending = false;
    }
  }

  function handleKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendReply();
    }
  }

  async function toggleStatus() {
    if (!selectedTicket) return;
    const newStatus = selectedTicket.status === 'closed' ? 'open' : 'closed';
    try {
      const updated = await api.updateTicketStatus(selectedTicket.id, newStatus);
      selectedTicket = updated;
      messages = updated.messages || [];
      toasts.success(newStatus === 'closed' ? 'Тикет закрыт' : 'Тикет открыт');
      await loadTickets();
    } catch (e) {
      toasts.error(e.message);
    }
  }

  async function cyclePriority() {
    if (!selectedTicket) return;
    const priorities = ['low', 'medium', 'high'];
    const idx = priorities.indexOf(selectedTicket.priority);
    const next = priorities[(idx + 1) % 3];
    try {
      const updated = await api.updateTicketPriority(selectedTicket.id, next);
      selectedTicket = updated;
      messages = updated.messages || [];
      toasts.success('Приоритет изменён');
      await loadTickets();
    } catch (e) {
      toasts.error(e.message);
    }
  }

  async function openCreateModal() {
    showCreateModal = true;
    usersLoading = true;
    userSearch = '';
    createForm = { user_id: '', subject: '', text: '', priority: 'medium' };
    try {
      users = await api.getUsers({ limit: 500 });
    } catch (e) {
      toasts.error('Ошибка загрузки пользователей');
    } finally {
      usersLoading = false;
    }
  }

  async function createTicket() {
    if (!createForm.user_id || !createForm.text.trim() || !createForm.subject.trim()) return;
    try {
      const data = {
        user_id: parseInt(createForm.user_id),
        subject: createForm.subject.trim(),
        text: createForm.text.trim(),
        priority: createForm.priority
      };
      const newTicket = await api.createTicket(data);
      toasts.success('Тикет создан');
      showCreateModal = false;
      await loadTickets();
      await selectTicket(newTicket);
    } catch (e) {
      toasts.error(e.message);
    }
  }

  function selectUser(user) {
    createForm.user_id = user.id;
  }
</script>

<Spinner {loading} />

<div class="page-enter flex flex-col lg:flex-row gap-4 h-auto lg:h-[calc(100vh-7rem)]">
  <!-- Left: Chat Panel -->
  <div class="flex-[2] min-w-0 flex flex-col bg-[#16161d] rounded-[14px] border border-zinc-800/50 overflow-hidden {activeTicketId ? 'min-h-[60vh] lg:min-h-0' : 'min-h-[40vh] lg:min-h-0'}">
    {#if activeTicketId && selectedTicket}
      <!-- Chat Header -->
      <div class="flex items-center gap-3 px-5 py-3.5 border-b border-zinc-800/50 bg-[#0d0d12]/50 shrink-0">
        <div class="w-9 h-9 rounded-[10px] bg-gradient-to-br from-[#5b8def] to-[#5b8def]/60 flex items-center justify-center text-sm font-bold text-white shrink-0">
          {(selectedTicket.user_full_name || selectedTicket.user_username || '?')[0].toUpperCase()}
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="text-[14px] font-semibold truncate">{selectedTicket.user_full_name || '—'}</span>
            {#if selectedTicket.user_username}
              <span class="text-[12px] text-zinc-500 font-mono">@{selectedTicket.user_username}</span>
            {/if}
          </div>
          <div class="flex items-center gap-2 mt-0.5">
            <span class="text-[11px] leading-none px-1.5 py-0.5 rounded-md font-medium {statusBadge(selectedTicket.status)}">{statusText(selectedTicket.status)}</span>
            <button onclick={cyclePriority} class="text-[11px] leading-none px-1.5 py-0.5 rounded-md font-medium {priorityBadge(selectedTicket.priority)} hover:opacity-80 transition-opacity cursor-pointer">
              {priorityText(selectedTicket.priority)}
            </button>
          </div>
        </div>
        <button
          onclick={toggleStatus}
          class="shrink-0 px-3 py-1.5 rounded-lg text-[12px] font-medium transition-colors {selectedTicket.status === 'closed' ? 'bg-[#22c55e]/20 text-[#22c55e] hover:bg-[#22c55e]/30' : 'bg-zinc-500/20 text-zinc-400 hover:bg-zinc-500/30'}">
          <span class="flex items-center gap-1.5">
            <Icon name={selectedTicket.status === 'closed' ? 'check' : 'x'} size={13} />
            {selectedTicket.status === 'closed' ? 'Открыть' : 'Закрыть'}
          </span>
        </button>
      </div>

      <!-- Messages Area -->
      <div
        bind:this={messagesContainer}
        class="flex-1 overflow-y-auto px-4 py-4 space-y-3 scroll-smooth"
        class:flex={detailLoading}
        class:items-center={detailLoading}
        class:justify-center={detailLoading}>
        {#if detailLoading}
          <div class="w-6 h-6 border-2 border-zinc-600 border-t-[#5b8def] rounded-full animate-spin"></div>
        {:else if messages.length === 0}
          <div class="flex flex-col items-center justify-center h-full text-zinc-500">
            <Icon name="messageSquare" size={40} class="opacity-30 mb-3" />
            <p class="text-sm">Нет сообщений</p>
          </div>
        {:else}
          {#each messages as msg, idx}
            {@const isAdmin = !!msg.is_admin}
            <div class="flex {isAdmin ? 'justify-end' : 'justify-start'} items-end gap-2" style="animation: msgIn 0.2s ease-out both; animation-delay: {Math.min(idx * 15, 200)}ms">
              {#if !isAdmin}
                <div class="w-6 h-6 rounded-full bg-[#16161d] border border-zinc-700/50 flex items-center justify-center text-[9px] font-bold text-zinc-400 shrink-0">
                  U
                </div>
              {/if}
              <div class="max-w-[80%] min-w-0 {isAdmin ? 'order-1' : ''}">
                <div
                  class="px-3.5 py-2.5 rounded-2xl break-words text-[13px] leading-relaxed shadow-sm {isAdmin ? 'bg-[#5b8def] text-white rounded-br-md' : 'bg-[#16161d] border border-zinc-800 text-zinc-200 rounded-bl-md'}">
                  <p>{msg.text}</p>
                </div>
                <div class="flex items-center gap-1 mt-0.5 px-1 {isAdmin ? 'justify-end' : 'justify-start'}">
                  <span class="text-[9px] text-zinc-600">{formatDateTime(msg.created_at)}</span>
                  {#if isAdmin}
                    <span class="text-[9px] text-zinc-600 flex items-center gap-0.5">
                      <Icon name="check" size={9} class="text-[#5b8def]" />
                    </span>
                  {/if}
                </div>
              </div>
              {#if isAdmin}
                <div class="w-6 h-6 rounded-full bg-[#5b8def]/20 border border-[#5b8def]/30 flex items-center justify-center text-[9px] font-bold text-[#5b8def] shrink-0">
                  A
                </div>
              {/if}
            </div>
          {/each}
        {/if}
      </div>

      <!-- Reply Input -->
      {#if selectedTicket.status !== 'closed'}
        <div class="border-t border-zinc-800/50 bg-[#0d0d12]/50 p-3 shrink-0">
          <div class="flex items-end gap-2">
            <textarea
              bind:value={replyText}
              onkeydown={handleKeydown}
              class="flex-1 bg-[#16161d] border border-zinc-700/50 rounded-xl px-3.5 py-2.5 text-[13px] text-zinc-200 placeholder-zinc-600 resize-none outline-none focus:border-[#5b8def]/50 focus:ring-1 focus:ring-[#5b8def]/30 transition-all min-h-[40px] max-h-[120px]"
              placeholder="Напишите ответ..."
              rows="1"
              oninput={(e) => { e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'; }}>
            </textarea>
            <button
              onclick={sendReply}
              disabled={!replyText.trim() || isSending || sendCooldown}
              class="shrink-0 w-[38px] h-[38px] rounded-xl flex items-center justify-center transition-all disabled:opacity-40 disabled:cursor-not-allowed {replyText.trim() && !isSending && !sendCooldown ? 'bg-[#5b8def] hover:bg-[#5b8def]/80 text-white shadow-sm' : 'bg-zinc-800 text-zinc-500'}">
              {#if isSending}
                <div class="w-4 h-4 border-2 border-zinc-400 border-t-white rounded-full animate-spin"></div>
              {:else}
                <Icon name="send" size={16} />
              {/if}
            </button>
          </div>
        </div>
      {:else}
        <div class="border-t border-zinc-800/50 bg-[#0d0d12]/30 p-3 shrink-0 text-center">
          <p class="text-[12px] text-zinc-500">Тикет закрыт. Нажмите "Открыть" чтобы возобновить переписку.</p>
        </div>
      {/if}
    {:else}
      <!-- No ticket selected -->
      <div class="flex-1 flex flex-col items-center justify-center text-zinc-600 gap-4">
        <div class="w-16 h-16 rounded-full bg-zinc-800/50 flex items-center justify-center">
          <Icon name="messageSquare" size={32} class="opacity-40" />
        </div>
        <div class="text-center">
          <p class="text-[17px] font-medium text-zinc-400">Выберите тикет</p>
          <p class="text-[13px] text-zinc-600 mt-1">Выберите обращение из списка</p>
        </div>
      </div>
    {/if}
  </div>

  <!-- Right: Ticket List Panel -->
  <div class="flex-1 flex flex-col bg-[#16161d] rounded-[14px] border border-zinc-800/50 overflow-hidden {activeTicketId ? 'max-h-[40vh] lg:max-h-none' : ''}">
    <!-- Panel Header -->
    <div class="px-4 py-3.5 border-b border-zinc-800/50 shrink-0 space-y-3">
      <div class="flex items-center justify-between gap-2">
        <h2 class="text-[15px] font-semibold">Тикеты</h2>
        <button onclick={openCreateModal} class="px-3 py-1.5 rounded-lg text-[12px] font-medium bg-[#5b8def] text-white hover:bg-[#5b8def]/80 transition-colors flex items-center gap-1.5">
          <Icon name="plus" size={14} />
          Создать
        </button>
      </div>
      <div class="flex gap-2">
        <div class="relative flex-1">
          <div class="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-600 pointer-events-none">
            <Icon name="search" size={14} />
          </div>
          <input type="text" bind:value={search} placeholder="Поиск..." class="w-full bg-[#0d0d12] border border-zinc-800 rounded-lg pl-8 pr-3 py-1.5 text-[13px] text-zinc-300 placeholder-zinc-600 outline-none focus:border-[#5b8def]/40 transition-colors" />
        </div>
        <select bind:value={statusFilter} class="bg-[#0d0d12] border border-zinc-800 rounded-lg px-2.5 py-1.5 text-[13px] text-zinc-300 outline-none focus:border-[#5b8def]/40 transition-colors cursor-pointer">
          <option value="all">Все</option>
          <option value="open">Открытые</option>
          <option value="in_progress">В работе</option>
          <option value="closed">Закрытые</option>
        </select>
      </div>
    </div>

    <!-- Ticket List -->
    <div class="flex-1 overflow-y-auto divide-y divide-zinc-800/30">
      {#if filteredTickets.length === 0}
        <div class="flex flex-col items-center justify-center h-full text-zinc-600 gap-3 p-8">
          <Icon name="ticket" size={32} class="opacity-30" />
          <p class="text-sm">Тикеты не найдены</p>
        </div>
      {:else}
        {#each filteredTickets as ticket (ticket.id)}
          <button
            onclick={() => selectTicket(ticket)}
            class="w-full text-left px-4 py-3 transition-colors hover:bg-zinc-800/30 {activeTicketId === ticket.id ? 'bg-[#5b8def]/10 border-l-2 border-l-[#5b8def]' : 'border-l-2 border-l-transparent'}">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <span class="text-[11px] font-mono text-zinc-500 shrink-0">#{ticket.id}</span>
                  <span class="text-[13px] font-medium truncate">{ticket.subject || 'Без темы'}</span>
                </div>
                <div class="flex items-center gap-1.5 mt-1">
                  <div class="w-5 h-5 rounded-full bg-gradient-to-br from-[#5b8def] to-[#5b8def]/60 flex items-center justify-center text-[7px] font-bold text-white shrink-0">
                    {(ticket.user_full_name || ticket.user_username || '?')[0].toUpperCase()}
                  </div>
                  <span class="text-[12px] text-zinc-400 truncate">{ticket.user_full_name || '—'}</span>
                  {#if ticket.user_username}
                    <span class="text-[11px] text-zinc-600 font-mono">@{ticket.user_username}</span>
                  {/if}
                </div>
              </div>
              <div class="flex flex-col items-end gap-1 shrink-0">
                <span class="text-[10px] leading-none px-1.5 py-0.5 rounded-md font-medium {statusBadge(ticket.status)}">{statusText(ticket.status)}</span>
                <span class="text-[10px] leading-none px-1.5 py-0.5 rounded-md font-medium {priorityBadge(ticket.priority)}">{priorityText(ticket.priority)}</span>
              </div>
            </div>
            <div class="mt-1.5 flex items-center justify-between">
              {#if ticket.messages?.length}
                <span class="text-[11px] text-zinc-600">{ticket.messages.length} сообщ.</span>
              {:else}
                <span></span>
              {/if}
              <span class="text-[10px] text-zinc-600">{formatDateTime(ticket.created_at)}</span>
            </div>
          </button>
        {/each}
      {/if}
    </div>
  </div>
</div>

<!-- Create Ticket Modal -->
<Modal bind:open={showCreateModal} title="Создать тикет" size="lg">
  <div class="space-y-4">
    <div class="space-y-1.5">
      <label class="text-[13px] text-zinc-400 font-medium">Пользователь</label>
      <input
        type="text"
        bind:value={userSearch}
        placeholder="Поиск пользователя..."
        class="w-full bg-[#0d0d12] border border-zinc-800 rounded-lg px-3 py-2 text-[13px] text-zinc-300 placeholder-zinc-600 outline-none focus:border-[#5b8def]/40 transition-colors" />
      {#if usersLoading}
        <div class="flex items-center justify-center py-6">
          <div class="w-5 h-5 border-2 border-zinc-600 border-t-[#5b8def] rounded-full animate-spin"></div>
        </div>
      {:else}
        <div class="max-h-40 overflow-y-auto space-y-0.5 rounded-lg border border-zinc-800/50 {createForm.user_id ? 'opacity-60 pointer-events-none' : ''}">
          {#if filteredUsers.length === 0}
            <p class="text-[12px] text-zinc-600 text-center py-4">Пользователи не найдены</p>
          {:else}
            {#each filteredUsers as user}
              <button
                onclick={() => selectUser(user)}
                class="w-full text-left flex items-center gap-2.5 px-3 py-2 transition-colors hover:bg-zinc-800/40 {createForm.user_id === user.id ? 'bg-[#5b8def]/10' : ''}">
                <div class="w-7 h-7 rounded-[8px] bg-gradient-to-br from-[#5b8def] to-[#5b8def]/60 flex items-center justify-center text-[10px] font-bold text-white shrink-0">
                  {(user.full_name || user.username || '?')[0].toUpperCase()}
                </div>
                <div class="min-w-0 flex-1">
                  <div class="text-[13px] font-medium truncate">{user.full_name || 'Без имени'}</div>
                  <div class="text-[11px] text-zinc-500">@{user.username || ('ID: ' + user.id)}</div>
                </div>
                {#if createForm.user_id === user.id}
                  <Icon name="check" size={14} class="text-[#22c55e] shrink-0" />
                {/if}
              </button>
            {/each}
          {/if}
        </div>
        {#if createForm.user_id}
          <div class="flex items-center justify-between bg-[#5b8def]/10 border border-[#5b8def]/20 rounded-lg px-3 py-2">
            <span class="text-[13px] text-zinc-300">Пользователь выбран (ID: {createForm.user_id})</span>
            <button onclick={() => { createForm.user_id = ''; userSearch = ''; }} class="text-[11px] text-zinc-500 hover:text-[#ef4450]">
              <Icon name="x" size={14} />
            </button>
          </div>
        {/if}
      {/if}
    </div>

    <div class="space-y-1.5">
      <label class="text-[13px] text-zinc-400 font-medium">Тема</label>
      <input
        type="text"
        bind:value={createForm.subject}
        placeholder="Краткое описание проблемы"
        class="w-full bg-[#0d0d12] border border-zinc-800 rounded-lg px-3 py-2 text-[13px] text-zinc-300 placeholder-zinc-600 outline-none focus:border-[#5b8def]/40 transition-colors" />
    </div>

    <div class="space-y-1.5">
      <label class="text-[13px] text-zinc-400 font-medium">Сообщение</label>
      <textarea
        bind:value={createForm.text}
        placeholder="Опишите проблему подробнее..."
        class="w-full bg-[#0d0d12] border border-zinc-800 rounded-lg px-3 py-2 text-[13px] text-zinc-300 placeholder-zinc-600 outline-none focus:border-[#5b8def]/40 transition-colors resize-none h-24"></textarea>
    </div>

    <div class="space-y-1.5">
      <label class="text-[13px] text-zinc-400 font-medium">Приоритет</label>
      <select bind:value={createForm.priority} class="w-full bg-[#0d0d12] border border-zinc-800 rounded-lg px-3 py-2 text-[13px] text-zinc-300 outline-none focus:border-[#5b8def]/40 transition-colors cursor-pointer">
        <option value="low">Низкий</option>
        <option value="medium">Средний</option>
        <option value="high">Высокий</option>
      </select>
    </div>

    <div class="flex gap-3 pt-2">
      <button onclick={() => { showCreateModal = false; }} class="flex-1 px-4 py-2 rounded-lg text-[13px] font-medium bg-zinc-800 text-zinc-400 hover:bg-zinc-700 transition-colors">
        Отмена
      </button>
      <button
        onclick={createTicket}
        disabled={!createForm.user_id || !createForm.subject.trim() || !createForm.text.trim()}
        class="flex-1 px-4 py-2 rounded-lg text-[13px] font-medium bg-[#5b8def] text-white hover:bg-[#5b8def]/80 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
        Создать
      </button>
    </div>
  </div>
</Modal>

<style>
  :global(.page-enter) {
    animation: fadeIn 0.2s ease-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @keyframes msgIn {
    from { opacity: 0; transform: translateY(8px) scale(0.97); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }
</style>
