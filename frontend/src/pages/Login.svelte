<script>
  import { router, toasts } from '../lib/stores.js';
  import { api } from '../lib/api.svelte.js';
  import Spinner from '../components/Spinner.svelte';

  let username = $state('');
  let password = $state('');
  let loading = $state(false);
  let error = $state('');

  async function handleLogin() {
    if (!username.trim() || !password.trim()) {
      error = 'Заполните все поля';
      return;
    }
    loading = true;
    error = '';
    try {
      await api.login(username, password);
      toasts.success('Добро пожаловать!');
      router.navigate('#/dashboard');
    } catch (e) {
      error = e.message || 'Ошибка авторизации';
      toasts.error(error);
    } finally {
      loading = false;
    }
  }

  function handleKeydown(e) {
    if (e.key === 'Enter') handleLogin();
  }
</script>

<Spinner {loading} />

<div class="min-h-screen flex items-center justify-center bg-base-100 p-4">
  <div class="absolute inset-0 overflow-hidden pointer-events-none">
    <div class="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-primary/5 blur-3xl"></div>
    <div class="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-secondary/5 blur-3xl"></div>
  </div>

  <div class="w-full max-w-md animate-slide-up relative">
    <div class="text-center mb-8">
      <div class="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center mx-auto mb-4 shadow-xl shadow-primary/25">
        <svg class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      </div>
      <h1 class="text-3xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">Scorbium</h1>
      <p class="text-sm text-base-content/40 mt-1">VPN Dashboard</p>
    </div>

    <div class="glass-strong rounded-2xl p-8 space-y-5">
      <div class="space-y-1">
        <h2 class="text-xl font-semibold text-center">Вход в панель</h2>
        <p class="text-sm text-base-content/40 text-center">Введите данные администратора</p>
      </div>

      {#if error}
        <div class="alert alert-error text-sm animate-fade-in">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      {/if}

      <div class="form-control">
        <label class="label"><span class="label-text text-xs font-medium uppercase tracking-wider text-base-content/50">Логин</span></label>
        <input
          type="text"
          bind:value={username}
          onkeydown={handleKeydown}
          placeholder="admin"
          class="input input-bordered input-glass w-full"
          autofocus />
      </div>

      <div class="form-control">
        <label class="label"><span class="label-text text-xs font-medium uppercase tracking-wider text-base-content/50">Пароль</span></label>
        <input
          type="password"
          bind:value={password}
          onkeydown={handleKeydown}
          placeholder="••••••••"
          class="input input-bordered input-glass w-full" />
      </div>

      <button
        onclick={handleLogin}
        disabled={loading}
        class="btn btn-primary w-full btn-glow gradient-primary border-0 text-white font-medium">
        {#if loading}
          <span class="loading loading-spinner loading-sm"></span>
        {:else}
          Войти
        {/if}
      </button>
    </div>
  </div>
</div>
