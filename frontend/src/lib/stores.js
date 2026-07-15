import { writable, derived } from 'svelte/store';

function createRouter() {
  const initial = parseHash(window.location.hash);
  const { subscribe, set } = writable(initial);

  function parseHash(hash) {
    const raw = (hash || '#/').replace(/^#/, '');
    const parts = raw.split('/').filter(Boolean);
    return { path: '/' + (parts[0] || 'dashboard'), params: parts.slice(1) };
  }

  function init() {
    set(parseHash(window.location.hash));
    window.addEventListener('hashchange', () => set(parseHash(window.location.hash)));
  }

  function navigate(hash) {
    window.location.hash = hash;
  }

  return { subscribe, init, navigate };
}

function createToasts() {
  let id = 0;
  const { subscribe, update } = writable([]);

  function add(message, type = 'info', duration = 4000) {
    const toast = { id: ++id, message, type, duration };
    update((t) => [...t, toast]);
    if (duration > 0) {
      setTimeout(() => remove(toast.id), duration);
    }
    return toast.id;
  }

  function remove(toastId) {
    update((t) => t.filter((x) => x.id !== toastId));
  }

  return {
    subscribe,
    success: (m, d) => add(m, 'success', d),
    error: (m, d) => add(m, 'error', d || 6000),
    warning: (m, d) => add(m, 'warning', d || 5000),
    info: (m, d) => add(m, 'info', d),
    remove,
  };
}

export const router = createRouter();
export const toasts = createToasts();
export const loading = writable(false);
