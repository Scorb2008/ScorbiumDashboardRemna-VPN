import { writable, derived } from 'svelte/store';

// ── Router ──────────────────────────────────────────────────────────────
function createRouter() {
  const { subscribe, set } = writable({ path: '', params: {} });

  function navigate(hash) {
    const clean = hash.replace(/^#/, '') || '/dashboard';
    const parts = clean.split('/').filter(Boolean);
    set({ path: '/' + parts.join('/'), params: {} });
  }

  function init() {
    navigate(window.location.hash);
    window.addEventListener('hashchange', () => navigate(window.location.hash));
  }

  return { subscribe, navigate: (p) => { window.location.hash = '#' + p; }, init };
}

export const router = createRouter();

// ── Toast notifications ─────────────────────────────────────────────────
function createToasts() {
  const { subscribe, update } = writable([]);
  let id = 0;

  function add(message, type = 'info', duration = 4000) {
    const toast = { id: ++id, message, type };
    update((t) => [...t, toast]);
    if (duration > 0) {
      setTimeout(() => remove(toast.id), duration);
    }
  }

  function remove(toastId) {
    update((t) => t.filter((x) => x.id !== toastId));
  }

  return {
    subscribe,
    success: (msg) => add(msg, 'success'),
    error: (msg) => add(msg, 'error', 6000),
    warning: (msg) => add(msg, 'warning', 5000),
    info: (msg) => add(msg, 'info'),
    remove,
  };
}

export const toasts = createToasts();

// ── Loading state ───────────────────────────────────────────────────────
export const loading = writable(false);

// ── Sidebar ─────────────────────────────────────────────────────────────
export const sidebarOpen = writable(true);
