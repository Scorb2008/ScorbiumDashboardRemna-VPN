<script>
  import { router } from '../lib/stores.js';
  import { api } from '../lib/api.js';

  let { currentPath = $bindable('/dashboard') } = $props();

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
    { path: '/users', label: 'Пользователи', icon: 'M12 4.354a4 4 0 110 7.292 4 4 0 010-7.292zM15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z' },
    { path: '/vpn', label: 'VPN Ключи', icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z' },
    { path: '/plans', label: 'Тарифы', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01' },
    { path: '/payments', label: 'Платежи', icon: 'M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z' },
    { path: '/remnawave', label: 'Remnawave', icon: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01' },
    { path: '/support', label: 'Поддержка', icon: 'M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z' },
    { path: '/promos', label: 'Промокоды', icon: 'M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z' },
    { path: '/broadcasts', label: 'Рассылки', icon: 'M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z' },
    { path: '/referrals', label: 'Рефералы', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z' },
  ];

  let theme = $state(localStorage.getItem('theme') || 'dark');

  function toggleTheme() {
    theme = theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }

  $effect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  });

  function handleLogout() {
    api.logout();
  }
</script>

<aside class="fixed left-0 top-0 bottom-0 w-[var(--sidebar-width)] glass-strong flex flex-col z-40">
  <div class="p-5 flex items-center gap-3 border-b border-base-300/50">
    <div class="w-9 h-9 rounded-xl gradient-primary flex items-center justify-center shadow-lg shadow-primary/25">
      <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    </div>
    <div>
      <h1 class="text-lg font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">Scorbium</h1>
      <p class="text-[10px] text-base-content/40 uppercase tracking-widest">Dashboard</p>
    </div>
  </div>

  <nav class="flex-1 overflow-y-auto py-3 px-3 space-y-0.5">
    {#each navItems as item}
      <a
        href="#{item.path}"
        class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-200 group
          {currentPath === item.path || currentPath.startsWith(item.path + '/')
            ? 'bg-primary/10 text-primary font-medium shadow-sm shadow-primary/5'
            : 'text-base-content/60 hover:text-base-content hover:bg-base-300/50'}">
        <svg class="w-5 h-5 flex-shrink-0 transition-colors {currentPath === item.path ? 'text-primary' : 'text-base-content/40 group-hover:text-base-content/70'}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d={item.icon} />
        </svg>
        <span>{item.label}</span>
      </a>
    {/each}
  </nav>

  <div class="p-3 border-t border-base-300/50 space-y-1">
    <button onclick={toggleTheme} class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-base-content/60 hover:text-base-content hover:bg-base-300/50 transition-all w-full">
      {#if theme === 'dark'}
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <span>Светлая тема</span>
      {:else}
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
        <span>Тёмная тема</span>
      {/if}
    </button>
    <button onclick={handleLogout} class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-base-content/60 hover:text-error hover:bg-error/10 transition-all w-full">
      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
      </svg>
      <span>Выйти</span>
    </button>
  </div>
</aside>
