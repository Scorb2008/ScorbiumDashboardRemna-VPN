<script>
  import { router } from '../lib/stores.js';
  import { api } from '../lib/api.svelte.js';
  import Icon from './Icon.svelte';

  let { currentPath = $bindable('/dashboard') } = $props();

  const groups = [
    {
      label: '',
      items: [
        { path: '/dashboard', label: 'Dashboard', icon: 'barChart3' },
      ],
    },
    {
      label: 'Управление',
      items: [
        { path: '/users', label: 'Пользователи', icon: 'users' },
        { path: '/vpn', label: 'VPN Ключи', icon: 'key' },
        { path: '/plans', label: 'Тарифы', icon: 'creditCard' },
        { path: '/payments', label: 'Платежи', icon: 'dollarSign' },
      ],
    },
    {
      label: 'Инфраструктура',
      items: [
        { path: '/remnawave', label: 'Remnawave', icon: 'server' },
        { path: '/telegram', label: 'Telegram Bot', icon: 'phone' },
      ],
    },
    {
      label: 'Маркетинг',
      items: [
        { path: '/promos', label: 'Промокоды', icon: 'tag' },
        { path: '/broadcasts', label: 'Рассылки', icon: 'megaphone' },
        { path: '/referrals', label: 'Рефералы', icon: 'userPlus' },
      ],
    },
    {
      label: '',
      items: [
        { path: '/support', label: 'Поддержка', icon: 'lifeBuoy' },
      ],
    },
  ];

  function handleLogout() {
    api.logout();
  }
</script>

<aside class="fixed left-0 top-0 bottom-0 w-[var(--sidebar-width)] bg-surface-0 border-r border-surface-4/40 flex flex-col z-40 select-none">
  <!-- Logo -->
  <div class="px-5 h-16 flex items-center gap-3 border-b border-surface-4/40">
    <div class="w-8 h-8 rounded-[10px] bg-white flex items-center justify-center">
      <Icon name="zap" size={18} class="text-black" />
    </div>
    <div class="min-w-0">
      <span class="text-sm font-semibold text-accent block leading-tight">Scorbium</span>
      <span class="text-[10px] text-muted uppercase tracking-widest">VPN Dashboard</span>
    </div>
  </div>

  <!-- Navigation -->
  <nav class="flex-1 overflow-y-auto py-4 px-3 space-y-5">
    {#each groups as group}
      <div>
        {#if group.label}
          <p class="px-3 mb-1.5 text-[11px] font-medium text-muted/60 uppercase tracking-wider">{group.label}</p>
        {/if}
        <div class="space-y-0.5">
          {#each group.items as item}
            {@const active = currentPath === item.path || currentPath.startsWith(item.path + '/')}
            <a
              href="#{item.path}"
              class="flex items-center gap-2.5 px-3 py-[7px] rounded-[10px] text-[13px] font-medium transition-all duration-150
                {active
                  ? 'bg-white text-black shadow-sm'
                  : 'text-muted hover:text-accent hover:bg-surface-3'}">
              <Icon name={item.icon} size={18} class="{active ? 'text-black' : ''}" />
              <span>{item.label}</span>
            </a>
          {/each}
        </div>
      </div>
    {/each}
  </nav>

  <!-- Footer -->
  <div class="px-3 py-3 border-t border-surface-4/40">
    <button onclick={handleLogout} class="flex items-center gap-2.5 px-3 py-[7px] rounded-[10px] text-[13px] font-medium text-muted hover:text-[#ef4444] hover:bg-[#ef4444]/10 transition-all duration-150 w-full">
      <Icon name="logout" size={18} />
      <span>Выйти</span>
    </button>
  </div>
</aside>
