<script>
  import { api } from '../lib/api.svelte.js';
  import { toasts } from '../lib/stores.js';
  import Icon from '../components/Icon.svelte';

  let username = $state('');
  let password = $state('');
  let loading = $state(false);
  let error = $state('');

  let twoFARequired = $state(false);
  let tempToken = $state('');
  let totpCode = $state('');
  let twoFALoading = $state(false);

  async function handleLogin(e) {
    e.preventDefault();
    if (!username || !password) return;
    loading = true;
    error = '';
    try {
      const result = await api.login(username, password);
      if (result?.requires_2fa) {
        tempToken = result.temp_token;
        twoFARequired = true;
        totpCode = '';
        return;
      }
      window.location.hash = '#/dashboard';
    } catch (err) {
      error = err.message || 'Ошибка авторизации';
    } finally {
      loading = false;
    }
  }

  async function handle2FA(e) {
    e.preventDefault();
    if (!totpCode || totpCode.length < 6) return;
    twoFALoading = true;
    error = '';
    try {
      await api.login2fa(tempToken, totpCode);
      window.location.hash = '#/dashboard';
    } catch (err) {
      error = err.message || 'Неверный код';
    } finally {
      twoFALoading = false;
    }
  }

  function backToLogin() {
    twoFARequired = false;
    tempToken = '';
    totpCode = '';
    error = '';
  }
</script>

<div class="login-page">
  <div class="login-bg-glow"></div>
  <div class="login-grid-overlay"></div>

  <div class="login-card">
    <div class="login-logo">
      <div class="login-logo-icon">
        <Icon name="zap" size={24} class="text-black" />
      </div>
      <div class="login-logo-text">
        <h1 class="text-[22px] font-bold tracking-tight">Scorbium</h1>
        <p class="text-[10px] text-muted uppercase tracking-[0.2em]">VPN Dashboard</p>
      </div>
    </div>

    {#if twoFARequired}
      <form onsubmit={handle2FA} class="login-form">
        <div class="two-fa-header">
          <Icon name="shield" size={32} class="text-accent" />
          <p class="text-[13px] text-muted mt-2">Введите код из приложения аутентификатора</p>
        </div>
        <div class="login-field">
          <label for="totp" class="login-label">Код 2FA</label>
          <input
            id="totp"
            type="text"
            inputmode="numeric"
            maxlength="6"
            class="login-input text-center text-[24px] tracking-[0.5em] font-mono"
            placeholder="000000"
            bind:value={totpCode}
            autofocus
            required />
        </div>

        {#if error}
          <div class="login-error">
            <Icon name="alertTriangle" size={14} class="shrink-0" />
            <span>{error}</span>
          </div>
        {/if}

        <button type="submit" class="login-submit" disabled={twoFALoading || totpCode.length < 6}>
          {#if twoFALoading}
            <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            <span>Проверка...</span>
          {:else}
            <span>Подтвердить</span>
          {/if}
        </button>

        <button type="button" class="login-back-btn" onclick={backToLogin}>
          ← Назад к логину
        </button>
      </form>
    {:else}
      <form onsubmit={handleLogin} class="login-form">
        <div class="login-field">
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
        <div class="login-field">
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
            <Icon name="alertTriangle" size={14} class="shrink-0" />
            <span>{error}</span>
          </div>
        {/if}

        <button type="submit" class="login-submit" disabled={loading || !username || !password}>
          {#if loading}
            <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            <span>Вход...</span>
          {:else}
            <span>Войти</span>
          {/if}
        </button>
      </form>
    {/if}
  </div>
</div>

<style>
  .login-page {
    min-height: 100dvh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #0d0d12;
    padding: 1rem;
    box-sizing: border-box;
    position: relative;
    overflow: hidden;
  }

  .login-bg-glow {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 600px;
    height: 600px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(91, 141, 239, 0.08) 0%, rgba(91, 141, 239, 0.02) 40%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }

  .login-grid-overlay {
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
    background-size: 48px 48px;
    pointer-events: none;
    z-index: 0;
    mask-image: radial-gradient(circle at center, rgba(0,0,0,0.4) 0%, transparent 65%);
    -webkit-mask-image: radial-gradient(circle at center, rgba(0,0,0,0.4) 0%, transparent 65%);
  }

  .login-card {
    width: 100%;
    max-width: 380px;
    position: relative;
    z-index: 1;
    background: #13131b;
    border: 1px solid #222230;
    border-radius: 16px;
    padding: 2.5rem 2rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255,255,255,0.03) inset;
    animation: cardIn 0.4s cubic-bezier(0.22, 1, 0.36, 1);
  }

  .login-logo {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.875rem;
    margin-bottom: 2.25rem;
  }

  .login-logo-icon {
    width: 3rem;
    height: 3rem;
    border-radius: 14px;
    background: linear-gradient(135deg, #5b8def, #7aa3ff);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 16px rgba(91, 141, 239, 0.3);
    flex-shrink: 0;
  }

  .login-logo-text {
    text-align: left;
  }

  .login-form {
    display: flex;
    flex-direction: column;
    gap: 1.125rem;
  }

  .login-field {
    display: flex;
    flex-direction: column;
  }

  .login-label {
    display: block;
    font-size: 11px;
    font-weight: 600;
    color: #6b6b7d;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .login-input {
    width: 100%;
    background: #191920;
    border: 1px solid #28283a;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    font-size: 15px;
    color: #f0f0f2;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
    box-sizing: border-box;
    -webkit-appearance: none;
  }

  .login-input:focus {
    border-color: #5b8def;
    box-shadow: 0 0 0 3px rgba(91, 141, 239, 0.12), 0 0 20px rgba(91, 141, 239, 0.08);
  }

  .login-input::placeholder {
    color: #4a4a5a;
  }

  .login-error {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 0.875rem;
    border-radius: 10px;
    background: rgba(239, 68, 80, 0.08);
    border: 1px solid rgba(239, 68, 80, 0.2);
    color: #ef4444;
    font-size: 13px;
  }

  .login-submit {
    width: 100%;
    padding: 0.75rem;
    font-size: 14px;
    font-weight: 600;
    border-radius: 10px;
    border: none;
    background: linear-gradient(135deg, #5b8def, #4a7de0);
    color: #fff;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    transition: all 0.2s;
    margin-top: 0.25rem;
    box-shadow: 0 2px 12px rgba(91, 141, 239, 0.25);
  }

  .login-submit:hover:not(:disabled) {
    background: linear-gradient(135deg, #6d9bf5, #5b8def);
    box-shadow: 0 4px 24px rgba(91, 141, 239, 0.35);
    transform: translateY(-1px);
  }

  .login-submit:active:not(:disabled) {
    transform: translateY(0);
  }

  .login-submit:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    transform: none;
  }

  .login-back-btn {
    background: none;
    border: none;
    color: #6b6b7d;
    font-size: 13px;
    cursor: pointer;
    padding: 0.25rem;
    transition: color 0.15s;
    align-self: center;
  }
  .login-back-btn:hover {
    color: #b0b0c0;
  }

  .two-fa-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0.5rem 0;
  }

  @keyframes cardIn {
    0% { opacity: 0; transform: translateY(12px) scale(0.98); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
  }
</style>
