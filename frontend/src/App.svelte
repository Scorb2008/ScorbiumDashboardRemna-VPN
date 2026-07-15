<script>
  import { onMount } from 'svelte';
  import { router } from './lib/stores.js';
  import { api } from './lib/api.js';
  import Sidebar from './components/Sidebar.svelte';
  import Toasts from './components/Toasts.svelte';

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

  let currentPath = $state('/dashboard');
  let authenticated = $state(api.isAuthenticated);

  onMount(() => {
    router.init();
    const unsub = router.subscribe((r) => {
      currentPath = r.path;
      authenticated = api.isAuthenticated;
    });
    return unsub;
  });
</script>

<Toasts />

{#if !authenticated || currentPath === '/login'}
  <Login />
{:else}
  <div class="flex h-screen overflow-hidden">
    <Sidebar bind:currentPath />
    <main class="flex-1 overflow-y-auto ml-[var(--sidebar-width)]">
      <div class="p-6 max-w-[1600px]">
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
        {:else}
          <Dashboard />
        {/if}
      </div>
    </main>
  </div>
{/if}
