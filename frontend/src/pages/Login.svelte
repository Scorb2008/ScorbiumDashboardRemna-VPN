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
    } catch (err) {
      error = err.message || 'Ошибка авторизации';
    } finally {
      loading = false;
    }
  }
</script>

<div class="login-page">
  <div class="login-card">
    <div class="login-logo">
      <div class="login-logo-icon">
        <Icon name="zap" size={22} class="text-black" />
      </div>
      <div>
        <h1 class="text-lg font-bold tracking-tight">Scorbium</h1>
        <p class="text-[10px] text-muted uppercase tracking-widest">VPN Dashboard</p>
      </div>
    </div>

    <form onsubmit={handleLogin} class="login-form">
      <div>
        <label for="username" class="login-label">Логин</label>
        <input
          id="username"
          type="text"
          class="login-input"
          placeholder="admin"
          bind:value={username}
          autocomplete="username"
          autofocus />
      </div>
      <div>
        <label for="password" class="login-label">Пароль</label>
        <input
          id="password"
          type="password"
          class="login-input"
          placeholder="••••••••"
          bind:value={password}
          autocomplete="current-password" />
      </div>

      {#if error}
        <div class="login-error">
          <Icon name="alertTriangle" size={16} class="shrink-0" />
          <span>{error}</span>
        </div>
      {/if}

      <button type="submit" class="btn btn-primary login-submit" disabled={loading || !username || !password}>
        {#if loading}
          <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
          <span>Вход...</span>
        {:else}
          <span>Войти</span>
        {/if}
      </button>
    </form>
  </div>
</div>

<style>
  .login-page {
    min-height: 100dvh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #16161d;
    padding: 1rem;
    box-sizing: border-box;
  }
  .login-card {
    width: 100%;
    max-width: 360px;
    animation: fadeIn 0.2s ease-out;
  }
  .login-logo {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    margin-bottom: 2rem;
  }
  .login-logo-icon {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 12px;
    background: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .login-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  .login-label {
    display: block;
    font-size: 12px;
    font-weight: 500;
    color: #8a8a9e;
    margin-bottom: 6px;
  }
  .login-input {
    width: 100%;
    background: #1c1c24;
    border: 1px solid #2a2a35;
    border-radius: 10px;
    padding: 0.75rem 0.875rem;
    font-size: 16px;
    color: #f0f0f2;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
    box-sizing: border-box;
    -webkit-appearance: none;
  }
  .login-input:focus {
    border-color: #5b8def;
    box-shadow: 0 0 0 3px rgba(91, 141, 239, 0.15);
  }
  .login-input::placeholder {
    color: #6b6b7d;
  }
  .login-error {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    border-radius: 10px;
    background: rgba(239, 68, 80, 0.1);
    border: 1px solid rgba(239, 68, 80, 0.3);
    color: #ef4444;
    font-size: 14px;
  }
  .login-submit {
    width: 100%;
    padding: 0.75rem;
    font-size: 15px;
  }
  @keyframes fadeIn {
    0% { opacity: 0; transform: translateY(6px); }
    100% { opacity: 1; transform: translateY(0); }
  }
</style>
