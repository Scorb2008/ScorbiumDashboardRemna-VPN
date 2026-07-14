<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.js';
  import { toasts } from '../lib/stores.js';
  import Spinner from '../components/Spinner.svelte';
  import Modal from '../components/Modal.svelte';

  let broadcasts = $state([]);
  let loading = $state(true);
  let showModal = $state(false);
  let sending = $state(false);

  let form = $state({ title: '', text: '', target: 'all' });

  onMount(loadBroadcasts);

  async function loadBroadcasts() {
    loading = true;
    try {
      broadcasts = await api.getBroadcasts({ limit: 50 });
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    } finally {
      loading = false;
    }
  }

  async function handleCreate() {
    try {
      await api.createBroadcast(form);
      toasts.success('Рассылка создана');
      showModal = false;
      form = { title: '', text: '', target: 'all' };
      await loadBroadcasts();
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    }
  }

  async function handleSend(broadcast) {
    sending = true;
    try {
      await api.sendBroadcast(broadcast.id);
      toasts.success('Рассылка отправлена');
      await loadBroadcasts();
    } catch (e) {
      toasts.error('Ошибка: ' + e.message);
    } finally {
      sending = false;
    }
  }
</script>

<div class="fade-in">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">Рассылки</h1>
    <button class="btn btn-sm btn-primary" onclick={() => showModal = true}>+ Создать</button>
  </div>

  <Spinner {loading} />

  {#if !loading}
    {#if broadcasts.length === 0}
      <div class="text-center py-12 text-base-content/40">Нет рассылок</div>
    {:else}
      <div class="space-y-3">
        {#each broadcasts as b (b.id)}
          <div class="bg-base-200 rounded-xl p-4 flex items-center justify-between">
            <div>
              <div class="font-medium">{b.title}</div>
              <div class="text-sm text-base-content/50 mt-1 line-clamp-1">{b.text}</div>
              <div class="text-xs text-base-content/40 mt-2">
                Цель: {b.target} · {b.created_at ? new Date(b.created_at).toLocaleString('ru-RU') : ''}
              </div>
            </div>
            <div class="flex gap-2">
              <span class="badge badge-sm" class:badge-success={b.status === 'sent'} class:badge-warning={b.status === 'draft'}>
                {b.status}
              </span>
              {#if b.status === 'draft'}
                <button
                  class="btn btn-xs btn-primary"
                  onclick={() => handleSend(b)}
                  disabled={sending}>
                  Отправить
                </button>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  {/if}
</div>

<Modal bind:open={showModal} title="Новая рассылка" size="lg">
  <div class="space-y-4">
    <div class="form-control">
      <label class="label"><span class="label-text">Заголовок</span></label>
      <input type="text" bind:value={form.title} class="input input-bordered" />
    </div>
    <div class="form-control">
      <label class="label"><span class="label-text">Текст (HTML)</span></label>
      <textarea bind:value={form.text} class="textarea textarea-bordered h-32 font-mono text-sm"></textarea>
    </div>
    <div class="form-control">
      <label class="label"><span class="label-text">Цель</span></label>
      <select bind:value={form.target} class="select select-bordered">
        <option value="all">Все</option>
        <option value="active">Активные</option>
        <option value="expired">Истёкшие</option>
      </select>
    </div>
    <div class="flex justify-end gap-2 mt-4">
      <button class="btn btn-ghost" onclick={() => showModal = false}>Отмена</button>
      <button class="btn btn-primary" onclick={handleCreate}>Создать</button>
    </div>
  </div>
</Modal>
