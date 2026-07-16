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
    { id: 'monitoring', label: 'Мониторинг', icon: 'activity' },
    { id: 'trial', label: 'Пробный период', icon: 'zap' },
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
                      onclick={() => botSettings[field.key] = !botSettings[field.key]}
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
                      onclick={() => botSettings[field.key] = !botSettings[field.key]}
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
      {/if}
    </div>
</div>
