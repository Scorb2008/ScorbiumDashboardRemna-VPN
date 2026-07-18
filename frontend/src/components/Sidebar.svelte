<script>
  import { onMount } from 'svelte';
  import { router } from '../lib/stores.js';
  import { api } from '../lib/api.svelte.js';
  import Icon from './Icon.svelte';

  let { currentPath = $bindable('/dashboard'), onToggle } = $props();

  let logoUrl = $state('');

  onMount(async () => {
    try {
      const s = await api.getSettings();
      logoUrl = s?.logo_url || '';
    } catch {}
  });

  const groups = [
    {
      label: '',
      items: [
        { path: '/dashboard', label: 'Обзор', icon: 'layout-dashboard' },
      ],
    },
    {
      label: 'Управление',
      items: [
        { path: '/users', label: 'Пользователи', icon: 'users' },
        { path: '/vpn', label: 'Подписки', icon: 'key-round' },
        { path: '/plans', label: 'Тарифы', icon: 'ticket' },
        { path: '/payments', label: 'Платежи', icon: 'wallet' },
      ],
    },
    {
      label: 'Инфраструктура',
      items: [
        { path: '/remnawave', label: 'Remnawave', icon: 'server' },
        { path: '/groups', label: 'Группы VPN', icon: 'shield' },
        { path: '/telegram', label: 'Telegram', icon: 'bot' },
      ],
    },
    {
      label: 'Маркетинг',
      items: [
        { path: '/promos', label: 'Промокоды', icon: 'percent' },
        { path: '/broadcasts', label: 'Рассылки', icon: 'send' },
        { path: '/referrals', label: 'Рефералы', icon: 'git-branch' },
      ],
    },
    {
      label: 'Система',
      items: [
        { path: '/settings', label: 'Настройки', icon: 'settings' },
        { path: '/support', label: 'Поддержка', icon: 'headset' },
        { path: '/database', label: 'База данных', icon: 'database' },
        { path: '/admins', label: 'Администраторы', icon: 'shield' },
      ],
    },
  ];

  function navigate(path) {
    router.navigate(path);
  }
</script>

<div class="flex flex-col h-full">
  <div class="flex items-center gap-3 px-5 py-5 border-b border-[#2a2a35]">
    {#if logoUrl}
      <img src={logoUrl} alt="Logo" class="w-8 h-8 rounded-[10px] object-cover shrink-0" />
    {:else}
      <div class="w-8 h-8 rounded-[10px] bg-accent flex items-center justify-center shrink-0">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/></svg>
      </div>
    {/if}
    <div>
      <p class="text-[14px] font-semibold text-text leading-tight">Scorbium</p>
      <p class="text-[11px] text-muted leading-tight">VPN Dashboard</p>
    </div>
  </div>

  <nav class="flex-1 overflow-y-auto py-3 px-2 space-y-4">
    {#each groups as group}
      {#if group.label}
        <div class="px-3 mb-1">
          <p class="text-[10px] font-semibold uppercase tracking-[0.08em] text-muted">{group.label}</p>
        </div>
      {/if}
      <div class="space-y-0.5">
        {#each group.items as item}
          {@const active = currentPath === item.path}
          <button
            onclick={() => navigate(item.path)}
            class="w-full flex items-center gap-2.5 px-3 py-2 text-[13px] font-medium rounded-[10px] transition-all duration-150
              {active
                ? 'bg-accent/10 text-accent hover:bg-accent/15'
                : 'text-muted hover:text-text hover:bg-surface-2'}">
            <Icon name={item.icon} size={18} class="flex-shrink-0 {active ? 'text-accent' : 'text-muted'}" />
            <span>{item.label}</span>
          </button>
        {/each}
      </div>
    {/each}
  </nav>

  <div class="border-t border-[#2a2a35] p-3">
    <button
      onclick={() => { api.logout(); router.navigate('/login'); }}
      class="w-full flex items-center gap-2.5 px-3 py-2 text-[13px] font-medium rounded-[10px] text-muted hover:text-danger hover:bg-danger/5 transition-all duration-150">
      <Icon name="log-out" size={18} class="flex-shrink-0" />
      <span>Выйти</span>
    </button>
  </div>
</div>

<style>
  nav::-webkit-scrollbar { width: 3px; }
  nav::-webkit-scrollbar-thumb { background: #2f2f39; border-radius: 2px; }
</style>
