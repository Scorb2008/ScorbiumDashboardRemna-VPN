<script>
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import Icon from '../components/Icon.svelte';

  let username = $state('');
  let password = $state('');
  let loading = $state(false);
  let error = $state('');

  async function handleLogin(e) {
    e.preventDefault();
    if (!username || !password) return;
    loading = true;
    error = '';
    try {
      await api.login(username, password);
      window.location.hash = '#/dashboard';
      window.location.reload();
    } catch (err) {
      error = err.message || 'Ошибка авторизации';
    } finally {
      loading = false;
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center bg-surface-1 p-4">
  <div class="w-full max-w-[360px] animate-fade-in">
    <!-- Logo -->
    <div class="flex items-center justify-center gap-3 mb-8">
      <div class="w-10 h-10 rounded-[12px] bg-white flex items-center justify-center">
        <Icon name="zap" size={22} class="text-black" />
      </div>
      <div>
        <h1 class="text-lg font-bold tracking-tight">Scorbium</h1>
        <p class="text-[10px] text-muted uppercase tracking-widest">VPN Dashboard</p>
      </div>
    </div>

    <!-- Form -->
    <form onsubmit={handleLogin} class="space-y-4">
      <div>
        <label for="username" class="block text-[12px] font-medium text-muted mb-1.5">Логин</label>
        <input
          id="username"
          type="text"
          class="input"
          placeholder="admin"
          bind:value={username}
          autocomplete="username"
          autofocus />
      </div>
      <div>
        <label for="password" class="block text-[12px] font-medium text-muted mb-1.5">Пароль</label>
        <input
          id="password"
          type="password"
          class="input"
          placeholder="••••••••"
          bind:value={password}
          autocomplete="current-password" />
      </div>

      {#if error}
        <div class="flex items-center gap-2 px-3 py-2 rounded-[10px] bg-[#ef4444]/10 border border-[#ef4444]/30 text-[#ef4444] text-sm">
          <Icon name="alertTriangle" size={16} class="shrink-0" />
          <span>{error}</span>
        </div>
      {/if}

      <button type="submit" class="btn btn-primary w-full py-2.5" disabled={loading || !username || !password}>
        {#if loading}
          <div class="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin"></div>
          <span>Вход...</span>
        {:else}
          <span>Войти</span>
        {/if}
      </button>
    </form>
  </div>
</div>
