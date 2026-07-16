<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
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
  let photoStatus = $state('');
  let botCommands = $state([]);
  let editingBtn = $state(null);
  let addPreset = $state('');
  let savingOrder = $state(false);
  let logoUploading = $state(false);
  let sectionUploading = $state('');

  let dragSource = $state(null);
  let dragOverTarget = $state(null);

  function parseLayout(raw) {
    if (raw && typeof raw === 'string' && raw.trim()) {
      try {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.every(r => Array.isArray(r))) {
          return parsed.map(row => row.filter(name => typeof name === 'string'));
        }
      } catch {}
      return raw.split(',').map(s => s.trim()).filter(Boolean).map(name => [name]);
    }
    return [];
  }

  let buttonLayout = $state([[]]);
  let allEnabledButtons = $derived(
    BUTTON_PRESETS.filter(b => settings[`btn_${b.name}`]?.trim())
  );
  let unassignedButtons = $derived(
    allEnabledButtons.filter(b => !buttonLayout.flat().includes(b.name))
  );
  let layoutFlat = $derived(buttonLayout.flat());

  function refreshLayout() {
    const raw = settings['btn_order'];
    const parsed = parseLayout(raw);
    if (parsed.length > 0) {
      buttonLayout = parsed;
    } else {
      buttonLayout = allEnabledButtons.map(b => [b.name]);
    }
  }

  $effect(() => { settings; refreshLayout(); });

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

  async function reloadSettings() {
    try {
      const s = await api.getSettings();
      settings = s || {};
    } catch (e) { /* ignore */ }
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
      await reloadSettings();
      toasts.success('Сохранено');
    } catch (e) { toasts.error(e.message); }
    finally { settingsLoading = false; }
  }

  async function saveGeneralSetting(key) {
    settingsLoading = true;
    try {
      await api.updateSettings({ [key]: settings[key] ?? '' });
      await reloadSettings();
      toasts.success('Сохранено');
    } catch (e) { toasts.error(e.message); }
    finally { settingsLoading = false; }
  }

  async function saveButton(name) {
    settingsLoading = true;
    try {
      const updates = {
        [`btn_${name}`]: settings[`btn_${name}`] ?? '',
        [`btn_${name}_style`]: settings[`btn_${name}_style`] ?? '',
        [`btn_icon_${name}`]: settings[`btn_icon_${name}`] ?? '',
      };
      await api.updateSettings(updates);
      await reloadSettings();
      toasts.success('Кнопка сохранена');
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
      await reloadSettings();
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
    const newLayout = buttonLayout.map(r => [...r]);
    if (newLayout.length === 0 || newLayout[newLayout.length - 1].length >= 2) {
      newLayout.push([preset.name]);
    } else {
      newLayout[newLayout.length - 1].push(preset.name);
    }
    buttonLayout = newLayout;
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
    photoStatus = 'uploading';
    try {
      await api.setBotPhoto(photoFile);
      photoStatus = 'success';
      toasts.success('Фото бота обновлено');
      photoFile = null;
    } catch (e) {
      photoStatus = 'error';
      toasts.error(e.message);
    }
    finally { photoUploading = false; }
  }

  async function handleDeletePhoto() {
    try {
      await api.deleteBotPhoto();
      botInfo = { ...botInfo, photo_url: null };
      toasts.success('Фото бота удалено');
    }
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
    logoUploading = true;
    try {
      const dataUrl = await fileToDataUrl(file);
      await api.updateSettings({ logo_url: dataUrl });
      settings.logo_url = dataUrl;
      await reloadSettings();
      toasts.success('Логотип загружен');
    } catch (err) {
      toasts.error(err.message);
    } finally {
      logoUploading = false;
      e.target.value = '';
    }
  }

  async function saveLogoUrl() {
    settingsLoading = true;
    try {
      await api.updateSettings({ logo_url: settings.logo_url ?? '' });
      await reloadSettings();
      toasts.success('URL логотипа сохранён');
    } catch (e) { toasts.error(e.message); }
    finally { settingsLoading = false; }
  }

  async function uploadSectionPhoto(key, e) {
    const file = e.target.files?.[0];
    if (!file) return;
    sectionUploading = key;
    try {
      const dataUrl = await fileToDataUrl(file);
      await api.updateSettings({ [key]: dataUrl });
      settings[key] = dataUrl;
      await reloadSettings();
      toasts.success(`Фото ${key} загружено`);
    } catch (err) {
      toasts.error(err.message);
    } finally {
      sectionUploading = '';
      e.target.value = '';
    }
  }

  function fileToDataUrl(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (ev) => resolve(ev.target.result);
      reader.onerror = () => reject(new Error('Ошибка чтения файла'));
      reader.readAsDataURL(file);
    });
  }

  function handleLayoutDragStart(e, rowIdx, colIdx) {
    dragSource = { row: rowIdx, col: colIdx };
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', `${rowIdx},${colIdx}`);
  }

  function handleLayoutDragOver(e, rowIdx, colIdx) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    dragOverTarget = { row: rowIdx, col: colIdx };
  }

  function handleLayoutDragOverRow(e, rowIdx) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    dragOverTarget = { row: rowIdx, col: -1 };
  }

  function handleLayoutDrop(e, rowIdx, colIdx) {
    e.preventDefault();
    e.stopPropagation();
    if (!dragSource) { dragSource = null; dragOverTarget = null; return; }
    const src = dragSource;
    const name = buttonLayout[src.row]?.[src.col];
    if (!name) { dragSource = null; dragOverTarget = null; return; }
    const newLayout = buttonLayout.map(r => [...r]);
    newLayout[src.row].splice(src.col, 1);
    if (newLayout[src.row].length === 0) newLayout.splice(src.row, 1);
    const insertRow = Math.min(rowIdx, newLayout.length);
    if (colIdx >= 0) {
      const insertCol = Math.min(colIdx, newLayout[insertRow]?.length ?? 0);
      if (!newLayout[insertRow]) newLayout[insertRow] = [];
      newLayout[insertRow].splice(insertCol, 0, name);
    } else {
      if (!newLayout[insertRow]) newLayout[insertRow] = [];
      newLayout[insertRow].push(name);
    }
    buttonLayout = newLayout.filter(r => r.length > 0);
    dragSource = null;
    dragOverTarget = null;
  }

  function handlePoolDrop(e) {
    e.preventDefault();
    if (!dragSource) { dragSource = null; dragOverTarget = null; return; }
    const src = dragSource;
    const name = buttonLayout[src.row]?.[src.col];
    if (!name) { dragSource = null; dragOverTarget = null; return; }
    const newLayout = buttonLayout.map(r => [...r]);
    newLayout[src.row].splice(src.col, 1);
    buttonLayout = newLayout.filter(r => r.length > 0);
    dragSource = null;
    dragOverTarget = null;
  }

  function handleDragEnd() {
    dragSource = null;
    dragOverTarget = null;
  }

  function addRow() {
    buttonLayout = [...buttonLayout, []];
  }

  function removeRow(rowIdx) {
    const newLayout = buttonLayout.filter((_, i) => i !== rowIdx);
    buttonLayout = newLayout.length > 0 ? newLayout : [[]];
  }

  function addBtnToRow(btnName, rowIdx) {
    const newLayout = buttonLayout.map(r => [...r]);
    if (rowIdx >= 0 && rowIdx < newLayout.length) {
      newLayout[rowIdx].push(btnName);
    } else {
      newLayout.push([btnName]);
    }
    buttonLayout = newLayout;
  }

  function removeBtnFromRow(rowIdx, colIdx) {
    const newLayout = buttonLayout.map(r => [...r]);
    newLayout[rowIdx].splice(colIdx, 1);
    buttonLayout = newLayout.filter(r => r.length > 0);
    if (buttonLayout.length === 0) buttonLayout = [[]];
  }

  async function saveButtonOrder() {
    savingOrder = true;
    try {
      const cleaned = buttonLayout.filter(r => r.length > 0);
      await api.updateSettings({ btn_order: JSON.stringify(cleaned) });
      await reloadSettings();
      toasts.success('Раскладка сохранена');
    } catch (e) { toasts.error(e.message); }
    finally { savingOrder = false; }
  }

  const TAB_CONFIG = [
    { id: 'branding', icon: 'fileText', label: 'Брендирование' },
    { id: 'buttons', icon: 'layoutDashboard', label: 'Кнопки' },
    { id: 'media', icon: 'camera', label: 'Медиа' },
    { id: 'commands', icon: 'terminal', label: 'Команды' },
  ];
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
    {#each TAB_CONFIG as tc}
      <button
        onclick={() => { tab = tc.id; editingBtn = null; }}
        class="flex items-center gap-2 px-5 py-2.5 text-[13px] font-medium whitespace-nowrap border-b-2 transition-colors
          {tab === tc.id
            ? 'border-accent text-accent'
            : 'border-transparent text-muted hover:text-white hover:border-surface-4'}">
        <Icon name={tc.icon} class="w-4 h-4" />
        {tc.label}
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
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-[15px] font-semibold flex items-center gap-2"><Icon name="layoutDashboard" class="w-4 h-4 text-accent" /> Чат-превью</h3>
              <p class="text-[13px] text-muted mt-0.5">Перетаскивайте кнопки прямо в превью. Каждая строка — один ряд в Telegram.</p>
            </div>
            <button onclick={saveButtonOrder} disabled={savingOrder} class="btn btn-primary btn-xs">
              {savingOrder ? '...' : 'Сохранить раскладку'}
            </button>
          </div>

          <div class="flex justify-center">
            <div class="bg-[#0f0f0f] rounded-[36px] p-3 shadow-xl border border-surface-4/30 w-full max-w-[375px]">
              <div class="bg-[#17212b] rounded-[28px] overflow-hidden">
                <div class="flex items-center justify-center h-6 bg-[#0f0f0f]">
                  <div class="w-[120px] h-[5px] bg-surface-4/50 rounded-full"></div>
                </div>
                <div class="px-3 pb-1 pt-0.5 flex items-center gap-2 bg-[#17212b]">
                  <div class="w-6 h-6 rounded-full bg-accent/30 flex items-center justify-center">
                    <Icon name="bot" class="w-3 h-3 text-accent" />
                  </div>
                  <div class="text-[11px] font-medium text-white/80">{botInfo?.first_name || 'Bot'}</div>
                  <div class="flex-1"></div>
                  <div class="text-white/40 text-[10px]">{new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}</div>
                </div>
                <div class="px-3 py-2 min-h-[280px] flex flex-col">
                  <div class="bg-[#2b5278] text-white/90 rounded-[12px] px-3 py-2 text-[13px] max-w-[80%] self-start shadow-sm leading-relaxed">
                    Выберите действие:
                  </div>

                  {#if buttonLayout.length > 0 && layoutFlat.length > 0}
                    <div class="mt-2 space-y-1.5">
                      {#each buttonLayout as row, rowIdx (rowIdx)}
                        <div
                          class="flex flex-wrap justify-center gap-1 min-h-[32px] py-0.5 rounded-lg transition-all
                            {dragOverTarget?.row === rowIdx ? 'bg-white/5 ring-1 ring-accent/40' : ''}"
                          ondragover={(e) => handleLayoutDragOverRow(e, rowIdx)}
                          ondrop={(e) => handleLayoutDrop(e, rowIdx, -1)}>
                          {#each row as btnName, colIdx (rowIdx + '-' + btnName)}
                            {@const style = settings[`btn_${btnName}_style`] || ''}
                            {@const icon = settings[`btn_icon_${btnName}`] || ''}
                            <div
                              draggable="true"
                              ondragstart={(e) => handleLayoutDragStart(e, rowIdx, colIdx)}
                              ondragover={(e) => handleLayoutDragOver(e, rowIdx, colIdx)}
                              ondrop={(e) => handleLayoutDrop(e, rowIdx, colIdx)}
                              ondragend={handleDragEnd}
                              class="flex items-center gap-1 px-2.5 py-1.5 rounded-[8px] text-[11px] font-medium cursor-grab active:cursor-grabbing select-none transition-all
                                {!style ? 'bg-white/10 text-white/80' : style === 'primary' ? 'bg-accent/85 text-white' : style === 'success' ? 'bg-[#22c55e]/70 text-white' : 'bg-[#ef4450]/70 text-white'}
                                {dragSource?.row === rowIdx && dragSource?.col === colIdx ? 'opacity-20 scale-95' : ''}
                                {dragOverTarget?.row === rowIdx && dragOverTarget?.col === colIdx ? 'ring-1 ring-white/50 scale-105' : ''}">
                              {#if icon}
                                <Icon name={icon} class="w-3 h-3 shrink-0" />
                              {/if}
                              <span class="truncate max-w-[70px]">{settings[`btn_${btnName}`] || btnName}</span>
                            </div>
                          {/each}
                        </div>
                      {/each}
                    </div>
                  {:else}
                    <div class="flex-1 flex items-center justify-center text-[12px] text-white/30 mt-4">
                      Нет кнопок
                    </div>
                  {/if}

                  <div class="flex-1"></div>
                  <div class="flex justify-center mt-1">
                    <div class="w-[30px] h-[3px] bg-white/20 rounded-full"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="card p-5 space-y-3">
          <h3 class="text-[15px] font-semibold flex items-center gap-2">
            <Icon name="layoutDashboard" class="w-4 h-4 text-accent" /> Управление строками
          </h3>
          <p class="text-[12px] text-muted">Добавляйте и удаляйте строки. Кнопки перетаскиваются между строками в превью выше.</p>
          <div class="space-y-1.5">
            {#each buttonLayout as row, rowIdx (rowIdx)}
              <div class="flex items-center gap-2 p-2 rounded-lg bg-surface-3/30 border border-surface-4/10">
                <span class="text-[10px] text-muted font-mono w-5 text-center shrink-0">{rowIdx + 1}</span>
                <div class="flex flex-wrap gap-1 flex-1 min-w-0">
                  {#each row as btnName}
                    {@const style = settings[`btn_${btnName}_style`] || ''}
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium
                      {style === 'primary' ? 'bg-accent/20 text-accent' : style === 'success' ? 'bg-success/20 text-success' : style === 'danger' ? 'bg-danger/20 text-danger' : 'bg-surface-3 text-muted'}">
                      {settings[`btn_${btnName}`] || btnName}
                    </span>
                  {/each}
                  {#if row.length === 0}
                    <span class="text-[11px] text-muted/40 italic">пусто</span>
                  {/if}
                </div>
                <button onclick={() => removeRow(rowIdx)}
                  class="shrink-0 w-5 h-5 rounded flex items-center justify-center text-muted hover:text-danger transition-colors">
                  <Icon name="x" size={12} />
                </button>
              </div>
            {/each}
          </div>
          <div class="flex gap-2">
            <button onclick={addRow} class="btn btn-ghost btn-sm">
              <Icon name="plus" class="w-3.5 h-3.5" /> Добавить строку
            </button>
          </div>

          {#if unassignedButtons.length > 0}
            <div class="border-t border-surface-4/20 pt-3 space-y-2">
              <p class="text-[11px] text-muted font-medium uppercase tracking-wider">Не в раскладке</p>
              <div class="flex flex-wrap gap-1.5"
                ondragover={(e) => e.preventDefault()}
                ondrop={handlePoolDrop}>
                {#each unassignedButtons as btn}
                  {@const style = settings[`btn_${btn.name}_style`] || ''}
                  {@const icon = settings[`btn_icon_${btn.name}`] || ''}
                  <button
                    onclick={() => { addBtnToRow(btn.name, buttonLayout.length - 1); }}
                    class="flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-medium transition-all
                      border border-dashed border-surface-4/40 hover:border-accent/50 hover:bg-accent/5 text-muted hover:text-text cursor-pointer">
                    {#if icon}
                      <Icon name={icon} class="w-3 h-3 shrink-0" />
                    {/if}
                    <span>{settings[`btn_${btn.name}`] || btn.label}</span>
                  </button>
                {/each}
              </div>
            </div>
          {/if}
        </div>

        {#if !editingBtn}
          <div class="card p-5 space-y-4">
            <h4 class="text-[14px] font-semibold flex items-center gap-2">
              <Icon name="plus" class="w-4 h-4 text-accent" /> Добавить кнопку
            </h4>
            <div class="flex gap-2">
              <select bind:value={addPreset} class="select flex-1">
                <option value="">— Выберите кнопку —</option>
                {#each BUTTON_PRESETS.filter(b => !layoutFlat.includes(b.name)) as p}
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
        {#if currentEdit}
          <div class="card p-5 space-y-4 animate-fade-in">
            <div class="flex items-center justify-between">
              <h4 class="text-[14px] font-semibold flex items-center gap-2">
                <Icon name="edit" class="w-4 h-4 text-accent" />
                Настройка: {currentEdit.label}
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
                  <Icon name="trash" class="w-3.5 h-3.5" /> Удалить
                </button>
                <button onclick={() => saveButton(currentEdit.name)} disabled={settingsLoading} class="btn btn-primary btn-sm flex-1">
                  {settingsLoading ? '...' : 'Сохранить кнопку'}
                </button>
              </div>
            </div>
          </div>
        {:else}
          <div class="card p-5 space-y-3">
            <h3 class="text-[15px] font-semibold flex items-center gap-2">
              <Icon name="settings" class="w-4 h-4 text-accent" /> Все настройки
            </h3>
            <p class="text-[13px] text-muted">Выберите кнопку слева для редактирования настроек</p>
            <button onclick={saveAllButtons} disabled={settingsLoading} class="btn btn-primary w-full">
              {#if settingsLoading}<div class="w-4 h-4 border-2 border-surface-4 border-t-white rounded-full animate-spin"></div>{/if}
              Сохранить все кнопки
            </button>
          </div>
        {/if}
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
            <input
              type="file"
              accept="image/png,image/jpeg"
              onchange={(e) => { photoFile = e.target.files?.[0] || null; photoStatus = ''; }}
              class="text-sm text-muted file:mr-3 file:py-1.5 file:px-3 file:rounded-[8px] file:border-0 file:text-xs file:font-medium file:bg-accent file:text-white hover:file:bg-accent-hover" />
            <div class="flex gap-2 flex-wrap items-center">
              <button onclick={handlePhotoUpload} disabled={!photoFile || photoUploading} class="btn btn-primary btn-sm">
                {#if photoUploading}
                  <div class="flex items-center gap-1.5">
                    <div class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    Загрузка...
                  </div>
                {:else}
                  Загрузить фото
                {/if}
              </button>
              <button onclick={handleDeletePhoto} class="btn btn-danger btn-sm">Удалить фото</button>
              {#if photoStatus === 'success'}
                <span class="text-[12px] text-green-400 flex items-center gap-1">
                  <Icon name="check" class="w-3 h-3" /> Обновлено
                </span>
              {:else if photoStatus === 'error'}
                <span class="text-[12px] text-red-400">Ошибка</span>
              {/if}
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
              <input
                type="file"
                accept="image/*"
                onchange={uploadLogoFile}
                class="text-sm text-muted file:mr-3 file:py-1.5 file:px-3 file:rounded-[8px] file:border-0 file:text-xs file:font-medium file:bg-accent file:text-white hover:file:bg-accent-hover" />
              <button onclick={saveLogoUrl} disabled={settingsLoading} class="btn btn-primary btn-sm">
                {#if settingsLoading}
                  <div class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                {:else}
                  Сохранить URL
                {/if}
              </button>
            </div>
            {#if logoUploading}
              <div class="flex items-center gap-2 text-[12px] text-accent">
                <div class="w-3.5 h-3.5 border-2 border-accent/30 border-t-accent rounded-full animate-spin"></div>
                Загрузка файла...
              </div>
            {/if}
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
                <button onclick={() => saveMessage(photoKey)} class="btn btn-ghost btn-xs flex-1" disabled={settingsLoading}>
                  {#if sectionUploading === photoKey}
                    <div class="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto"></div>
                  {:else}
                    OK
                  {/if}
                </button>
                <input type="file" accept="image/*" onchange={(e) => uploadSectionPhoto(photoKey, e)} class="hidden" id="upload-{photoKey}" />
                <label for="upload-{photoKey}" class="btn btn-ghost btn-xs cursor-pointer">
                  {sectionUploading === photoKey ? '...' : 'Загрузить'}
                </label>
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
