<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';

  let settings = $state({});
  let appConfig = $state(null);
  let paymentSystems = $state({});
  let loading = $state(true);
  let saving = $state(false);
  let activeSection = $state('general');

  async function loadAll() {
    loading = true;
    try {
      const [s, c, p] = await Promise.all([
        api.getSettings(),
        api.getAppConfig(),
        api.getPaymentSystems(),
      ]);
      settings = s || {};
      appConfig = c;
      paymentSystems = p || {};
    } catch (e) { toasts.error('Ошибка загрузки настроек'); }
    finally { loading = false; }
  }

  onMount(loadAll);

  async function saveSettings() {
    saving = true;
    try {
      await api.updateSettings(settings);
      toasts.success('Настройки сохранены');
    } catch (e) { toasts.error('Ошибка сохранения: ' + e.message); }
    finally { saving = false; }
  }

  const sections = [
    { id: 'general', label: 'Основные', icon: 'settings' },
    { id: 'payment', label: 'Платежи', icon: 'wallet' },
    { id: 'config', label: 'Конфигурация', icon: 'terminal' },
  ];
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-[28px] font-bold tracking-tight text-text">Настройки</h1>
      <p class="text-sm text-muted mt-1">Управление конфигурацией бота и системы</p>
    </div>
    <button class="btn btn-primary" onclick={saveSettings} disabled={saving}>
      {#if saving}
        <Icon name="rotate-ccw" class="w-4 h-4 animate-spin" />
      {:else}
        <Icon name="check" class="w-4 h-4" />
      {/if}
      Сохранить
    </button>
  </div>

  <div class="flex gap-1 bg-surface-2 p-1 rounded-[10px] w-fit">
    {#each sections as sec}
      <button
        class="px-3.5 py-1.5 text-xs font-medium rounded-[7px] transition-all {activeSection === sec.id ? 'bg-surface text-text shadow-sm' : 'text-muted hover:text-text'}"
        onclick={() => activeSection = sec.id}>
        <span class="flex items-center gap-1.5">
          <Icon name={sec.icon} class="w-3.5 h-3.5" />
          {sec.label}
        </span>
      </button>
    {/each}
  </div>

  {#if activeSection === 'general'}
    <div class="card p-5 space-y-4">
      <h3 class="text-[15px] font-semibold">Основные настройки бота</h3>
      <div class="space-y-3">
        {#each ['welcome_message', 'btn_my_keys', 'btn_buy', 'btn_support', 'btn_profile', 'btn_language'] as key}
          <div class="space-y-1">
            <label class="label text-xs">{key}</label>
            <textarea
              bind:value={settings[key]}
              class="textarea w-full h-20 text-[13px]"
              placeholder={key}></textarea>
          </div>
        {/each}
      </div>
    </div>

    <div class="card p-5 space-y-3">
      <h3 class="text-[15px] font-semibold">Системные настройки</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {#each [
          { key: 'maintenance_mode', label: 'Режим обслуживания', type: 'checkbox' },
          { key: 'auto_backup_enabled', label: 'Авто-бэкап', type: 'checkbox' },
          { key: 'trial_enabled', label: 'Пробный период', type: 'checkbox' },
          { key: 'referral_enabled', label: 'Реферальная система', type: 'checkbox' },
        ] as field}
          <label class="flex items-center gap-3 cursor-pointer p-3 rounded-[10px] bg-surface-2 hover:bg-surface-3 transition-colors">
            <input type="checkbox" checked={settings[field.key] === '1' || settings[field.key] === true} onchange={(e) => { settings[field.key] = e.target.checked ? '1' : '0'; }} class="w-4 h-4 rounded accent-accent" />
            <span class="text-[13px] font-medium">{field.label}</span>
          </label>
        {/each}
      </div>
    </div>
  {:else if activeSection === 'payment'}
    <div class="card p-5 space-y-4">
      <h3 class="text-[15px] font-semibold">Платёжные системы</h3>
      <div class="space-y-2.5">
        {#each ['yookassa', 'cryptobot', 'freekassa', 'aikassa', 'platega', 'paypalych'] as ps}
          <div class="flex items-center justify-between py-3 px-4 rounded-[10px] bg-surface-2">
            <span class="text-[13px] font-medium">{ps}</span>
            <div class="flex items-center gap-2">
              <span class="badge {paymentSystems[ps] === '1' || paymentSystems[ps] === true ? 'badge-success' : 'badge-neutral'}">
                {paymentSystems[ps] === '1' || paymentSystems[ps] === true ? 'Включена' : 'Выключена'}
              </span>
              <button
                class="btn btn-xs {paymentSystems[ps] === '1' || paymentSystems[ps] === true ? 'btn-danger' : 'btn-success'}"
                onclick={() => {
                  const enabled = paymentSystems[ps] === '1' || paymentSystems[ps] === true;
                  settings[`payment_system_${ps}`] = enabled ? '0' : '1';
                  paymentSystems[ps] = enabled ? '0' : '1';
                }}>
                {paymentSystems[ps] === '1' || paymentSystems[ps] === true ? 'Отключить' : 'Включить'}
              </button>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {:else if activeSection === 'config'}
    <div class="card p-5 space-y-4">
      <h3 class="text-[15px] font-semibold">Конфигурация приложения</h3>
      <div class="space-y-0 divide-y divide-border">
        {#each [
          ['Название', appConfig?.app_name],
          ['Версия', appConfig?.app_version],
          ['Сайт', appConfig?.site_url],
          ['Домен', appConfig?.domain],
          ['Путь панели', appConfig?.panel_path],
          ['Username бота', appConfig?.bot_username || '—'],
          ['ЮKassa', appConfig?.has_yookassa ? '✓ Настроена' : '✗ Не настроена'],
          ['Remnawave', appConfig?.has_remnawave ? '✓ Подключена' : '✗ Не подключена'],
        ] as [label, value]}
          <div class="flex justify-between py-3">
            <span class="text-[13px] text-muted">{label}</span>
            <span class="text-[13px] font-medium text-right">{value || '—'}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>
