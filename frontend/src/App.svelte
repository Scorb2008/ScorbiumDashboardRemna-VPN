<script>
  import { onMount } from 'svelte';
  import { router } from './lib/stores.js';
  import { api } from './lib/api.svelte.js';
  import Sidebar from './components/Sidebar.svelte';
  import Toasts from './components/Toasts.svelte';
  import Icon from './components/Icon.svelte';

  import Login from './pages/Login.svelte';
  import Dashboard from './pages/Dashboard.svelte';
  import Users from './pages/Users.svelte';
  import VPN from './pages/VPN.svelte';
  import Plans from './pages/Plans.svelte';
  import Payments from './pages/Payments.svelte';
  import Remnawave from './pages/Remnawave.svelte';
  import Support from './pages/Support.svelte';
  import Promos from './pages/Promos.svelte';
  import Broadcasts from './pages/Broadcasts.svelte';
  import Referrals from './pages/Referrals.svelte';
  import Telegram from './pages/Telegram.svelte';
  import Settings from './pages/Settings.svelte';
  import Database from './pages/Database.svelte';
  import Admins from './pages/Admins.svelte';

  let currentPath = $state('/dashboard');
  let authenticated = $state(api.isAuthenticated);
  let sidebarOpen = $state(true);
  let isMobile = $state(false);

  onMount(() => {
    const saved = localStorage.getItem('sidebar_open');
    if (saved !== null) sidebarOpen = saved === 'true';

    function checkMobile() {
      isMobile = window.innerWidth < 768;
    }
    checkMobile();
    window.addEventListener('resize', checkMobile);

    router.init();
    const unsub = router.subscribe((r) => {
      currentPath = r.path;
      authenticated = api.isAuthenticated;
      if (isMobile) sidebarOpen = false;
    });
    return () => {
      unsub();
      window.removeEventListener('resize', checkMobile);
    };
  });

  function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
    localStorage.setItem('sidebar_open', String(sidebarOpen));
  }

  function closeSidebar() {
    sidebarOpen = false;
  }
</script>

<Toasts />

{#if !authenticated || currentPath === '/login'}
  <Login />
{:else}
  <div class="flex h-screen overflow-hidden bg-bg">
    <!-- Mobile overlay backdrop -->
    {#if sidebarOpen && isMobile}
      <div
        class="fixed inset-0 bg-black/60 z-20 md:hidden"
        onclick={closeSidebar}
      ></div>
    {/if}

    <!-- Sidebar -->
    <aside
      class="fixed md:relative z-30 h-full transition-all duration-300 ease-in-out
        {sidebarOpen
          ? 'translate-x-0'
          : '-translate-x-full md:translate-x-0 md:w-0 md:overflow-hidden'}"
      class:w-0 md:overflow-hidden={!sidebarOpen}
    >
      <div class="w-[260px] md:w-[260px] h-full border-r border-[#2a2a35] bg-bg">
        <Sidebar bind:currentPath />
      </div>
    </aside>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Top bar with hamburger -->
      <header class="flex items-center gap-3 px-4 py-3 border-b border-[#2a2a35] bg-bg/80 backdrop-blur-sm md:hidden sticky top-0 z-10">
        <button onclick={toggleSidebar} class="p-1.5 rounded-lg text-muted hover:text-text hover:bg-surface-2 transition-colors">
          <Icon name={sidebarOpen ? 'x' : 'menu'} size={22} />
        </button>
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 rounded-[6px] bg-accent flex items-center justify-center">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/></svg>
          </div>
          <span class="text-[13px] font-semibold">Scorbium</span>
        </div>
      </header>

      <!-- Desktop sidebar toggle -->
      <button
        onclick={toggleSidebar}
        class="hidden md:flex fixed left-[260px] top-1/2 -translate-y-1/2 z-40 w-5 h-10 items-center justify-center rounded-r-lg bg-surface-2 border border-l-0 border-[#2a2a35] text-muted hover:text-text transition-all cursor-pointer
          {sidebarOpen ? 'left-[260px]' : 'left-0'}"
        style="transition: left 0.3s ease-in-out;"
      >
        <Icon name={sidebarOpen ? 'chevronLeft' : 'chevronRight'} size={14} />
      </button>

      <main
        class="flex-1 overflow-y-auto"
        style="transition: margin-left 0.3s ease-in-out;"
      >
        <div class="p-4 md:p-6 max-w-[1600px] min-h-screen">
          {#if currentPath === '/dashboard'}
            <Dashboard />
          {:else if currentPath === '/users'}
            <Users />
          {:else if currentPath === '/vpn'}
            <VPN />
          {:else if currentPath === '/plans'}
            <Plans />
          {:else if currentPath === '/payments'}
            <Payments />
          {:else if currentPath === '/remnawave'}
            <Remnawave />
          {:else if currentPath === '/support'}
            <Support />
          {:else if currentPath === '/promos'}
            <Promos />
          {:else if currentPath === '/broadcasts'}
            <Broadcasts />
          {:else if currentPath === '/referrals'}
            <Referrals />
          {:else if currentPath === '/telegram'}
            <Telegram />
          {:else if currentPath === '/settings'}
            <Settings />
          {:else if currentPath === '/database'}
            <Database />
          {:else if currentPath === '/admins'}
            <Admins />
          {:else}
            <Dashboard />
          {/if}
        </div>
      </main>
    </div>
  </div>
{/if}
