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
    if (body && !(body instanceof URLSearchParams) && !(body instanceof FormData)) {
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
  upload(path, formData) {
    return this.request('POST', path, { body: formData });
  }

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
  bulkAction(userIds, action, value = '') { return this.post('/users/bulk', { user_ids: userIds, action, value }); }
  giveKey(userId, planId, days = 30) { return this.post(`/users/${userId}/give-key`, { plan_id: planId, days }); }

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
  activateSubscription(id) { return this.post(`/subscriptions/${id}/activate`); }
  deactivateSubscription(id) { return this.post(`/subscriptions/${id}/deactivate`); }
  deleteSubscription(id) { return this.del(`/subscriptions/${id}`); }
  giveSubscription(userId, planId = 0, days = 30) { return this.post('/subscriptions/give', { user_id: userId, plan_id: planId, days }); }
  expireOutdated() { return this.post('/subscriptions/expire-outdated'); }

  // VPN
  getVpnKeys(params = {}) { return this.get('/vpn/keys', params); }
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
  getBroadcastHistory(params) { return this.get('/broadcasts/', params); }
  getBroadcast(id) { return this.get(`/broadcasts/${id}`); }
  createBroadcast(data) { return this.post('/broadcasts/', data); }
  sendBroadcastById(id) { return this.post(`/broadcasts/${id}/send`); }
  createAndSendBroadcast(data) { return this.post('/broadcasts/create-and-send', data); }

  // Promos
  getPromos() { return this.get('/promos/'); }
  createPromo(data) { return this.post('/promos/', data); }
  updatePromo(id, data) { return this.patch(`/promos/${id}`, data); }
  deletePromo(id) { return this.del(`/promos/${id}`); }
  togglePromo(id) { return this.post(`/promos/${id}/toggle`); }
  applyPromo(code, userId) { return this.post('/promos/apply', { code, user_id: userId }); }

  // Telegram
  getBotInfo() { return this.get('/telegram/bot-info'); }
  sendTelegramMessage(chatId, text, parseMode = 'HTML') { return this.post('/telegram/send', { chat_id: chatId, text, parse_mode: parseMode }); }
  setBotName(name, languageCode = 'ru') { return this.post('/telegram/set-name', { name, language_code: languageCode }); }
  setBotDescription(description, shortDescription = '', languageCode = 'ru') { return this.post('/telegram/set-description', { description, short_description: shortDescription, language_code: languageCode }); }
  setBotPhoto(file) { const fd = new FormData(); fd.append('file', file); return this.upload('/telegram/set-photo', fd); }
  deleteBotPhoto() { return this.post('/telegram/delete-photo'); }
  setBotCommands(commands) { return this.post('/telegram/set-commands', { commands }); }
  getBotCommands() { return this.get('/telegram/get-commands'); }
  getBotName(languageCode = 'ru') { return this.get('/telegram/get-name', { language_code: languageCode }); }
  getBotDescription(languageCode = 'ru') { return this.get('/telegram/get-description', { language_code: languageCode }); }
  refreshWebhook() { return this.post('/telegram/refresh-webhook'); }

  // VPN Squads
  getVpnSquads() { return this.get('/telegram/squads'); }
  getSelectedVpnSquads() { return this.get('/telegram/squads/selected'); }
  saveSelectedVpnSquads(squadIds) { return this.post('/telegram/squads/selected', { squad_ids: squadIds }); }

  // Referrals
  getReferralStats() { return this.get('/referrals/stats'); }
  getReferrals(params = {}) { return this.get('/referrals/', params); }
  getTopReferrers(limit = 20) { return this.get('/referrals/top', { limit }); }
  getUserReferrals(userId) { return this.get(`/referrals/user/${userId}`); }

  // Remnawave
  getRemnawaveStatus() { return this.get('/remnawave/status'); }
  getRemnawaveConnect() { return this.get('/remnawave/connect'); }
  getRemnawaveNodes() { return this.get('/remnawave/nodes'); }
  getRemnawaveStats() { return this.get('/remnawave/stats'); }
  getRemnawaveSquads() { return this.get('/remnawave/squads'); }
  remnawaveRevoke(username) { return this.post(`/remnawave/users/${username}/revoke`); }
  remnawaveEnable(username) { return this.post(`/remnawave/users/${username}/enable`); }
  remnawaveDisable(username) { return this.post(`/remnawave/users/${username}/disable`); }
  remnawaveResetTraffic(username) { return this.post(`/remnawave/users/${username}/reset-traffic`); }
  remnawaveDelete(username) { return this.request('DELETE', `/remnawave/users/${username}`); }
  remnawaveExtend(username, days) { return this.post(`/remnawave/users/${username}/extend?days=${days}`); }

  // Admins
  getAdmins() { return this.get('/admins/'); }
  getCurrentAdmin() { return this.get('/admins/me'); }
  createAdmin(data) { return this.post('/admins/', data); }
  updateAdmin(id, data) { return this.patch(`/admins/${id}`, data); }
  deleteAdmin(id) { return this.del(`/admins/${id}`); }

  // Database
  getDatabaseStats() { return this.get('/database/stats'); }
  exportDatabase(format = 'sql') { return this.request('GET', '/database/export', { params: { format }, raw: true }); }
  exportUsersCsv() { return this.request('GET', '/database/export/users', { raw: true }); }
  exportPaymentsCsv() { return this.request('GET', '/database/export/payments', { raw: true }); }
  clearDatabase() { return this.post('/database/clear', { confirm: 'DELETE EVERYTHING' }); }

  // Settings
  getSettings() { return this.get('/settings/'); }
  updateSettings(data) { return this.patch('/settings/', data); }
  getPaymentSystems() { return this.get('/settings/payment-systems'); }
  getPaymentSystemsDetail() { return this.get('/settings/payment-systems/detail'); }
  configurePaymentSystem(name, data) { return this.post(`/settings/payment-systems/${name}/configure`, data); }
  testPaymentSystem(name) { return this.post(`/settings/payment-systems/${name}/test`); }
  getAppConfig() { return this.get('/settings/config'); }

  // Audit
  getAuditLogs(params) { return this.get('/audit/', params); }
}

export const api = new ApiClient();
