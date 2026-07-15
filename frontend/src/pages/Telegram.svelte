<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import StatsCard from '../components/StatsCard.svelte';
  import Spinner from '../components/Spinner.svelte';

  let botInfo = $state(null);
  let loading = $state(true);
  let chatId = $state('');
  let message = $state('');
  let sending = $state(false);

  onMount(async () => {
    try {
      botInfo = await api.getBotInfo();
    } catch (e) {
      toasts.error('Не удалось загрузить информацию о боте');
    } finally {
      loading = false;
    }
  });

  async function handleSend() {
    if (!chatId.trim() || !message.trim()) {
      toasts.warning('Заполните все поля');
      return;
    }
    sending = true;
    try {
      await api.sendTelegramMessage(chatId, message);
      toasts.success('Сообщение отправлено');
      message = '';
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    } finally {
      sending = false;
    }
  }
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div>
    <h1 class="text-2xl font-bold">Telegram</h1>
    <p class="text-sm text-base-content/40 mt-1">Информация о боте и отправка сообщений</p>
  </div>

  {#if botInfo}
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <StatsCard label="Username" value={`@${botInfo.username || '—'}`} icon="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" gradient="gradient-info" />
      <StatsCard label="Bot ID" value={botInfo.id ?? '—'} icon="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0" gradient="gradient-primary" />
      <StatsCard label="Имя" value={botInfo.first_name || '—'} icon="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" gradient="gradient-success" />
    </div>

    <div class="card p-5">
      <h2 class="font-semibold mb-4">Отправить сообщение</h2>
      <div class="space-y-4">
        <div class="form-control">
          <label class="label"><span class="label-text text-xs font-medium">Chat ID пользователя</span></label>
          <input type="text" bind:value={chatId} class="input input-bordered input-glass" placeholder="123456789" />
        </div>
        <div class="form-control">
          <label class="label"><span class="label-text text-xs font-medium">Текст сообщения (HTML)</span></label>
          <textarea bind:value={message} class="textarea textarea-bordered input-glass h-28 font-mono text-sm" placeholder="<b>Привет!</b> Это сообщение от администратора."></textarea>
        </div>
        <div class="flex justify-end">
          <button class="btn btn-primary btn-glow" disabled={sending} onclick={handleSend}>
            {#if sending}
              <span class="loading loading-spinner loading-sm"></span>
            {:else}
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
            {/if}
            Отправить
          </button>
        </div>
      </div>
    </div>
  {:else if !loading}
    <div class="card p-12 text-center text-base-content/30">
      <p>Не удалось загрузить информацию о боте. Проверьте настройки Telegram.</p>
    </div>
  {/if}
</div>
