<script>
  import { router } from '../lib/stores.js';

  let { currentPath = $bindable('/dashboard') } = $props();

  const navItems = [
    { path: '/dashboard', icon: '📊', label: 'Дашборд' },
    { path: '/users', icon: '👥', label: 'Пользователи' },
    { path: '/vpn', icon: '🔑', label: 'VPN Ключи' },
    { path: '/plans', icon: '📦', label: 'Тарифы' },
    { path: '/payments', icon: '💳', label: 'Платежи' },
    { path: '/remnawave', icon: '🌐', label: 'Remnawave' },
    { path: '/support', icon: '🎫', label: 'Поддержка' },
    { path: '/promos', icon: '🎁', label: 'Промокоды' },
    { path: '/broadcasts', icon: '📢', label: 'Рассылки' },
  ];

  function isActive(path) {
    return currentPath === path || currentPath.startsWith(path + '/');
  }

  function handleLogout() {
    localStorage.removeItem('admin_token');
    router.navigate('/login');
  }
</script>

<aside class="bg-base-200 h-full flex flex-col border-r border-base-300" style="width: var(--sidebar-width)">
  <div class="p-4 border-b border-base-300">
    <div class="flex items-center gap-2">
      <span class="text-2xl">⚡</span>
      <span class="font-bold text-lg">Scorbium</span>
    </div>
    <div class="text-xs opacity-50 mt-1">VPN Dashboard</div>
  </div>

  <nav class="flex-1 overflow-y-auto p-2">
    {#each navItems as item}
      <a
        href="#{item.path}"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 mb-0.5
          {isActive(item.path) ? 'bg-primary/15 text-primary font-medium' : 'text-base-content/70 hover:bg-base-300 hover:text-base-content'}">
        <span class="text-lg">{item.icon}</span>
        <span>{item.label}</span>
      </a>
    {/each}
  </nav>

  <div class="p-3 border-t border-base-300">
    <button
      onclick={handleLogout}
      class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-base-content/60 hover:bg-error/10 hover:text-error transition-all w-full">
      <span class="text-lg">🚪</span>
      <span>Выйти</span>
    </button>
  </div>
</aside>
