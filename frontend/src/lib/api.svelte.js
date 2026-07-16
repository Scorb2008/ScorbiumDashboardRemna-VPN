const BASE = '/api/v1';

class ApiClient {
  #token = $state(localStorage.getItem('admin_token') || null);

  get isAuthenticated() {
    return !!this.#token;
  }

  get token() {
    return this.#token;
  }

  async request(method, path, { body, params, raw } = {}) {
    let url = BASE + path;
    if (params) {
      const qs = new URLSearchParams();
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null && v !== '') qs.set(k, v);
      }
      const s = qs.toString();
      if (s) url += '?' + s;
    }

    const headers = {};
    if (body && !(body instanceof URLSearchParams)) {
      headers['Content-Type'] = 'application/json';
    }
    if (this.#token) headers['Authorization'] = `Bearer ${this.#token}`;

    const res = await fetch(url, {
      method,
      headers,
      body: body instanceof URLSearchParams ? body : body ? JSON.stringify(body) : undefined,
    });

    if (res.status === 401) {
      this.#token = null;
      localStorage.removeItem('admin_token');
      window.location.hash = '#/login';
      throw new Error('Unauthorized');
    }

    if (res.status === 204) return null;

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    if (raw) return res;
    return res.json();
  }

  get(path, params) { return this.request('GET', path, { params }); }
  post(path, body) { return this.request('POST', path, { body }); }
  patch(path, body) { return this.request('PATCH', path, { body }); }
  del(path) { return this.request('DELETE', path); }

  async login(username, password) {
    const form = new URLSearchParams();
    form.set('username', username);
    form.set('password', password);
    const data = await this.request('POST', '/auth/login', { body: form });
    this.#token = data.access_token;
    localStorage.setItem('admin_token', data.access_token);
    return data;
  }

  logout() {
    this.#token = null;
    localStorage.removeItem('admin_token');
    window.location.hash = '#/login';
  }

  // Dashboard
  getDashboard() { return this.get('/dashboard/stats'); }

  // Users
  getUsers(params) { return this.get('/users/', params); }
  getUser(id) { return this.get(`/users/${id}`); }
  updateUser(id, data) { return this.patch(`/users/${id}`, data); }
  banUser(id) { return this.post(`/users/${id}/ban`); }
  unbanUser(id) { return this.post(`/users/${id}/unban`); }
  sendMessage(userId, text) { return this.post(`/users/${userId}/message`, { text }); }
  getUserKeys(userId) { return this.get(`/users/${userId}/keys`); }
  getUserPayments(userId) { return this.get(`/users/${userId}/payments`); }

  // Plans
  getPlans(params) { return this.get('/plans/', params); }
  getPlan(id) { return this.get(`/plans/${id}`); }
  createPlan(data) { return this.post('/plans/', data); }
  updatePlan(id, data) { return this.patch(`/plans/${id}`, data); }
  togglePlan(id) { return this.post(`/plans/${id}/toggle`); }
  deletePlan(id) { return this.del(`/plans/${id}`); }

  // Subscriptions / VPN keys
  getSubscriptions(params) { return this.get('/subscriptions/', params); }
  getSubscription(id) { return this.get(`/subscriptions/${id}`); }
  cancelSubscription(id) { return this.post(`/subscriptions/${id}/cancel`); }
  expireOutdated() { return this.post('/subscriptions/expire-outdated'); }

  // VPN
  getVpnKeys(userId) { return this.get(`/vpn/${userId}/keys`); }
  revokeKey(id) { return this.del(`/vpn/keys/${id}`); }
  deleteKey(id) { return this.del(`/vpn/keys/${id}/delete`); }
  syncKeys() { return this.post('/vpn/sync'); }

  // Payments
  getPayments(params) { return this.get('/payments/', params); }
  getPayment(id) { return this.get(`/payments/${id}`); }
  createPayment(data) { return this.post('/payments/', data); }
  refundPayment(id) { return this.post(`/payments/${id}/refund`); }

  // Support
  getTickets(params) { return this.get('/support/', params); }
  getTicket(id) { return this.get(`/support/${id}`); }
  createTicket(data) { return this.post('/support/', data); }
  replyTicket(id, text, notifyUser = true) { return this.post(`/support/${id}/reply`, { text, notify_user: notifyUser }); }
  updateTicketStatus(id, status) { return this.patch(`/support/${id}/status`, { status }); }
  updateTicketPriority(id, priority) { return this.patch(`/support/${id}/priority`, { priority }); }

  // Broadcasts
  getBroadcasts(params) { return this.get('/broadcasts/', params); }
  getBroadcast(id) { return this.get(`/broadcasts/${id}`); }
  createBroadcast(data) { return this.post('/broadcasts/', data); }
  sendBroadcast(id) { return this.post(`/broadcasts/${id}/send`); }

  // Promos
  getPromos() { return this.get('/promos/'); }
  createPromo(data) { return this.post('/promos/', data); }
  deletePromo(id) { return this.del(`/promos/${id}`); }
  togglePromo(id) { return this.post(`/promos/${id}/toggle`); }
  applyPromo(code, userId) { return this.post('/promos/apply', { code, user_id: userId }); }

  // Telegram
  getBotInfo() { return this.get('/telegram/bot-info'); }
  sendTelegramMessage(chatId, text, parseMode = 'HTML') { return this.post('/telegram/send', { chat_id: chatId, text, parse_mode: parseMode }); }

  // Referrals
  getReferralStats() { return this.get('/referrals/stats'); }
  getTopReferrers(limit) { return this.get('/referrals/top', { limit }); }
  getUserReferrals(userId) { return this.get(`/referrals/user/${userId}`); }

  // Remnawave
  getRemnawaveStatus() { return this.get('/remnawave/status'); }
  getRemnawaveNodes() { return this.get('/remnawave/nodes'); }
  getRemnawaveUsers() { return this.get('/remnawave/users'); }
  remnawaveProxy(method, path, body) { return this.request(method, `/remnawave/proxy/${path}`, { body }); }

  // Admins
  getAdmins() { return this.get('/admins/'); }
  getCurrentAdmin() { return this.get('/admins/me'); }
  createAdmin(data) { return this.post('/admins/', data); }
  updateAdmin(id, data) { return this.patch(`/admins/${id}`, data); }
  deleteAdmin(id) { return this.del(`/admins/${id}`); }

  // Database
  getDatabaseStats() { return this.get('/database/stats'); }
  exportDatabase(format = 'sql') { return this.get('/database/export', { format }); }
  clearDatabase() { return this.post('/database/clear'); }

  // Settings
  getSettings() { return this.get('/settings/'); }
  updateSettings(data) { return this.patch('/settings/', data); }
  getPaymentSystems() { return this.get('/settings/payment-systems'); }
  getAppConfig() { return this.get('/settings/config'); }
}

export const api = new ApiClient();
