<script>
  import { onMount } from 'svelte';
  import { api } from './lib/api.js';
  import { router } from './lib/stores.js';
  import Sidebar from './components/Sidebar.svelte';
  import Toasts from './components/Toasts.svelte';
  import Spinner from './components/Spinner.svelte';

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

  let currentPath = $state('/dashboard');
  let authenticated = $state(api.isAuthenticated);

  onMount(() => {
    router.init();
  });

  $effect(() => {
    const unsub = router.subscribe((r) => {
      currentPath = r.path;
      authenticated = api.isAuthenticated;
    });
    return unsub;
  });

  const routes = {
    '/login': Login,
    '/dashboard': Dashboard,
    '/users': Users,
    '/vpn': VPN,
    '/plans': Plans,
    '/payments': Payments,
    '/remnawave': Remnawave,
    '/support': Support,
    '/promos': Promos,
    '/broadcasts': Broadcasts,
  };

  let routeComponent = $derived(
    routes[currentPath] || (authenticated ? Dashboard : Login)
  );
</script>

<Toasts />

{#if currentPath === '/login' || !authenticated}
  <Login />
{:else}
  <div class="flex h-screen overflow-hidden">
    <Sidebar {currentPath} />
    <main class="flex-1 overflow-y-auto p-6 bg-base-300">
      {#key currentPath}
        <svelte:component this={routeComponent} />
      {/key}
    </main>
  </div>
{/if}
