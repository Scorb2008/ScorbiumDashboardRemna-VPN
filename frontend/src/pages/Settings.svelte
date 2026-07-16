<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';

  let loading = $state(true);
  let appConfig = $state(null);
  let paymentSystems = $state({});
  let testing = $state({});
  let saving = $state({});

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

  async function loadAll() {
    loading = true;
    try {
      const [c, p] = await Promise.all([
        api.getAppConfig(),
        api.getPaymentSystemsDetail(),
      ]);
      appConfig = c;
      paymentSystems = p || {};
    } catch (e) { toasts.error('Ошибка загрузки настроек'); }
    finally { loading = false; }
  }

  onMount(loadAll);

  async function toggleSystem(name) {
    const ps = paymentSystems[name];
    if (!ps) return;
    saving[name] = true;
    try {
      await api.configurePaymentSystem(name, { enabled: !ps.enabled });
      ps.enabled = !ps.enabled;
      toasts.success(`${name}: ${ps.enabled ? 'включена' : 'отключена'}`);
    } catch (e) { toasts.error(e.message); }
    finally { saving[name] = false; }
  }

  async function saveSystem(name) {
    const ps = paymentSystems[name];
    if (!ps) return;
    saving[name] = true;
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
    try {
      const r = await api.testPaymentSystem(name);
      if (r.ok) toasts.success(r.detail || 'Подключение успешно');
      else toasts.error(r.detail || 'Ошибка подключения');
    } catch (e) { toasts.error(e.message); }
    finally { testing[name] = false; }
  }
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div>
    <h1 class="text-[28px] font-bold tracking-tight">Настройки</h1>
    <p class="text-sm text-muted mt-1">Управление платёжными системами и конфигурацией</p>
  </div>

  <!-- Payment Systems -->
  <div class="space-y-3">
    <h2 class="text-[17px] font-semibold flex items-center gap-2">
      <Icon name="wallet" class="w-5 h-5 text-accent" /> Платёжные системы
    </h2>
    <p class="text-[13px] text-muted -mt-2">Подключение и настройка способов оплаты</p>

    <div class="grid gap-4">
      {#each PAYMENT_SYSTEMS as ps}
        {@const configKey = `_ps_${ps.id}`}
        {#if paymentSystems[ps.id]}
          <div class="card p-5 space-y-4 border {paymentSystems[ps.id].enabled ? 'border-accent/30' : 'border-surface-4/30'}">
            <!-- System Header -->
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-[10px] bg-surface-3 border border-surface-4 flex items-center justify-center">
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
                  class="btn btn-xs {paymentSystems[ps.id].enabled ? 'btn-danger' : 'btn-primary'}">
                  {saving[ps.id] ? '...' : paymentSystems[ps.id].enabled ? 'Отключить' : 'Включить'}
                </button>
              </div>
            </div>

            <!-- Credential Fields -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {#each ps.fields as field}
                <div class="space-y-1">
                  <label class="label"><span class="label-text text-[11px]">{field.label}</span></label>
                  <input
                    type={field.type}
                    value={paymentSystems[ps.id].config?.[field.key] ?? ''}
                    oninput={(e) => { if (!paymentSystems[ps.id].config) paymentSystems[ps.id].config = {}; paymentSystems[ps.id].config[field.key] = e.target.value; }}
                    class="input text-[13px]"
                    placeholder={field.label}
                  />
                </div>
              {/each}
            </div>

          <!-- Actions -->
          <div class="flex gap-2">
            <button
              onclick={() => saveSystem(ps.id)}
              disabled={saving[ps.id]}
              class="btn btn-primary btn-sm">
              {#if saving[ps.id]}
                <div class="w-4 h-4 border-2 border-surface-4 border-t-white rounded-full animate-spin"></div>
              {/if}
              Сохранить
            </button>
            <button
              onclick={() => testSystem(ps.id)}
              disabled={testing[ps.id] || !paymentSystems[ps.id]?.enabled}
              class="btn btn-ghost btn-sm">
              {#if testing[ps.id]}
                <div class="w-4 h-4 border-2 border-surface-4 border-t-accent rounded-full animate-spin"></div>
              {:else}
                <Icon name="refreshCw" class="w-3.5 h-3.5" />
              {/if}
              Проверить
            </button>
          </div>
        </div>
      {/if}
      {/each}
    </div>
  </div>

  <!-- App Config -->
  <div class="card p-5 space-y-4">
    <h3 class="text-[15px] font-semibold flex items-center gap-2">
      <Icon name="terminal" class="w-4 h-4 text-accent" /> Конфигурация приложения
    </h3>
    <div class="space-y-0 divide-y divide-surface-4/30">
      {#each [
        ['Название', appConfig?.app_name],
        ['Версия', appConfig?.app_version],
        ['Сайт', appConfig?.site_url],
        ['Домен', appConfig?.domain],
        ['Путь панели', appConfig?.panel_path],
        ['Username бота', appConfig?.bot_username],
        ['ЮKassa', appConfig?.has_yookassa ? '✓ Настроена' : '✗ Не настроена'],
        ['Remnawave', appConfig?.has_remnawave ? '✓ Подключена' : '✗ Не подключена'],
      ] as [label, value]}
        <div class="flex justify-between py-3">
          <span class="text-[13px] text-muted">{label}</span>
          <span class="text-[13px] font-medium text-right">{value ?? '—'}</span>
        </div>
      {/each}
    </div>
  </div>
</div>
