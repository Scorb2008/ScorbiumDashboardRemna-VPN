<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import { formatDateTime } from '../lib/utils.js';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';

  let loading = $state(true);
  let botInfo = $state(null);
  let tab = $state('branding');

  let settings = $state({});
  let settingsLoading = $state(false);

  // Bot name/description
  let botName = $state('');
  let botDescription = $state('');
  let botShortDesc = $state('');

  // Button settings
  let buttonKeys = $state([]);
  let allBtnSettings = $state({});

  // Photo upload
  let photoFile = $state(null);
  let photoUploading = $state(false);
  let botCommands = $state([]);

  const BTN_LABELS = [
    { key: 'btn_buy', label: 'Купить подписку' },
    { key: 'btn_my_keys', label: 'Мои ключи' },
    { key: 'btn_support', label: 'Поддержка' },
    { key: 'btn_balance', label: 'Баланс' },
    { key: 'btn_promo', label: 'Промокод' },
    { key: 'btn_trial', label: 'Пробный период' },
    { key: 'btn_profile', label: 'Профиль' },
    { key: 'btn_connect', label: 'Подключение' },
    { key: 'btn_about', label: 'О нас' },
    { key: 'btn_servers', label: 'Серверы' },
    { key: 'btn_top_referrers', label: 'Топ рефереров' },
    { key: 'btn_language', label: 'Язык' },
  ];

  const BTN_STYLES = ['primary', 'success', 'danger', ''];
  const BTN_STYLE_LABELS = {
    primary: 'Синяя', success: 'Зелёная', danger: 'Красная', '': 'Обычная'
  };

  // Welcome/Branding messages
  const MSG_KEYS = [
    { key: 'welcome_message', label: 'Приветствие', typ: 'textarea' },
    { key: 'about_text', label: 'О нас (текст)', typ: 'textarea' },
    { key: 'payment_success_message', label: 'Успешный платёж', typ: 'textarea' },
    { key: 'subscription_issued_message', label: 'Ключ выдан', typ: 'textarea' },
    { key: 'subscription_cancelled_message', label: 'Подписка отменена', typ: 'textarea' },
    { key: 'ban_message', label: 'Бан', typ: 'textarea' },
    { key: 'unban_message', label: 'Разбан', typ: 'textarea' },
    { key: 'bot_disabled_message', label: 'Бот отключён', typ: 'textarea' },
    { key: 'referral_welcome_message', label: 'Реферал приветствие', typ: 'textarea' },
    { key: 'notify_expiry_message', label: 'Уведомление об истечении', typ: 'textarea' },
    { key: 'support_url', label: 'Ссылка поддержки', typ: 'input' },
    { key: 'panel_url', label: 'URL панели', typ: 'input' },
    { key: 'cabinet_url', label: 'URL кабинета', typ: 'input' },
  ];

  async function loadAll() {
    loading = true;
    try {
      const [info, s, cmds] = await Promise.all([
        api.getBotInfo(),
        api.getSettings(),
        api.getBotCommands(),
      ]);
      botInfo = info;
      settings = s || {};
      botCommands = Array.isArray(cmds) ? cmds : [];

      // Load bot name/description
      try {
        const nameData = await api.getBotName();
        botName = nameData.name || '';
        const descData = await api.getBotDescription();
        botDescription = descData.description || '';
        botShortDesc = descData.short_description || '';
      } catch (e) { /* ignore */ }

      // Load button settings
      allBtnSettings = {};
      for (const b of BTN_LABELS) {
        allBtnSettings[b.key] = s[b.key] || '';
        allBtnSettings[b.key + '_style'] = s[b.key + '_style'] || '';
        allBtnSettings[b.key.replace('btn_', 'btn_emoji_')] = s[b.key.replace('btn_', 'btn_emoji_')] || '';
      }
    } catch (e) { toasts.error('Ошибка загрузки: ' + e.message); }
    finally { loading = false; }
  }

  onMount(loadAll);

  async function saveBotName() {
    try {
      await api.setBotName(botName);
      toasts.success('Имя бота обновлено');
    } catch (e) { toasts.error(e.message); }
  }

  async function saveBotDescription() {
    try {
      await api.setBotDescription(botDescription, botShortDesc);
      toasts.success('Описание бота обновлено');
    } catch (e) { toasts.error(e.message); }
  }

  async function saveButtonSettings() {
    settingsLoading = true;
    try {
      const updates = {};
      for (const b of BTN_LABELS) {
        updates[b.key] = allBtnSettings[b.key] || '';
        updates[b.key + '_style'] = allBtnSettings[b.key + '_style'] || '';
        updates[b.key.replace('btn_', 'btn_emoji_')] = allBtnSettings[b.key.replace('btn_', 'btn_emoji_')] || '';
      }
      await api.updateSettings(updates);
      toasts.success('Настройки кнопок сохранены');
    } catch (e) { toasts.error(e.message); }
    finally { settingsLoading = false; }
  }

  async function saveMessage(key) {
    settingsLoading = true;
    try {
      await api.updateSettings({ [key]: settings[key] || '' });
      toasts.success('Сохранено');
    } catch (e) { toasts.error(e.message); }
    finally { settingsLoading = false; }
  }

  async function handlePhotoUpload() {
    if (!photoFile) return;
    photoUploading = true;
    try {
      await api.setBotPhoto(photoFile);
      toasts.success('Фото бота обновлено');
      photoFile = null;
    } catch (e) { toasts.error(e.message); }
    finally { photoUploading = false; }
  }

  async function handleDeletePhoto() {
    try {
      await api.deleteBotPhoto();
      toasts.success('Фото бота удалено');
    } catch (e) { toasts.error(e.message); }
  }

  async function handleRefreshWebhook() {
    try {
      const r = await api.refreshWebhook();
      toasts.success(r.detail || 'Webhook обновлён');
    } catch (e) { toasts.error(e.message); }
  }
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight">Telegram Бот</h1>
      <p class="text-sm text-muted mt-1">Управление ботом: настройка, брендирование, медиа</p>
    </div>
    {#if botInfo}
      <div class="flex items-center gap-3 bg-surface-3/50 rounded-[10px] px-4 py-2 border border-surface-4/30">
        <div class="w-8 h-8 rounded-[8px] bg-accent/20 flex items-center justify-center">
          <Icon name="bot" class="w-4 h-4 text-accent" />
        </div>
        <div class="text-sm">
          <p class="font-medium">{botInfo.first_name || 'Бот'}</p>
          <p class="text-[11px] text-muted">@{botInfo.username || '—'}</p>
        </div>
      </div>
    {/if}
  </div>

  <!-- Tabs -->
  <div class="flex gap-1 border-b border-surface-4/30 overflow-x-auto">
    {#each ['branding', 'buttons', 'media', 'commands'] as t}
      <button
        onclick={() => tab = t}
        class="px-5 py-2.5 text-[13px] font-medium whitespace-nowrap border-b-2 transition-colors
          {tab === t
            ? 'border-accent text-accent'
            : 'border-transparent text-muted hover:text-white hover:border-surface-4'}">
        {t === 'branding' ? '🎨 Брендирование' : t === 'buttons' ? '🔘 Кнопки' : t === 'media' ? '📷 Медиа' : '⚙️ Команды'}
      </button>
    {/each}
  </div>

  <!-- Tab: Branding -->
  {#if tab === 'branding'}
    <div class="space-y-4">
      <div class="card p-5 space-y-4">
        <h3 class="text-[15px] font-semibold flex items-center gap-2"><Icon name="edit" class="w-4 h-4 text-accent" /> Имя бота</h3>
        <div class="space-y-2">
          <input type="text" bind:value={botName} class="input w-full" placeholder="Имя бота (отображается в Telegram)" />
          <button onclick={saveBotName} class="btn btn-primary btn-sm">Сохранить имя</button>
        </div>
      </div>

      <div class="card p-5 space-y-4">
        <h3 class="text-[15px] font-semibold flex items-center gap-2"><Icon name="fileText" class="w-4 h-4 text-accent" /> Описание бота</h3>
        <div class="space-y-3">
          <div class="space-y-1">
            <label class="label"><span class="label-text">Описание (видно при /start)</span></label>
            <textarea bind:value={botDescription} class="textarea w-full h-24" placeholder="Описание бота..."></textarea>
          </div>
          <div class="space-y-1">
            <label class="label"><span class="label-text">Краткое описание (видно в списке ботов)</span></label>
            <input type="text" bind:value={botShortDesc} class="input w-full" placeholder="Краткое описание..." />
          </div>
          <button onclick={saveBotDescription} class="btn btn-primary btn-sm">Сохранить описание</button>
        </div>
      </div>

      <div class="card p-5 space-y-4">
        <h3 class="text-[15px] font-semibold flex items-center gap-2"><Icon name="messageSquare" class="w-4 h-4 text-accent" /> Тексты сообщений</h3>
        <p class="text-[13px] text-muted">Редактирование текстов, которые бот отправляет пользователям</p>
        <div class="space-y-3 max-h-[500px] overflow-y-auto pr-1">
          {#each MSG_KEYS as msg}
            <div class="bg-surface-3/40 rounded-[10px] p-3 border border-surface-4/20">
              <label class="label mb-1"><span class="label-text font-medium">{msg.label}</span></label>
              {#if msg.typ === 'textarea'}
                <textarea bind:value={settings[msg.key]} class="textarea w-full h-20 text-[13px]" placeholder={msg.label}></textarea>
              {:else}
                <input type="text" bind:value={settings[msg.key]} class="input w-full text-[13px]" placeholder={msg.label} />
              {/if}
              <button onclick={() => saveMessage(msg.key)} class="btn btn-ghost btn-xs mt-2" disabled={settingsLoading}>
                {settingsLoading ? '...' : 'Сохранить'}
              </button>
            </div>
          {/each}
        </div>
      </div>
    </div>

  <!-- Tab: Buttons -->
  {:else if tab === 'buttons'}
    <div class="card p-5 space-y-4">
      <h3 class="text-[15px] font-semibold flex items-center gap-2"><Icon name="layoutDashboard" class="w-4 h-4 text-accent" /> Кастомизация кнопок</h3>
      <p class="text-[13px] text-muted">Настройка текста, стиля и эмодзи для каждой кнопки бота</p>

      <div class="space-y-3">
        {#each BTN_LABELS as btn}
          <div class="bg-surface-3/40 rounded-[10px] p-3 border border-surface-4/20">
            <div class="flex items-center gap-2 mb-2">
              <div class="w-7 h-7 rounded-[6px] bg-surface-3 border border-surface-4 flex items-center justify-center">
                <Icon name="chevronRight" class="w-3 h-3 text-muted" />
              </div>
              <span class="text-[13px] font-medium">{btn.label}</span>
              <code class="text-[10px] font-mono text-muted ml-auto">{btn.key}</code>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <div class="space-y-1">
                <label class="text-[11px] text-muted">Текст кнопки</label>
                <input type="text" bind:value={allBtnSettings[btn.key]} class="input text-[13px]" placeholder="Текст..." />
              </div>
              <div class="space-y-1">
                <label class="text-[11px] text-muted">Стиль</label>
                <select bind:value={allBtnSettings[btn.key + '_style']} class="select text-[13px]">
                  {#each BTN_STYLES as s}
                    <option value={s}>{BTN_STYLE_LABELS[s]}</option>
                  {/each}
                </select>
              </div>
              <div class="space-y-1">
                <label class="text-[11px] text-muted">Emoji (опционально)</label>
                <input type="text" bind:value={allBtnSettings[btn.key.replace('btn_', 'btn_emoji_')]} class="input text-[13px]" placeholder="🔑" />
              </div>
            </div>
          </div>
        {/each}
      </div>

      <button onclick={saveButtonSettings} disabled={settingsLoading} class="btn btn-primary w-full">
        {#if settingsLoading}<div class="w-4 h-4 border-2 border-surface-4 border-t-white rounded-full animate-spin"></div>{/if}
        Сохранить все кнопки
      </button>
    </div>

  <!-- Tab: Media -->
  {:else if tab === 'media'}
    <div class="space-y-4">
      <div class="card p-5 space-y-4">
        <h3 class="text-[15px] font-semibold flex items-center gap-2"><Icon name="camera" class="w-4 h-4 text-accent" /> Фото бота</h3>
        <p class="text-[13px] text-muted">Загрузите фото профиля для бота (до 256x256 px)</p>

        <div class="flex flex-col sm:flex-row items-center gap-4">
          <div class="w-20 h-20 rounded-[14px] bg-surface-3 border-2 border-dashed border-surface-4 flex items-center justify-center overflow-hidden">
            {#if photoFile}
              <img src={URL.createObjectURL(photoFile)} alt="preview" class="w-full h-full object-cover" />
            {:else}
              <Icon name="bot" class="w-8 h-8 text-muted" />
            {/if}
          </div>
          <div class="flex-1 space-y-2">
            <input type="file" accept="image/png,image/jpeg" onchange={(e) => photoFile = e.target.files?.[0] || null} class="text-sm" />
            <div class="flex gap-2">
              <button onclick={handlePhotoUpload} disabled={!photoFile || photoUploading} class="btn btn-primary btn-sm">
                {photoUploading ? 'Загрузка...' : 'Загрузить фото'}
              </button>
              <button onclick={handleDeletePhoto} class="btn btn-danger btn-sm">Удалить фото</button>
            </div>
          </div>
        </div>
      </div>

      <div class="card p-5 space-y-3">
        <h3 class="text-[15px] font-semibold flex items-center gap-2"><Icon name="image" class="w-4 h-4 text-accent" /> Изображения для разделов бота</h3>
        <p class="text-[13px] text-muted">Фото, которые бот показывает в разделах (через bot settings)</p>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {#each ['photo_welcome', 'photo_buy', 'photo_my_keys', 'photo_balance', 'photo_about', 'photo_support', 'photo_profile', 'photo_language', 'photo_trial'] as photoKey}
            <div class="bg-surface-3/40 rounded-[10px] p-3 border border-surface-4/20 text-center">
              <div class="w-full h-20 rounded-[8px] bg-surface-3 border border-surface-4 mb-2 flex items-center justify-center overflow-hidden">
                {#if settings[photoKey]}
                  <img src={settings[photoKey]} alt={photoKey} class="w-full h-full object-cover" />
                {:else}
                  <Icon name="image" class="w-6 h-6 text-muted" />
                {/if}
              </div>
              <code class="text-[10px] font-mono text-muted">{photoKey}</code>
              <div class="flex gap-1 mt-2">
                <input type="text" bind:value={settings[photoKey]} class="input text-[11px] flex-1" placeholder="URL фото" />
                <button onclick={() => saveMessage(photoKey)} class="btn btn-ghost btn-xs px-2">OK</button>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <div class="card p-5 space-y-3">
        <h3 class="text-[15px] font-semibold">Сеть</h3>
        <button onclick={handleRefreshWebhook} class="btn btn-primary btn-sm">
          <Icon name="refreshCw" class="w-3.5 h-3.5" /> Переустановить Webhook
        </button>
      </div>
    </div>

  <!-- Tab: Commands -->
  {:else if tab === 'commands'}
    <div class="card p-5 space-y-4">
      <h3 class="text-[15px] font-semibold flex items-center gap-2"><Icon name="terminal" class="w-4 h-4 text-accent" /> Команды бота</h3>
      <p class="text-[13px] text-muted">Текущий список команд бота. Для изменения обратитесь к @BotFather.</p>

      <div class="space-y-2">
        {#each botCommands as cmd}
          <div class="flex items-center gap-3 py-2 border-b border-surface-4/20 last:border-0">
            <code class="font-mono text-[13px] text-accent min-w-[100px]">/{cmd.command}</code>
            <span class="text-[13px] text-muted">{cmd.description}</span>
          </div>
        {/each}
      </div>
      {#if botCommands.length === 0}
        <p class="text-sm text-muted">Нет установленных команд</p>
      {/if}
    </div>
  {/if}
</div>
