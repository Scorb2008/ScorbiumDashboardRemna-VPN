<script>
  import { api } from '../lib/api.js';
  import { toasts, router } from '../lib/stores.js';

  let username = $state('');
  let password = $state('');
  let loading = $state(false);

  async function handleLogin() {
    if (!username || !password) {
      toasts.warning('Введите логин и пароль');
      return;
    }
    loading = true;
    try {
      await api.login(username, password);
      toasts.success('Добро пожаловать!');
      router.navigate('/dashboard');
    } catch (e) {
      toasts.error('Неверный логин или пароль');
    } finally {
      loading = false;
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center bg-base-300">
  <div class="bg-base-200 rounded-2xl shadow-2xl border border-base-300 p-8 w-full max-w-sm fade-in">
    <div class="text-center mb-8">
      <span class="text-5xl">⚡</span>
      <h1 class="text-2xl font-bold mt-3">Scorbium</h1>
      <p class="text-base-content/50 text-sm mt-1">VPN Dashboard</p>
    </div>

    <form onsubmit={(e) => { e.preventDefault(); handleLogin(); }}>
      <div class="form-control mb-4">
        <label class="label">
          <span class="label-text">Логин</span>
        </label>
        <input
          type="text"
          bind:value={username}
          placeholder="admin"
          class="input input-bordered w-full"
          autofocus />
      </div>

      <div class="form-control mb-6">
        <label class="label">
          <span class="label-text">Пароль</span>
        </label>
        <input
          type="password"
          bind:value={password}
          placeholder="••••••••"
          class="input input-bordered w-full"
          onkeydown={(e) => e.key === 'Enter' && handleLogin()} />
      </div>

      <button
        type="submit"
        class="btn btn-primary w-full"
        disabled={loading}>
        {#if loading}
          <span class="loading loading-spinner loading-sm"></span>
        {:else}
          Войти
        {/if}
      </button>
    </form>
  </div>
</div>
