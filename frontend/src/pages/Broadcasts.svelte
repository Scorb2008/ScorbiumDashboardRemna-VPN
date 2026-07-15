<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDateTime, truncate } from '../lib/utils.js';
  import Modal from '../components/Modal.svelte';
  import Spinner from '../components/Spinner.svelte';

  let broadcasts = $state([]);
  let loading = $state(true);
  let showModal = $state(false);
  let form = $state({ title: '', text: '', target: 'all', parse_mode: 'HTML' });
  let sending = $state(null);

  async function loadBroadcasts() {
    loading = true;
    try {
      broadcasts = await api.getBroadcasts({ limit: 50 });
    } catch (e) {
      toasts.error(e.message);
    } finally {
      loading = false;
    }
  }

  onMount(loadBroadcasts);

  async function handleCreate() {
    try {
      await api.createBroadcast(form);
      toasts.success('Рассылка создана');
      showModal = false;
      form = { title: '', text: '', target: 'all', parse_mode: 'HTML' };
      await loadBroadcasts();
    } catch (e) {
      toasts.error(e.message);
    }
  }

  async function handleSend(broadcast) {
    sending = broadcast.id;
    try {
      await api.sendBroadcast(broadcast.id);
      toasts.success('Рассылка отправлена');
      await loadBroadcasts();
    } catch (e) {
      toasts.error(e.message);
    } finally {
      sending = null;
    }
  }

  function statusBadge(status) {
    const map = { draft: 'badge-ghost', sending: 'badge-warning', done: 'badge-success', failed: 'badge-error' };
    return map[status] || 'badge-ghost';
  }

  function statusLabel(s) {
    const map = { draft: 'Черновик', sending: 'Отправка', done: 'Отправлено', failed: 'Ошибка' };
    return map[s] || s;
  }

  function targetLabel(t) {
    const map = { all: 'Все', active: 'Активные', expired: 'Истёкшие' };
    return map[t] || t;
  }
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-2xl font-bold">Рассылки</h1>
      <p class="text-sm text-base-content/40 mt-1">{broadcasts.length} рассылок</p>
    </div>
    <button onclick={() => showModal = true} class="btn btn-primary btn-sm btn-glow gap-2">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>
      Создать
    </button>
  </div>

  {#if broadcasts.length === 0}
    <div class="card p-12 text-center text-base-content/30">
      <svg class="w-12 h-12 mx-auto mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1"><path stroke-linecap="round" stroke-linejoin="round" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" /></svg>
      <p>Нет рассылок</p>
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      {#each broadcasts as bc, i (bc.id)}
        <div class="card p-5 animate-slide-up" style="animation-delay: {i * 30}ms">
          <div class="flex items-start justify-between mb-3">
            <div class="flex-1 min-w-0">
              <h3 class="font-medium truncate">{bc.title}</h3>
              <p class="text-xs text-base-content/40 mt-1">#{bc.id} &middot; {targetLabel(bc.target)} &middot; {formatDateTime(bc.created_at)}</p>
            </div>
            <span class="badge badge-sm badge-glow flex-shrink-0 ml-2 {statusBadge(bc.status)}">{statusLabel(bc.status)}</span>
          </div>
          <p class="text-sm text-base-content/60 mb-3 line-clamp-2">{truncate(bc.text, 120)}</p>
          <div class="flex items-center justify-between">
            <div class="text-xs text-base-content/40">
              {#if bc.sent_count > 0}
                Отправлено: {bc.sent_count}
              {/if}
              {#if bc.failed_count > 0}
                &middot; Ошибок: {bc.failed_count}
              {/if}
            </div>
            {#if bc.status === 'draft'}
              <button
                class="btn btn-sm btn-primary btn-glow"
                disabled={sending === bc.id}
                onclick={() => handleSend(bc)}>
                {#if sending === bc.id}
                  <span class="loading loading-spinner loading-sm"></span>
                  Отправка...
                {:else}
                  Отправить
                {/if}
              </button>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<Modal bind:open={showModal} title="Новая рассылка" size="md">
  <div class="space-y-4">
    <div class="form-control">
      <label class="label"><span class="label-text text-xs font-medium">Заголовок</span></label>
      <input type="text" bind:value={form.title} class="input input-bordered input-glass" placeholder="Заголовок рассылки" />
    </div>
    <div class="form-control">
      <label class="label"><span class="label-text text-xs font-medium">Текст (HTML)</span></label>
      <textarea bind:value={form.text} class="textarea textarea-bordered input-glass h-32 font-mono text-sm" placeholder="<b>Привет!</b> Это важное сообщение..."></textarea>
    </div>
    <div class="grid grid-cols-2 gap-3">
      <div class="form-control">
        <label class="label"><span class="label-text text-xs font-medium">Аудитория</span></label>
        <select bind:value={form.target} class="select select-bordered input-glass">
          <option value="all">Все</option>
          <option value="active">Активные</option>
          <option value="expired">Истёкшие</option>
        </select>
      </div>
      <div class="form-control">
        <label class="label"><span class="label-text text-xs font-medium">Формат</span></label>
        <select bind:value={form.parse_mode} class="select select-bordered input-glass">
          <option value="HTML">HTML</option>
          <option value="Markdown">Markdown</option>
          <option value="MarkdownV2">MarkdownV2</option>
        </select>
      </div>
    </div>
    <div class="flex gap-3 justify-end pt-2">
      <button class="btn btn-ghost" onclick={() => showModal = false}>Отмена</button>
      <button class="btn btn-primary btn-glow" onclick={handleCreate}>Создать черновик</button>
    </div>
  </div>
</Modal>
