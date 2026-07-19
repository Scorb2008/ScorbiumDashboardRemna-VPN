<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDateTime } from '../lib/utils.js';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';

  let broadcastHistory = $state([]);
  let loading = $state(true);
  let text = $state('');
  let target = $state('all');
  let sending = $state(false);
  let confirmSend = $state(false);

  const TARGET_LABELS = { all: 'всем пользователям', active: 'активным (за 7 дней)', paid: 'платившим', expired: 'с истёкшим ключом' };

  async function loadHistory() {
    loading = true;
    try { broadcastHistory = await api.getBroadcastHistory({ limit: 50 }); }
    catch (e) { toasts.error('Ошибка загрузки: ' + e.message); }
    finally { loading = false; }
  }

  onMount(loadHistory);

  async function sendBroadcast() {
    if (!text.trim()) return toasts.error('Введите текст рассылки');
    confirmSend = true;
  }

  async function doSendBroadcast() {
    confirmSend = false;
    sending = true;
    try {
      const created = await api.createBroadcast({ text: text.trim(), target });
      await api.sendBroadcastById(created.id);
      toasts.success('Рассылка отправлена!');
      text = '';
      await loadHistory();
    } catch (e) { toasts.error('Ошибка: ' + e.message); }
    finally { sending = false; }
  }
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div>
    <h1 class="text-[28px] font-bold tracking-tight">Рассылки</h1>
    <p class="text-sm text-muted mt-1">Массовые сообщения пользователям бота</p>
  </div>

  <div class="card p-5">
    <h3 class="text-[15px] font-semibold mb-4">Новая рассылка</h3>
    <div class="space-y-3">
      <div class="space-y-1">
        <label class="label"><span class="label-text">Целевая аудитория</span></label>
        <select bind:value={target} class="select w-full">
          <option value="all">Все пользователи</option>
          <option value="active">Активные (за 7 дней)</option>
          <option value="paid">Платившие</option>
          <option value="expired">С истёкшим ключом</option>
        </select>
      </div>
      <div class="space-y-1">
        <label class="label"><span class="label-text">Текст сообщения</span></label>
        <textarea bind:value={text} class="textarea w-full h-28" placeholder="Текст рассылки..."></textarea>
      </div>
      <button class="btn btn-primary" onclick={sendBroadcast} disabled={sending || !text.trim()}>
        {#if sending}
          <div class="w-4 h-4 border-2 border-surface-4 border-t-white rounded-full animate-spin"></div>
        {:else}
          <Icon name="send" class="w-4 h-4" />
        {/if}
        Отправить
      </button>
    </div>
  </div>

  {#if broadcastHistory.length > 0}
    <div class="card p-5">
      <h3 class="text-[15px] font-semibold mb-4">История рассылок</h3>
      <div class="space-y-0">
        {#each broadcastHistory as bc}
          <div class="flex items-start gap-4 py-3 border-b border-surface-4/30 last:border-0">
            <div class="w-8 h-8 rounded-[8px] bg-surface-3 border border-surface-4 flex items-center justify-center flex-shrink-0 mt-0.5">
              <Icon name="send" class="w-3.5 h-3.5 text-muted" />
            </div>
            <div class="min-w-0 flex-1">
              <p class="text-[13px] line-clamp-2">{bc.text || '—'}</p>
              <div class="flex items-center gap-3 mt-1">
                <span class="text-[11px] text-muted">{formatDateTime(bc.created_at)}</span>
                <span class="text-[11px] text-muted">Цель: {bc.target || 'all'}</span>
                {#if bc.sent_count != null}
                  <span class="text-[11px] text-muted">Отправлено: {bc.sent_count}</span>
                {/if}
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<ConfirmDialog bind:show={confirmSend} title="Отправить рассылку?" message={`Рассылка будет отправлена ${TARGET_LABELS[target] || target}.`} confirmText="Отправить" danger={false} onConfirm={doSendBroadcast} />
