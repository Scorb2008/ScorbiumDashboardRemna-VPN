<script>
  import { onMount } from 'svelte';
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import Spinner from '../components/Spinner.svelte';
  import Icon from '../components/Icon.svelte';

  let botInfo = $state(null);
  let loading = $state(true);

  async function loadBotInfo() {
    loading = true;
    try { botInfo = await api.getBotInfo(); }
    catch (e) { toasts.error('Ошибка загрузки: ' + e.message); }
    finally { loading = false; }
  }

  onMount(loadBotInfo);
</script>

<Spinner {loading} />

<div class="page-enter space-y-5">
  <div>
    <h1 class="text-[28px] font-bold tracking-tight">Telegram Бот</h1>
    <p class="text-sm text-muted mt-1">Информация о подключённом Telegram-боте</p>
  </div>

  {#if botInfo}
    <div class="card p-5 space-y-4">
      <div class="flex items-center gap-4">
        <div class="w-14 h-14 rounded-[12px] bg-surface-3 border border-surface-4 flex items-center justify-center">
          <Icon name="bot" class="w-7 h-7 text-accent" />
        </div>
        <div>
          <h3 class="text-[15px] font-semibold">{botInfo.first_name || '—'}</h3>
          <p class="text-xs text-muted">@{botInfo.username || '—'}</p>
        </div>
      </div>

      <div class="border-t border-surface-4/50"></div>

      <div class="space-y-0 text-[13px]">
        {#each [
          ['Bot ID', botInfo.id || '—'],
          ['Имя', botInfo.first_name || '—'],
          ['Username', botInfo.username ? '@' + botInfo.username : '—'],
          ['Can join groups', botInfo.can_join_groups ? 'Да' : 'Нет'],
          ['Can read messages', botInfo.can_read_all_group_messages ? 'Да' : 'Нет'],
          ['Supports inline', botInfo.supports_inline_queries ? 'Да' : 'Нет'],
          ['Webhook', botInfo.webhook_url || 'Не настроен'],
        ] as [label, value]}
          <div class="flex justify-between py-2.5 border-b border-surface-4/30">
            <span class="text-muted">{label}</span>
            <span>{value}</span>
          </div>
        {/each}
      </div>
    </div>

    <div class="card p-5">
      <h3 class="text-[15px] font-semibold mb-3">Команды бота</h3>
      <div class="space-y-0 text-[13px]">
        {#each [
          ['/start', 'Главное меню'],
          ['/buy', 'Купить подписку'],
          ['/my_keys', 'Мои VPN ключи'],
          ['/profile', 'Профиль'],
          ['/support', 'Поддержка'],
          ['/language', 'Смена языка'],
        ] as [cmd, desc]}
          <div class="flex justify-between py-2 border-b border-surface-4/30 last:border-0">
            <code class="font-mono text-xs text-accent">{cmd}</code>
            <span class="text-muted">{desc}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>
