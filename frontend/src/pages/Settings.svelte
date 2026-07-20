<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';

  let loading = $state(true);
  let activeTab = $state('payments');
  let appConfig = $state(null);
  let botSettings = $state({});
  let paymentSystems = $state({});
  let testing = $state({});
  let testResults = $state({});
  let saving = $state({});

  const TABS = [
    { id: 'payments', label: 'Платежи', icon: 'wallet' },
    { id: 'system', label: 'Система', icon: 'terminal' },
    { id: 'notifications', label: 'Уведомления', icon: 'bell' },
    { id: 'monitoring', label: 'Мониторинг', icon: 'activity' },
    { id: 'trial', label: 'Пробный период', icon: 'zap' },
    { id: 'referrals', label: 'Рефералы', icon: 'users' },
  ];

  const PAYMENT_SYSTEMS = [
    { id: 'yookassa', label: 'ЮKassa', icon: 'creditCard', fields: [
      { key: 'shop_id', label: 'Shop ID', type: 'text' },
      { key: 'secret_key', label: 'Secret Key', type: 'password' },
    ]},
    { id: 'cryptobot', label: 'CryptoBot', icon: 'wallet', fields: [
      { key: 'token', label: 'API Token', type: 'password' },
      { key: 'rate', label: 'Курс Stars → RUB', type: 'text' },
    ]},
    { id: 'stars', label: 'Telegram Stars', icon: 'zap', fields: [
      { key: 'rate', label: 'Курс Stars → RUB', type: 'text' },
    ]},
    { id: 'freekassa', label: 'FreeKassa', icon: 'dollarSign', fields: [
      { key: 'shop_id', label: 'Shop ID', type: 'text' },
      { key: 'api_key', label: 'API Key', type: 'password' },
      { key: 'secret_word_1', label: 'Secret Word 1', type: 'password' },
      { key: 'secret_word_2', label: 'Secret Word 2', type: 'password' },
    ]},
    { id: 'aikassa', label: 'AiKassa', icon: 'payment', fields: [
      { key: 'shop_id', label: 'Shop ID', type: 'text' },
      { key: 'token', label: 'Токен', type: 'password' },
    ]},
    { id: 'platega', label: 'Platega', icon: 'creditCard', fields: [
      { key: 'merchant_id', label: 'Merchant ID', type: 'text' },
      { key: 'secret', label: 'Секрет', type: 'password' },
    ]},
    { id: 'paypalych', label: 'PayPal.ych', icon: 'payment', fields: [
      { key: 'api_token', label: 'API Token', type: 'password' },
    ]},
  ];

  const MONITORING_FIELDS = [
    { key: 'notify_expiry_enabled', label: 'Уведомления об истечении', type: 'checkbox' },
    { key: 'notify_expiry_days', label: 'Дней до истечения', type: 'number' },
    { key: 'notify_expiry_message', label: 'Текст уведомления', type: 'textarea' },
    { key: 'notify_chat_ids', label: 'ID чатов для уведомлений', type: 'text' },
    { key: 'maintenance_mode', label: 'Режим обслуживания', type: 'checkbox' },
    { key: 'maintenance_message', label: 'Сообщение об обслуживании', type: 'textarea' },
    { key: 'traffic_abuse_threshold_gb', label: 'Порог злоупотребления (ГБ)', type: 'number' },
    { key: 'traffic_abuse_speed_limit_mbps', label: 'Лимит скорости (Мбит/с)', type: 'number' },
  ];

  const TRIAL_FIELDS = [
    { key: 'trial_enabled', label: 'Включить пробный период', type: 'checkbox' },
    { key: 'trial_days', label: 'Дней пробного периода', type: 'number' },
    { key: 'trial_label', label: 'Название пробного тарифа', type: 'text' },
  ];

  async function loadAll() {
    loading = true;
    try {
      const [c, p, s] = await Promise.all([
        api.getAppConfig(),
        api.getPaymentSystemsDetail(),
        api.getSettings(),
      ]);
      appConfig = c;
      paymentSystems = p || {};
      botSettings = s || {};
    } catch (e) { toasts.error('Ошибка загрузки настроек'); }
    finally { loading = false; }
  }

  onMount(loadAll);

  async function toggleSystem(name) {
    const ps = paymentSystems[name];
    if (!ps) return;
    saving[name] = true;
    try {
      const willEnable = !ps.enabled;
      if (willEnable) {
        const required = PAYMENT_SYSTEMS.find(p => p.id === name)?.fields || [];
        const empty = required.filter(f => !ps.config?.[f.key]?.trim());
        if (empty.length > 0) {
          toasts.warning(`Заполните поля: ${empty.map(f => f.label).join(', ')}`);
          saving[name] = false;
          return;
        }
      }
      await api.configurePaymentSystem(name, { enabled: willEnable });
      ps.enabled = willEnable;
      toasts.success(`${name}: ${willEnable ? 'включена' : 'отключена'}`);
    } catch (e) { toasts.error(e.message); }
    finally { saving[name] = false; }
  }

  async function saveSystem(name) {
    const ps = paymentSystems[name];
    if (!ps) return;
    saving[name] = true;
    testResults[name] = null;
    try {
      const payload = {};
      for (const f of PAYMENT_SYSTEMS.find(p => p.id === name)?.fields || []) {
        if (ps.config?.[f.key] !== undefined) {
          payload[f.key] = ps.config[f.key];
        }
      }
      await api.configurePaymentSystem(name, payload);
      toasts.success(`Настройки ${name} сохранены`);
    } catch (e) { toasts.error(e.message); }
    finally { saving[name] = false; }
  }

  async function testSystem(name) {
    testing[name] = true;
    testResults[name] = null;
    try {
      const r = await api.testPaymentSystem(name);
      testResults[name] = r;
    } catch (e) {
      testResults[name] = { ok: false, detail: e.message };
    }
    finally { testing[name] = false; }
  }

  async function saveSettingsSection(keys) {
    saving._section = true;
    try {
      const payload = {};
      for (const key of keys) {
        if (botSettings[key] !== undefined) {
          payload[key] = botSettings[key];
        }
      }
      await api.updateSettings(payload);
      toasts.success('Настройки сохранены');
    } catch (e) { toasts.error(e.message); }
    finally { saving._section = false; }
  }

  async function toggleAndSave(key) {
    const newVal = botSettings[key] === '1' ? '0' : '1';
    botSettings[key] = newVal;
    saving[key] = true;
    try {
      await api.updateSettings({ [key]: newVal });
    } catch (e) {
      botSettings[key] = newVal === '1' ? '0' : '1';
      toasts.error(e.message);
    } finally { saving[key] = false; }
  }

  async function saveSingleSetting(key) {
    saving[key] = true;
    try {
      await api.updateSettings({ [key]: botSettings[key] });
      toasts.success('Сохранено');
    } catch (e) { toasts.error(e.message); }
    finally { saving[key] = false; }
  }
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div>
    <h1 class="text-[28px] font-bold tracking-tight">Настройки</h1>
    <p class="text-sm text-muted mt-1">Управление конфигурацией платформы</p>
  </div>

  <!-- Top Inner Sidebar -->
  <div class="flex gap-1 bg-surface-2 p-1 rounded-[10px] w-fit overflow-x-auto whitespace-nowrap">
    {#each TABS as tab}
      <button
        onclick={() => activeTab = tab.id}
        class="flex items-center gap-1.5 px-3.5 py-2 text-xs font-medium rounded-[7px] transition-all
          {activeTab === tab.id
            ? 'bg-surface text-text shadow-sm'
            : 'text-muted hover:text-text'}"
      >
        <Icon name={tab.icon} size={14} />
        {tab.label}
      </button>
    {/each}
  </div>

  <!-- Content -->
  <div class="flex-1 min-w-0">
      {#if activeTab === 'payments'}
        <div class="space-y-4">
          <div>
            <h2 class="text-[17px] font-semibold flex items-center gap-2">
              <Icon name="wallet" class="w-5 h-5 text-accent" /> Платёжные системы
            </h2>
            <p class="text-[13px] text-muted mt-0.5">Подключение и настройка способов оплаты</p>
          </div>

          <div class="grid gap-4">
            {#each PAYMENT_SYSTEMS as ps}
              {#if paymentSystems[ps.id]}
                <div class="card p-5 space-y-4 border {paymentSystems[ps.id].enabled ? 'border-accent/30' : 'border-surface-4/30'}">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                      <div class="w-10 h-10 rounded-[10px] bg-[#1c1c24] border border-[#2a2a35] flex items-center justify-center">
                        <Icon name={ps.icon} class="w-5 h-5 {paymentSystems[ps.id].enabled ? 'text-accent' : 'text-muted'}" />
                      </div>
                      <div>
                        <h3 class="text-[15px] font-semibold">{ps.label}</h3>
                        <p class="text-[11px] text-muted">{ps.id}</p>
                      </div>
                    </div>
                    <div class="flex items-center gap-2">
                      <span class="badge {paymentSystems[ps.id].enabled ? 'badge-success' : 'badge-neutral'} text-[10px]">
                        {paymentSystems[ps.id].enabled ? 'Вкл' : 'Выкл'}
                      </span>
                      <button
                        onclick={() => toggleSystem(ps.id)}
                        disabled={saving[ps.id]}
                        class="btn btn-xs {paymentSystems[ps.id].enabled ? 'btn-danger' : 'btn-primary'}"
                      >
                        {saving[ps.id] ? '...' : paymentSystems[ps.id].enabled ? 'Отключить' : 'Включить'}
                      </button>
                    </div>
                  </div>

                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {#each ps.fields as field}
                      <div class="space-y-1">
                        <label class="label"><span class="label-text text-[11px]">{field.label}</span></label>
                        <input
                          type={field.type}
                          value={paymentSystems[ps.id].config?.[field.key] ?? ''}
                          oninput={(e) => {
                            if (!paymentSystems[ps.id].config) paymentSystems[ps.id].config = {};
                            paymentSystems[ps.id].config[field.key] = e.target.value;
                          }}
                          class="input text-[13px]"
                          placeholder={field.label}
                        />
                      </div>
                    {/each}
                    {#if ps.id === 'yookassa'}
                      <div class="space-y-1">
                        <label class="label"><span class="label-text text-[11px]">СБП (СБП через ЮKassa)</span></label>
                        <button
                          onclick={async () => {
                            const v = botSettings['ps_sbp_enabled'] === '1' ? '0' : '1';
                            await api.updateSettings({ ps_sbp_enabled: v });
                            botSettings['ps_sbp_enabled'] = v;
                            toasts.success(`СБП ${v === '1' ? 'включена' : 'отключена'}`);
                          }}
                          class="mt-1 relative inline-flex h-6 w-10 shrink-0 cursor-pointer items-center rounded-full border border-[#2a2a35] transition-colors duration-200
                            {botSettings['ps_sbp_enabled'] === '1' ? 'bg-accent border-accent' : 'bg-[#1c1c24]'}"
                        >
                          <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200
                            {botSettings['ps_sbp_enabled'] === '1' ? 'translate-x-5' : 'translate-x-0.5'}" />
                        </button>
                      </div>
                    {/if}
                  </div>

                  <div class="flex items-center gap-3">
                    <div class="flex gap-2">
                      <button
                        onclick={() => saveSystem(ps.id)}
                        disabled={saving[ps.id]}
                        class="btn btn-primary btn-sm"
                      >
                        {#if saving[ps.id]}
                          <div class="w-4 h-4 border-2 border-surface-4 border-t-white rounded-full animate-spin"></div>
                        {/if}
                        Сохранить
                      </button>
                      <button
                        onclick={() => testSystem(ps.id)}
                        disabled={testing[ps.id] || !paymentSystems[ps.id]?.enabled}
                        class="btn btn-ghost btn-sm"
                      >
                        {#if testing[ps.id]}
                          <div class="w-4 h-4 border-2 border-surface-4 border-t-accent rounded-full animate-spin"></div>
                        {:else}
                          <Icon name="refreshCw" class="w-3.5 h-3.5" />
                        {/if}
                        Проверить
                      </button>
                    </div>
                    {#if testResults[ps.id] !== undefined && testResults[ps.id] !== null}
                      <div class="flex items-center gap-1.5 text-[12px]">
                        {#if testResults[ps.id].ok}
                          <Icon name="checkCircle" size={14} class="text-[#22c55e]" />
                          <span class="text-[#22c55e]">Подключение успешно</span>
                        {:else}
                          <Icon name="xCircle" size={14} class="text-[#ef4450]" />
                          <span class="text-[#ef4450]">{testResults[ps.id].detail || 'Ошибка подключения'}</span>
                        {/if}
                      </div>
                    {/if}
                  </div>
                </div>
              {/if}
            {/each}
          </div>
        </div>

      {:else if activeTab === 'system'}
        <div class="space-y-4">
          <div>
            <h2 class="text-[17px] font-semibold flex items-center gap-2">
              <Icon name="terminal" class="w-5 h-5 text-accent" /> Конфигурация приложения
            </h2>
            <p class="text-[13px] text-muted mt-0.5">Общая информация о платформе</p>
          </div>

          <div class="card p-5">
            <div class="space-y-0 divide-y divide-[#2a2a35]/50">
              {#each [
                { label: 'Название', value: appConfig?.app_name },
                { label: 'Версия', value: appConfig?.app_version },
                { label: 'Сайт', value: appConfig?.site_url },
                { label: 'Домен', value: appConfig?.domain },
                { label: 'Путь панели', value: appConfig?.panel_path },
                { label: 'Username бота', value: appConfig?.bot_username ? '@' + appConfig.bot_username : '—' },
              ] as item}
                <div class="flex justify-between py-3">
                  <span class="text-[13px] text-muted">{item.label}</span>
                  <span class="text-[13px] font-medium text-right">{item.value ?? '—'}</span>
                </div>
              {/each}
            </div>
          </div>

          <div class="card p-5">
            <h3 class="text-[14px] font-semibold mb-3">Статус интеграций</h3>
            <div class="flex gap-4">
              {#each [
                { label: 'ЮKassa', ok: appConfig?.has_yookassa },
                { label: 'Remnawave', ok: appConfig?.has_remnawave },
              ] as integration}
                <div class="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-[#1c1c24] border border-[#2a2a35]">
                  {#if integration.ok}
                    <Icon name="checkCircle" size={16} class="text-[#22c55e]" />
                    <span class="text-[13px] font-medium text-[#22c55e]">{integration.label}</span>
                  {:else}
                    <Icon name="xCircle" size={16} class="text-[#ef4450]" />
                    <span class="text-[13px] font-medium text-[#ef4450]">{integration.label}</span>
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        </div>

      {:else if activeTab === 'monitoring'}
        <div class="space-y-4">
          <div>
            <h2 class="text-[17px] font-semibold flex items-center gap-2">
              <Icon name="activity" class="w-5 h-5 text-accent" /> Мониторинг и уведомления
            </h2>
            <p class="text-[13px] text-muted mt-0.5">Настройки оповещений и лимитов</p>
          </div>

          <div class="grid gap-3">
            {#each MONITORING_FIELDS as field}
              <div class="card p-4 flex items-start justify-between gap-4">
                <div class="flex-1 min-w-0">
                  <label class="label"><span class="label-text text-[13px]">{field.label}</span></label>
                  {#if field.type === 'checkbox'}
                    <button
                      onclick={() => toggleAndSave(field.key)}
                      class="mt-1 relative inline-flex h-6 w-10 shrink-0 cursor-pointer items-center rounded-full border border-[#2a2a35] transition-colors duration-200 ease-in-out
                        {botSettings[field.key] ? 'bg-accent border-accent' : 'bg-[#1c1c24]'}"
                    >
                      <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 ease-in-out
                        {botSettings[field.key] ? 'translate-x-5' : 'translate-x-0.5'}" />
                    </button>
                  {:else if field.type === 'textarea'}
                    <textarea
                      value={botSettings[field.key] ?? ''}
                      oninput={(e) => botSettings[field.key] = e.target.value}
                      class="textarea mt-1 w-full text-[13px]"
                      rows="3"
                    />
                  {:else}
                    <input
                      type={field.type}
                      value={botSettings[field.key] ?? ''}
                      oninput={(e) => botSettings[field.key] = e.target.value}
                      class="input mt-1 w-full text-[13px]"
                    />
                  {/if}
                </div>
              </div>
            {/each}
          </div>

          <button
            onclick={() => saveSettingsSection(MONITORING_FIELDS.map(f => f.key))}
            disabled={saving._section}
            class="btn btn-primary btn-sm"
          >
            {#if saving._section}
              <div class="w-4 h-4 border-2 border-surface-4 border-t-white rounded-full animate-spin"></div>
            {/if}
            Сохранить все
          </button>
        </div>

      {:else if activeTab === 'notifications'}
        <div class="space-y-4">
          <div>
            <h2 class="text-[17px] font-semibold flex items-center gap-2">
              <Icon name="bell" class="w-5 h-5 text-accent" /> Управление уведомлениями
            </h2>
            <p class="text-[13px] text-muted mt-0.5">Настройка оповещений о сервисах и подписках</p>
          </div>

          <!-- Master toggle -->
          <div class="card p-5">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-[14px] font-semibold">Системные оповещения</h3>
                <p class="text-[12px] text-muted mt-0.5">Уведомления о статусе сервисов (БД, Telegram, VPN панель, платёжки)</p>
              </div>
              <button
                onclick={() => toggleAndSave('notify_monitoring_enabled')}
                class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border border-[#2a2a35] transition-colors duration-200
                  {botSettings['notify_monitoring_enabled'] === '1' ? 'bg-accent border-accent' : 'bg-[#1c1c24]'}"
              >
                <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200
                  {botSettings['notify_monitoring_enabled'] === '1' ? 'translate-x-[22px]' : 'translate-x-0.5'}" />
              </button>
            </div>
          </div>

          {#if botSettings['notify_monitoring_enabled'] === '1'}
            <!-- Per-service toggles -->
            <div class="card p-5 space-y-3">
              <h3 class="text-[14px] font-semibold">Оповещения по сервисам</h3>
              <p class="text-[12px] text-muted">Выберите о каких сервисах присылать уведомления</p>
              {#each [
                { key: 'notify_svc_database', label: 'База данных', icon: 'database' },
                { key: 'notify_svc_telegram_bot', label: 'Telegram бот', icon: 'bot' },
                { key: 'notify_svc_vpn_panel', label: 'VPN панель (Remnawave)', icon: 'shield' },
                { key: 'notify_svc_yookassa', label: 'ЮKassa', icon: 'creditCard' },
                { key: 'notify_svc_cryptobot', label: 'CryptoBot', icon: 'wallet' },
                { key: 'notify_svc_freekassa', label: 'FreeKassa', icon: 'dollarSign' },
              ] as svc}
                <div class="flex items-center justify-between py-2 px-3 rounded-lg bg-surface-3/30 border border-surface-4/10">
                  <div class="flex items-center gap-2.5">
                    <Icon name={svc.icon} class="w-4 h-4 text-muted" />
                    <span class="text-[13px]">{svc.label}</span>
                  </div>
                  <button
                    onclick={() => toggleAndSave(svc.key)}
                    class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border border-[#2a2a35] transition-colors duration-200
                      {botSettings[svc.key] === '1' ? 'bg-accent border-accent' : 'bg-[#1c1c24]'}"
                  >
                    <span class="inline-block h-3 w-3 transform rounded-full bg-white transition-transform duration-200
                      {botSettings[svc.key] === '1' ? 'translate-x-[18px]' : 'translate-x-0.5'}" />
                  </button>
                </div>
              {/each}
            </div>

            <!-- Alert settings -->
            <div class="card p-5 space-y-4">
              <h3 class="text-[14px] font-semibold">Параметры оповещений</h3>
              <div class="space-y-3">
                <div class="space-y-1">
                  <label class="label"><span class="label-text text-[13px]">Интервал повторных оповещений (сек)</span></label>
                  <input
                    type="number"
                    value={botSettings['notify_cooldown_seconds'] ?? '300'}
                    oninput={(e) => botSettings['notify_cooldown_seconds'] = e.target.value}
                    class="input w-full text-[13px]"
                    min="60"
                    placeholder="300"
                  />
                  <p class="text-[11px] text-muted">Минимум 60 сек. Повторное оповещение о том же сервисе придет только через это время.</p>
                </div>

                <div class="flex items-center justify-between py-2 px-3 rounded-lg bg-surface-3/30 border border-surface-4/10">
                  <div>
                    <span class="text-[13px]">Оповещать о деградации</span>
                    <p class="text-[11px] text-muted">Когда сервис работает медленно, но не упал</p>
                  </div>
                  <button
                    onclick={() => toggleAndSave('notify_on_degraded')}
                    class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border border-[#2a2a35] transition-colors duration-200
                      {botSettings['notify_on_degraded'] === '1' ? 'bg-accent border-accent' : 'bg-[#1c1c24]'}"
                  >
                    <span class="inline-block h-3 w-3 transform rounded-full bg-white transition-transform duration-200
                      {botSettings['notify_on_degraded'] === '1' ? 'translate-x-[18px]' : 'translate-x-0.5'}" />
                  </button>
                </div>
              </div>
            </div>

            <!-- Subscription expiry alerts -->
            <div class="card p-5 space-y-3">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-[14px] font-semibold">Уведомления об истечении подписок</h3>
                  <p class="text-[12px] text-muted">Оповещать пользователей перед окончанием подписки</p>
                </div>
                <button
                  onclick={() => toggleAndSave('notify_expiry_enabled')}
                  class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border border-[#2a2a35] transition-colors duration-200
                    {botSettings['notify_expiry_enabled'] === '1' ? 'bg-accent border-accent' : 'bg-[#1c1c24]'}"
                >
                  <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200
                    {botSettings['notify_expiry_enabled'] === '1' ? 'translate-x-[22px]' : 'translate-x-0.5'}" />
                </button>
              </div>
              {#if botSettings['notify_expiry_enabled'] === '1'}
                <div class="space-y-2 pl-1">
                  <div class="space-y-1">
                    <label class="label"><span class="label-text text-[13px]">Дни до истечения</span></label>
                    <input
                      type="text"
                      value={botSettings['notify_expiry_days'] ?? '7,3,1'}
                      oninput={(e) => botSettings['notify_expiry_days'] = e.target.value}
                      class="input w-full text-[13px]"
                      placeholder="7,3,1"
                    />
                    <p class="text-[11px] text-muted">Через запятую. Уведомления придут за указанное количество дней до истечения.</p>
                  </div>
                  <div class="space-y-1">
                    <label class="label"><span class="label-text text-[13px]">Текст уведомления</span></label>
                    <textarea
                      value={botSettings['notify_expiry_message'] ?? ''}
                      oninput={(e) => botSettings['notify_expiry_message'] = e.target.value}
                      class="textarea w-full text-[13px]"
                      rows="4"
                      placeholder="Текст уведомления..."
                    ></textarea>
                    <p class="text-[11px] text-muted">Переменные: {'{days}'}, {'{name}'}, {'{date}'}</p>
                  </div>
                </div>
              {/if}
            </div>

            <!-- Chat IDs -->
            <div class="card p-5 space-y-3">
              <h3 class="text-[14px] font-semibold">Получатели оповещений</h3>
              <div class="space-y-1">
                <label class="label"><span class="label-text text-[13px]">Chat ID (через запятую)</span></label>
                <input
                  type="text"
                  value={botSettings['notify_chat_ids'] ?? ''}
                  oninput={(e) => botSettings['notify_chat_ids'] = e.target.value}
                  class="input w-full text-[13px]"
                  placeholder="Оставьте пустым для использования admin IDs из .env"
                />
                <p class="text-[11px] text-muted">ID чатов куда слать уведомления. Если пусто — используется TELEGRAM_ADMIN_IDS из .env</p>
              </div>
            </div>

            <button
              onclick={() => saveSettingsSection([
                'notify_monitoring_enabled', 'notify_svc_database', 'notify_svc_telegram_bot',
                'notify_svc_vpn_panel', 'notify_svc_yookassa', 'notify_svc_cryptobot', 'notify_svc_freekassa',
                'notify_cooldown_seconds', 'notify_on_degraded', 'notify_expiry_enabled',
                'notify_expiry_days', 'notify_expiry_message', 'notify_chat_ids',
              ])}
              disabled={saving._section}
              class="btn btn-primary btn-sm"
            >
              {#if saving._section}
                <div class="w-4 h-4 border-2 border-surface-4 border-t-white rounded-full animate-spin"></div>
              {/if}
              Сохранить все
            </button>
          {/if}
        </div>

      {:else if activeTab === 'trial'}
        <div class="space-y-4">
          <div>
            <h2 class="text-[17px] font-semibold flex items-center gap-2">
              <Icon name="zap" class="w-5 h-5 text-accent" /> Пробный период
            </h2>
            <p class="text-[13px] text-muted mt-0.5">Настройка бесплатного тестового доступа</p>
          </div>

          <div class="grid gap-3">
            {#each TRIAL_FIELDS as field}
              <div class="card p-4 flex items-start justify-between gap-4">
                <div class="flex-1 min-w-0">
                  <label class="label"><span class="label-text text-[13px]">{field.label}</span></label>
                  {#if field.type === 'checkbox'}
                    <button
                      onclick={() => toggleAndSave(field.key)}
                      class="mt-1 relative inline-flex h-6 w-10 shrink-0 cursor-pointer items-center rounded-full border border-[#2a2a35] transition-colors duration-200 ease-in-out
                        {botSettings[field.key] ? 'bg-accent border-accent' : 'bg-[#1c1c24]'}"
                    >
                      <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 ease-in-out
                        {botSettings[field.key] ? 'translate-x-5' : 'translate-x-0.5'}" />
                    </button>
                  {:else}
                    <input
                      type={field.type}
                      value={botSettings[field.key] ?? ''}
                      oninput={(e) => botSettings[field.key] = e.target.value}
                      class="input mt-1 w-full text-[13px]"
                    />
                  {/if}
                </div>
              </div>
            {/each}
          </div>

          <button
            onclick={() => saveSettingsSection(TRIAL_FIELDS.map(f => f.key))}
            disabled={saving._section}
            class="btn btn-primary btn-sm"
          >
            {#if saving._section}
              <div class="w-4 h-4 border-2 border-surface-4 border-t-white rounded-full animate-spin"></div>
            {/if}
            Сохранить все
          </button>
        </div>

      {:else if activeTab === 'referrals'}
        <div class="space-y-4">
          <div>
            <h2 class="text-[17px] font-semibold flex items-center gap-2">
              <Icon name="users" class="w-5 h-5 text-accent" /> Реферальная программа
            </h2>
            <p class="text-[13px] text-muted mt-0.5">Настройка вознаграждений за приглашение пользователей</p>
          </div>

          <!-- Bonus type & value -->
          <div class="card p-5 space-y-5">
            <h3 class="text-[14px] font-semibold">Вознаграждение за реферала</h3>

            <div class="space-y-1">
              <label class="label"><span class="label-text text-[13px]">Тип бонуса</span></label>
              <select
                bind:value={botSettings['referral_bonus_type']}
                class="select w-full text-[13px]"
              >
                <option value="days">Дни подписки (продлить VPN ключ реферера)</option>
                <option value="balance">Баланс (начислить рубли на баланс)</option>
                <option value="percent">Баланс (%)</option>
              </select>
              <p class="text-[11px] text-muted mt-1">
                {#if botSettings['referral_bonus_type'] === 'days'}
                  Реферер получит продление текущей подписки на указанное количество дней
                {:else if botSettings['referral_bonus_type'] === 'balance'}
                  На баланс реферера будет начислена фиксированная сумма в рублях
                {:else}
                  На баланс реферера будет начислен процент от суммы (значение — размер процента)
                {/if}
              </p>
            </div>

            <div class="space-y-1">
              <label class="label"><span class="label-text text-[13px]">
                {#if botSettings['referral_bonus_type'] === 'days'}
                  Количество дней
                {:else if botSettings['referral_bonus_type'] === 'balance'}
                  Сумма (₽)
                {:else}
                  Процент (%)
                {/if}
              </span></label>
              <input
                type="number"
                bind:value={botSettings['referral_bonus_value']}
                class="input w-full text-[13px]"
                min="0"
                max="999999"
                placeholder="3"
              />
            </div>

            <div class="bg-surface-2/50 rounded-[10px] p-4 border border-surface-4/30">
              <div class="flex items-start gap-3">
                <Icon name="info" class="w-4 h-4 text-accent mt-0.5 shrink-0" />
                <div class="text-[12px] text-muted space-y-1">
                  <p><b class="text-text">Текущая настройка:</b>
                    {#if botSettings['referral_bonus_type'] === 'days'}
                      <span class="text-accent">{botSettings['referral_bonus_value'] || '3'} дн.</span> продление подписки
                    {:else if botSettings['referral_bonus_type'] === 'balance'}
                      <span class="text-accent">{botSettings['referral_bonus_value'] || '3'} ₽</span> на баланс
                    {:else}
                      <span class="text-accent">{botSettings['referral_bonus_value'] || '3'}%</span> на баланс
                    {/if}
                  </p>
                  <p>Бонус начисляется <b class="text-text">рефереру</b> (тому, кто пригласил) при регистрации нового пользователя по реферальной ссылке.</p>
                  <p>Если тип — «Дни» и у реферера нет активной подписки, бонус не будет начислен.</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Welcome message -->
          <div class="card p-5 space-y-4">
            <h3 class="text-[14px] font-semibold">Уведомление рефереру</h3>
            <p class="text-[12px] text-muted">Текст, который получит реферер при успешном приглашении</p>

            <textarea
              value={botSettings['referral_welcome_message'] ?? ''}
              oninput={(e) => botSettings['referral_welcome_message'] = e.target.value}
              class="textarea w-full text-[13px]"
              rows="5"
              placeholder="🎉 По вашей реферальной ссылке зарегистрировался новый пользователь!"
            ></textarea>
            <p class="text-[11px] text-muted">
              Переменные: <code class="bg-surface-3 px-1 rounded text-[10px]">{'{name}'}</code> — имя приглашённого,
              <code class="bg-surface-3 px-1 rounded text-[10px]">{'{username}'}</code> — username,
              <code class="bg-surface-3 px-1 rounded text-[10px]">{'{bonus}'}</code> — размер бонуса
            </p>
          </div>

          <!-- Limits -->
          <div class="card p-5 space-y-4">
            <h3 class="text-[14px] font-semibold">Лимиты</h3>

            <div class="space-y-1">
              <label class="label"><span class="label-text text-[13px]">Макс. рефералов на пользователя</span></label>
              <input
                type="number"
                bind:value={botSettings['referral_max_per_user']}
                class="input w-full text-[13px]"
                min="1"
                max="100000"
                placeholder="500"
              />
              <p class="text-[11px] text-muted">Максимальное количество приглашённых пользователей для одного реферера (по умолчанию 500).</p>
            </div>
          </div>

          <button
            onclick={() => saveSettingsSection([
              'referral_bonus_type', 'referral_bonus_value',
              'referral_welcome_message', 'referral_max_per_user',
            ])}
            disabled={saving._section}
            class="btn btn-primary btn-sm"
          >
            {#if saving._section}
              <div class="w-4 h-4 border-2 border-surface-4 border-t-white rounded-full animate-spin"></div>
            {/if}
            Сохранить все
          </button>
        </div>
      {/if}
    </div>
</div>
