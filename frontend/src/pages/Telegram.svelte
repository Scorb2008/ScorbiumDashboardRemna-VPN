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
  let botName = $state('');
  let botDescription = $state('');
  let botShortDesc = $state('');
  let photoFile = $state(null);
  let photoUploading = $state(false);
  let botCommands = $state([]);
  let editingBtn = $state(null);
  let addPreset = $state('');

  const ALL_ICONS = [
    'dashboard', 'users', 'key', 'creditCard', 'payment', 'server', 'lifeBuoy',
    'tag', 'megaphone', 'userPlus', 'phone', 'logout', 'sun', 'moon', 'bell',
    'settings', 'send', 'messageSquare', 'fileText', 'percent', 'dollarSign',
    'wallet', 'bot', 'keyRound', 'ticket', 'headset', 'trash', 'edit',
    'refreshCw', 'activity', 'globe', 'wifi', 'shield', 'zap', 'barChart3',
    'trendingUp', 'externalLink', 'copy', 'download', 'upload', 'filter',
    'calendar', 'clock', 'link', 'info', 'alertTriangle', 'mail', 'lock',
    'unlock', 'camera', 'image', 'power', 'play', 'pause', 'archive',
    'clipboard', 'helpCircle', 'mapPin', 'rocket', 'terminal', 'code',
    'database', 'cpu', 'hardDrive', 'user', 'check', 'x', 'plus', 'minus',
    'search', 'hash',
  ];

  const BUTTON_PRESETS = [
    { name: 'buy', label: 'Купить подписку', defaultIcon: 'keyRound' },
    { name: 'my_keys', label: 'Мои ключи', defaultIcon: 'key' },
    { name: 'support', label: 'Поддержка', defaultIcon: 'headset' },
    { name: 'balance', label: 'Баланс', defaultIcon: 'wallet' },
    { name: 'promo', label: 'Промокод', defaultIcon: 'percent' },
    { name: 'profile', label: 'Профиль', defaultIcon: 'user' },
    { name: 'connect', label: 'Подключение', defaultIcon: 'wifi' },
    { name: 'about', label: 'О нас', defaultIcon: 'info' },
    { name: 'servers', label: 'Серверы', defaultIcon: 'server' },
    { name: 'top_referrers', label: 'Топ рефереров', defaultIcon: 'trendingUp' },
    { name: 'language', label: 'Язык', defaultIcon: 'globe' },
    { name: 'trial', label: 'Пробный период', defaultIcon: 'zap' },
  ];

  const BTN_STYLES = ['primary', 'success', 'danger', ''];
  const BTN_STYLE_LABELS = { primary: 'Синяя', success: 'Зелёная', danger: 'Красная', '': 'Обычная' };
  const BTN_STYLE_COLORS = { primary: '#5b8def', success: '#22c55e', danger: '#ef4450', '': '#8a8a9e' };

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

  const GENERAL_KEYS = [
    { key: 'maintenance_mode', label: 'Режим обслуживания', typ: 'checkbox' },
    { key: 'trial_enabled', label: 'Пробный период включён', typ: 'checkbox' },
    { key: 'notify_expiry_enabled', label: 'Уведомления об истечении', typ: 'checkbox' },
    { key: 'keyboard_layout', label: 'Раскладка клавиатуры', typ: 'input' },
    { key: 'bot_language', label: 'Язык бота', typ: 'input' },
    { key: 'required_channel_id', label: 'ID обязательного канала', typ: 'input' },
    { key: 'required_channel_name', label: 'Название обязательного канала', typ: 'input' },
    { key: 'trial_days', label: 'Дней пробного периода', typ: 'input' },
    { key: 'trial_label', label: 'Название пробного периода', typ: 'input' },
    { key: 'notify_expiry_days', label: 'За сколько дней уведомлять', typ: 'input' },
    { key: 'notify_chat_ids', label: 'Chat ID для уведомлений', typ: 'input' },
  ];

  const PHOTO_KEYS = [
    'photo_welcome', 'photo_buy', 'photo_my_keys', 'photo_balance',
    'photo_about', 'photo_support', 'photo_profile', 'photo_language', 'photo_trial',
  ];

  let activeButtons = $derived(BUTTON_PRESETS.filter(b => settings[`btn_${b.name}`]?.trim()));

  let currentEdit = $derived(editingBtn ? BUTTON_PRESETS.find(b => b.name === editingBtn) : null);

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

      if (!settings.logo_url) settings.logo_url = '';

      try {
        const nameData = await api.getBotName();
        botName = nameData.name || '';
        const descData = await api.getBotDescription();
        botDescription = descData.description || '';
        botShortDesc = descData.short_description || '';
      } catch (e) { /* ignore */ }
    } catch (e) { toasts.error('Ошибка загрузки: ' + e.message); }
    finally { loading = false; }
  }

  onMount(loadAll);

  async function saveBotName() {
    try { await api.setBotName(botName); toasts.success('Имя бота обновлено'); }
    catch (e) { toasts.error(e.message); }
  }

  async function saveBotDescription() {
    try { await api.setBotDescription(botDescription, botShortDesc); toasts.success('Описание бота обновлено'); }
    catch (e) { toasts.error(e.message); }
  }

  async function saveMessage(key) {
    settingsLoading = true;
    try {
      await api.updateSettings({ [key]: settings[key] ?? '' });
      toasts.success('Сохранено');
    } catch (e) { toasts.error(e.message); }
    finally { settingsLoading = false; }
  }

  async function saveGeneralSetting(key) {
    settingsLoading = true;
    try {
      await api.updateSettings({ [key]: settings[key] ?? '' });
      toasts.success('Сохранено');
    } catch (e) { toasts.error(e.message); }
    finally { settingsLoading = false; }
  }

  async function saveAllButtons() {
    settingsLoading = true;
    try {
      const updates = {};
      for (const b of BUTTON_PRESETS) {
        updates[`btn_${b.name}`] = settings[`btn_${b.name}`] ?? '';
        updates[`btn_${b.name}_style`] = settings[`btn_${b.name}_style`] ?? '';
        updates[`btn_icon_${b.name}`] = settings[`btn_icon_${b.name}`] ?? '';
      }
      await api.updateSettings(updates);
      toasts.success('Настройки кнопок сохранены');
    } catch (e) { toasts.error(e.message); }
    finally { settingsLoading = false; }
  }

  async function deleteButton(name) {
    settings[`btn_${name}`] = '';
    settings[`btn_${name}_style`] = '';
    settings[`btn_icon_${name}`] = '';
    if (editingBtn === name) editingBtn = null;
    await saveAllButtons();
  }

  function addButtonByPreset() {
    if (!addPreset) return;
    const preset = BUTTON_PRESETS.find(b => b.name === addPreset);
    if (!preset) return;
    settings[`btn_${preset.name}`] = preset.label;
    settings[`btn_${preset.name}_style`] = 'primary';
    settings[`btn_icon_${preset.name}`] = preset.defaultIcon;
    editingBtn = preset.name;
    addPreset = '';
    toasts.success(`Кнопка «${preset.label}» добавлена`);
  }

  function selectButton(name) {
    editingBtn = editingBtn === name ? null : name;
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
    try { await api.deleteBotPhoto(); toasts.success('Фото бота удалено'); }
    catch (e) { toasts.error(e.message); }
  }

  async function handleRefreshWebhook() {
    try { const r = await api.refreshWebhook(); toasts.success(r.detail || 'Webhook обновлён'); }
    catch (e) { toasts.error(e.message); }
  }

  function botPhotoUrl() {
    if (!botInfo) return '';
    if (botInfo.photo_url) return botInfo.photo_url;
    if (botInfo.username) return `https://t.me/i/userpic/320/${botInfo.username}.jpg`;
    return '';
  }

  async function uploadLogoFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      settings.logo_url = ev.target.result;
    };
    reader.readAsDataURL(file);
  }

  async function uploadSectionPhoto(key, e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      settings[key] = ev.target.result;
    };
    reader.readAsDataURL(file);
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

  <div class="flex gap-1 border-b border-surface-4/30 overflow-x-auto">
    {#each ['branding', 'buttons', 'media', 'commands'] as t}
      <button
        onclick={() => { tab = t; editingBtn = null; }}
        class="px-5 py-2.5 text-[13px] font-medium whitespace-nowrap border-b-2 transition-colors
          {tab === t
            ? 'border-accent text-accent'
            : 'border-transparent text-muted hover:text-white hover:border-surface-4'}">
        {t === 'branding' ? '🎨 Брендирование' : t === 'buttons' ? '🔘 Кнопки' : t === 'media' ? '📷 Медиа' : '⚙️ Команды'}
      </button>
    {/each}
  </div>

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

      <div class="card p-5 space-y-4">
        <h3 class="text-[15px] font-semibold flex items-center gap-2"><Icon name="settings" class="w-4 h-4 text-accent" /> Общие настройки</h3>
        <p class="text-[13px] text-muted">Дополнительные параметры бота</p>
        <div class="space-y-3">
          {#each GENERAL_KEYS as gk}
            <div class="bg-surface-3/40 rounded-[10px] p-3 border border-surface-4/20">
              <label class="label mb-1"><span class="label-text font-medium">{gk.label}</span></label>
              {#if gk.typ === 'checkbox'}
                <div class="flex items-center gap-3">
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings[gk.key] === '1' || settings[gk.key] === 1 || settings[gk.key] === true}
                      onchange={(e) => { settings[gk.key] = e.target.checked ? '1' : '0'; }}
                      class="w-4 h-4 rounded accent-accent"
                    />
                    <span class="text-[13px] text-muted">Включено</span>
                  </label>
                  <button onclick={() => saveGeneralSetting(gk.key)} class="btn btn-ghost btn-xs" disabled={settingsLoading}>
                    {settingsLoading ? '...' : 'Сохранить'}
                  </button>
                </div>
              {:else}
                <input type="text" bind:value={settings[gk.key]} class="input w-full text-[13px]" placeholder={gk.label} />
                <button onclick={() => saveGeneralSetting(gk.key)} class="btn btn-ghost btn-xs mt-2" disabled={settingsLoading}>
                  {settingsLoading ? '...' : 'Сохранить'}
                </button>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    </div>

  {:else if tab === 'buttons'}
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-5">
      <div class="lg:col-span-3 space-y-4">
        <div class="card p-5 space-y-4">
          <h3 class="text-[15px] font-semibold flex items-center gap-2"><Icon name="layoutDashboard" class="w-4 h-4 text-accent" /> Чат-превью</h3>
          <p class="text-[13px] text-muted">Как ваши кнопки выглядят в Telegram</p>

          <div class="bg-[#17212b] rounded-[14px] p-5 max-w-[420px] mx-auto">
            <div class="bg-[#2b5278] text-white/90 rounded-[10px] px-3.5 py-2.5 text-sm max-w-[80%] shadow-sm">
              Выберите действие:
            </div>
            {#if activeButtons.length > 0}
              <div class="grid grid-cols-2 gap-2 mt-4">
                {#each activeButtons as btn}
                  {@const style = settings[`btn_${btn.name}_style`] || ''}
                  {@const icon = settings[`btn_icon_${btn.name}`] || ''}
                  <button
                    onclick={() => selectButton(btn.name)}
                    class="flex items-center gap-2 px-3.5 py-2.5 rounded-[10px] text-sm font-medium transition-all duration-150
                      {editingBtn === btn.name
                        ? 'ring-2 ring-accent bg-accent/10'
                        : 'hover:bg-white/10'}
                      {!style ? 'bg-white/8 text-white/80' : style === 'primary' ? 'bg-accent/85 text-white' : style === 'success' ? 'bg-success/70 text-white' : 'bg-danger/70 text-white'}">
                    {#if icon}
                      <Icon name={icon} class="w-4 h-4 shrink-0" />
                    {/if}
                    <span class="truncate">{settings[`btn_${btn.name}`]}</span>
                    <span class="w-2 h-2 rounded-full shrink-0" style="background: {BTN_STYLE_COLORS[style] || '#8a8a9e'}"></span>
                  </button>
                {/each}
              </div>
            {:else}
              <div class="mt-4 text-center py-6 text-muted text-sm border border-dashed border-surface-4/40 rounded-[10px]">
                Нет активных кнопок. Добавьте кнопку ниже.
              </div>
            {/if}
          </div>
        </div>

        {#if currentEdit}
          <div class="card p-5 space-y-4 animate-fade-in">
            <div class="flex items-center justify-between">
              <h4 class="text-[14px] font-semibold flex items-center gap-2">
                <Icon name="edit" class="w-4 h-4 text-accent" />
                Редактирование: {currentEdit.label}
              </h4>
              <button onclick={() => editingBtn = null} class="btn btn-ghost btn-xs">
                <Icon name="x" class="w-3.5 h-3.5" />
              </button>
            </div>
            <div class="space-y-3">
              <div class="space-y-1">
                <label class="label"><span class="label-text">Текст кнопки</span></label>
                <input type="text" bind:value={settings[`btn_${currentEdit.name}`]} class="input w-full" placeholder="Текст кнопки..." />
              </div>
              <div class="space-y-1">
                <label class="label"><span class="label-text">Стиль</span></label>
                <select bind:value={settings[`btn_${currentEdit.name}_style`]} class="select w-full">
                  {#each BTN_STYLES as s}
                    <option value={s}>{BTN_STYLE_LABELS[s]}</option>
                  {/each}
                </select>
              </div>
              <div class="space-y-1">
                <label class="label"><span class="label-text">Иконка</span></label>
                <div class="flex gap-2">
                  <select bind:value={settings[`btn_icon_${currentEdit.name}`]} class="select flex-1">
                    <option value="">— Без иконки —</option>
                    {#each ALL_ICONS as icn}
                      <option value={icn}>{icn}</option>
                    {/each}
                  </select>
                  {#if settings[`btn_icon_${currentEdit.name}`]}
                    <div class="w-10 h-10 rounded-[10px] bg-surface-3 border border-surface-4 flex items-center justify-center shrink-0">
                      <Icon name={settings[`btn_icon_${currentEdit.name}`]} class="w-4 h-4 text-accent" />
                    </div>
                  {/if}
                </div>
              </div>
              <div class="flex gap-2 pt-2">
                <button onclick={() => deleteButton(currentEdit.name)} class="btn btn-danger btn-sm">
                  <Icon name="trash" class="w-3.5 h-3.5" /> Удалить кнопку
                </button>
                <button onclick={saveAllButtons} disabled={settingsLoading} class="btn btn-primary btn-sm">
                  {settingsLoading ? '...' : 'Сохранить'}
                </button>
              </div>
            </div>
          </div>
        {/if}

        {#if !editingBtn}
          <div class="card p-5 space-y-4">
            <h4 class="text-[14px] font-semibold flex items-center gap-2">
              <Icon name="plus" class="w-4 h-4 text-accent" /> Добавить кнопку
            </h4>
            <div class="flex gap-2">
              <select bind:value={addPreset} class="select flex-1">
                <option value="">— Выберите кнопку —</option>
                {#each BUTTON_PRESETS as p}
                  <option value={p.name}>{p.label}</option>
                {/each}
              </select>
              <button onclick={addButtonByPreset} disabled={!addPreset} class="btn btn-primary btn-sm">
                <Icon name="plus" class="w-3.5 h-3.5" /> Добавить
              </button>
            </div>
          </div>
        {/if}
      </div>

      <div class="lg:col-span-2 space-y-4">
        <div class="card p-5 space-y-3">
          <h3 class="text-[15px] font-semibold flex items-center gap-2"><Icon name="list" class="w-4 h-4 text-accent" /> Все кнопки</h3>
          <p class="text-[13px] text-muted">Быстрый просмотр и управление всеми кнопками</p>
          <div class="space-y-2 max-h-[400px] overflow-y-auto pr-1">
            {#each BUTTON_PRESETS as btn}
              {@const text = settings[`btn_${btn.name}`] || ''}
              {@const style = settings[`btn_${btn.name}_style`] || ''}
              {@const icon = settings[`btn_icon_${btn.name}`] || ''}
              <div
                onclick={() => selectButton(btn.name)}
                class="flex items-center gap-3 p-2.5 rounded-[10px] cursor-pointer transition-all border
                  {editingBtn === btn.name
                    ? 'border-accent/40 bg-accent/8'
                    : 'border-transparent hover:bg-surface-3/60 hover:border-surface-4/30'}
                  {!text ? 'opacity-40' : ''}">
                {#if icon}
                  <div class="w-8 h-8 rounded-[8px] bg-surface-3 border border-surface-4 flex items-center justify-center shrink-0">
                    <Icon name={icon} class="w-4 h-4 text-muted" />
                  </div>
                {:else}
                  <div class="w-8 h-8 rounded-[8px] bg-surface-3 border border-surface-4 flex items-center justify-center shrink-0">
                    <span class="text-xs text-muted">{btn.label[0]}</span>
                  </div>
                {/if}
                <div class="flex-1 min-w-0">
                  <p class="text-[13px] font-medium truncate">{text || btn.label}</p>
                  <p class="text-[10px] text-muted font-mono">{btn.name}</p>
                </div>
                {#if style}
                  <span class="w-2 h-2 rounded-full shrink-0" style="background: {BTN_STYLE_COLORS[style] || '#8a8a9e'}"></span>
                {/if}
              </div>
            {/each}
          </div>
        </div>

        <div class="card p-5 space-y-3">
          <button onclick={saveAllButtons} disabled={settingsLoading} class="btn btn-primary w-full">
            {#if settingsLoading}<div class="w-4 h-4 border-2 border-surface-4 border-t-white rounded-full animate-spin"></div>{/if}
            Сохранить все кнопки
          </button>
        </div>
      </div>
    </div>

  {:else if tab === 'media'}
    <div class="space-y-4">
      <div class="card p-5 space-y-4">
        <h3 class="text-[15px] font-semibold flex items-center gap-2"><Icon name="camera" class="w-4 h-4 text-accent" /> Фото бота</h3>
        <p class="text-[13px] text-muted">Загрузите фото профиля для бота (до 256x256 px)</p>
        <div class="flex flex-col sm:flex-row items-center gap-4">
          <div class="w-20 h-20 rounded-[14px] bg-surface-3 border-2 border-dashed border-surface-4 flex items-center justify-center overflow-hidden shrink-0">
            {#if photoFile}
              <img src={URL.createObjectURL(photoFile)} alt="preview" class="w-full h-full object-cover" />
            {:else if botPhotoUrl()}
              <img src={botPhotoUrl()} alt="bot photo" class="w-full h-full object-cover" onerror={(e) => { e.target.style.display = 'none'; }} />
            {:else}
              <Icon name="bot" class="w-8 h-8 text-muted" />
            {/if}
          </div>
          <div class="flex-1 space-y-2">
            <input type="file" accept="image/png,image/jpeg" onchange={(e) => photoFile = e.target.files?.[0] || null} class="text-sm text-muted file:mr-3 file:py-1.5 file:px-3 file:rounded-[8px] file:border-0 file:text-xs file:font-medium file:bg-accent file:text-white hover:file:bg-accent-hover" />
            <div class="flex gap-2 flex-wrap">
              <button onclick={handlePhotoUpload} disabled={!photoFile || photoUploading} class="btn btn-primary btn-sm">
                {photoUploading ? 'Загрузка...' : 'Загрузить фото'}
              </button>
              <button onclick={handleDeletePhoto} class="btn btn-danger btn-sm">Удалить фото</button>
            </div>
          </div>
        </div>
      </div>

      <div class="card p-5 space-y-4">
        <h3 class="text-[15px] font-semibold flex items-center gap-2"><Icon name="globe" class="w-4 h-4 text-accent" /> Логотип для дашборда</h3>
        <p class="text-[13px] text-muted">Логотип отображается в веб-панели (сохраняется в настройках)</p>
        <div class="flex flex-col sm:flex-row items-center gap-4">
          <div class="w-28 h-28 rounded-[16px] bg-surface-3 border-2 border-dashed border-surface-4 flex items-center justify-center overflow-hidden shrink-0">
            {#if settings.logo_url}
              <img src={settings.logo_url} alt="logo" class="w-full h-full object-contain" />
            {:else}
              <Icon name="image" class="w-10 h-10 text-muted" />
            {/if}
          </div>
          <div class="flex-1 space-y-2">
            <input type="text" bind:value={settings.logo_url} class="input w-full" placeholder="URL логотипа или data:image/..." />
            <div class="flex gap-2">
              <input type="file" accept="image/*" onchange={(e) => uploadLogoFile(e)} class="text-sm text-muted file:mr-3 file:py-1.5 file:px-3 file:rounded-[8px] file:border-0 file:text-xs file:font-medium file:bg-accent file:text-white hover:file:bg-accent-hover" />
              <button onclick={() => saveMessage('logo_url')} disabled={settingsLoading} class="btn btn-primary btn-sm">Сохранить URL</button>
            </div>
          </div>
        </div>
      </div>

      <div class="card p-5 space-y-3">
        <h3 class="text-[15px] font-semibold flex items-center gap-2"><Icon name="image" class="w-4 h-4 text-accent" /> Изображения для разделов бота</h3>
        <p class="text-[13px] text-muted">Фото, которые бот показывает в разделах</p>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-3 gap-3">
          {#each PHOTO_KEYS as photoKey}
            <div class="bg-surface-3/40 rounded-[10px] p-3 border border-surface-4/20">
              <div class="w-full h-24 rounded-[12px] bg-surface-3 border border-surface-4 mb-2 flex items-center justify-center overflow-hidden">
                {#if settings[photoKey]}
                  <img src={settings[photoKey]} alt={photoKey} class="w-full h-full object-cover" />
                {:else}
                  <Icon name="image" class="w-6 h-6 text-muted" />
                {/if}
              </div>
              <code class="text-[10px] font-mono text-muted block truncate">{photoKey}</code>
              <input type="text" bind:value={settings[photoKey]} class="input text-[11px] w-full mt-1.5" placeholder="URL фото" />
              <div class="flex gap-1 mt-1.5">
                <button onclick={() => saveMessage(photoKey)} class="btn btn-ghost btn-xs flex-1">OK</button>
                <input type="file" accept="image/*" onchange={(e) => uploadSectionPhoto(photoKey, e)} class="hidden" id="upload-{photoKey}" />
                <label for="upload-{photoKey}" class="btn btn-ghost btn-xs cursor-pointer">Загрузить</label>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <div class="card p-5 space-y-3">
        <h3 class="text-[15px] font-semibold flex items-center gap-2"><Icon name="refreshCw" class="w-4 h-4 text-accent" /> Сеть</h3>
        <button onclick={handleRefreshWebhook} class="btn btn-primary btn-sm">
          <Icon name="refreshCw" class="w-3.5 h-3.5" /> Переустановить Webhook
        </button>
      </div>
    </div>

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
