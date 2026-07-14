const BASE = '/api/v1';

class ApiClient {
  constructor() {
    this._token = localStorage.getItem('admin_token') || '';
  }

  get token() {
    return this._token;
  }

  set token(val) {
    this._token = val;
    if (val) {
      localStorage.setItem('admin_token', val);
    } else {
      localStorage.removeItem('admin_token');
    }
  }

  get isAuthenticated() {
    return !!this._token;
  }

  async request(path, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    if (this._token) {
      headers['Authorization'] = `Bearer ${this._token}`;
    }
    const res = await fetch(`${BASE}${path}`, { ...options, headers });
    if (res.status === 401) {
      this.token = '';
      window.location.hash = '#/login';
      throw new Error('Unauthorized');
    }
    if (res.status === 204) return null;
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  get(path, params) {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return this.request(`${path}${qs}`);
  }
  post(path, body) {
    return this.request(path, { method: 'POST', body: JSON.stringify(body) });
  }
  patch(path, body) {
    return this.request(path, { method: 'PATCH', body: JSON.stringify(body) });
  }
  del(path) {
    return this.request(path, { method: 'DELETE' });
  }

  // ── Auth ──────────────────────────────────────────────────────────────
  async login(username, password) {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);
    const res = await fetch(`${BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || 'Login failed');
    }
    const data = await res.json();
    this.token = data.access_token;
    return data;
  }

  logout() {
    this.token = '';
  }

  // ── Dashboard ─────────────────────────────────────────────────────────
  getDashboard() { return this.get('/dashboard/stats'); }

  // ── Users ─────────────────────────────────────────────────────────────
  getUsers(params) { return this.get('/users/', params); }
  getUser(id) { return this.get(`/users/${id}`); }
  updateUser(id, data) { return this.patch(`/users/${id}`, data); }
  banUser(id) { return this.post(`/users/${id}/ban`); }
  unbanUser(id) { return this.post(`/users/${id}/unban`); }
  sendUserMessage(id, text) { return this.post(`/users/${id}/message`, { text }); }

  // ── Plans ─────────────────────────────────────────────────────────────
  getPlans() { return this.get('/plans/'); }
  createPlan(data) { return this.post('/plans/', data); }
  updatePlan(id, data) { return this.patch(`/plans/${id}`, data); }
  togglePlan(id) { return this.post(`/plans/${id}/toggle`); }
  deletePlan(id) { return this.del(`/plans/${id}`); }

  // ── VPN / Subscriptions ──────────────────────────────────────────────
  getSubscriptions(params) { return this.get('/subscriptions/', params); }
  getSubscription(id) { return this.get(`/subscriptions/${id}`); }
  cancelSubscription(id) { return this.post(`/subscriptions/${id}/cancel`); }
  expireOutdated() { return this.post('/subscriptions/expire-outdated'); }
  getUserKeys(userId) { return this.get(`/vpn/${userId}/keys`); }
  revokeKey(id) { return this.del(`/vpn/keys/${id}`); }
  deleteKey(id) { return this.del(`/vpn/keys/${id}/delete`); }
  syncKeys() { return this.post('/vpn/sync'); }

  // ── Payments ──────────────────────────────────────────────────────────
  getPayments(params) { return this.get('/payments/', params); }
  getPayment(id) { return this.get(`/payments/${id}`); }
  refundPayment(id) { return this.post(`/payments/${id}/refund`); }

  // ── Promos ────────────────────────────────────────────────────────────
  getPromos() { return this.get('/promos/'); }
  createPromo(data) { return this.post('/promos/', data); }
  deletePromo(id) { return this.del(`/promos/${id}`); }
  togglePromo(id) { return this.post(`/promos/${id}/toggle`); }

  // ── Support ───────────────────────────────────────────────────────────
  getTickets(params) { return this.get('/support/', params); }
  getTicket(id) { return this.get(`/support/${id}`); }
  replyTicket(id, text) { return this.post(`/support/${id}/reply`, { text }); }
  updateTicketStatus(id, status) { return this.patch(`/support/${id}/status`, { status }); }

  // ── Broadcasts ────────────────────────────────────────────────────────
  getBroadcasts(params) { return this.get('/broadcasts/', params); }
  createBroadcast(data) { return this.post('/broadcasts/', data); }
  sendBroadcast(id) { return this.post(`/broadcasts/${id}/send`); }

  // ── Referrals ─────────────────────────────────────────────────────────
  getReferralStats() { return this.get('/referrals/stats'); }
  getTopReferrers(limit) { return this.get('/referrals/top', { limit }); }

  // ── Telegram ──────────────────────────────────────────────────────────
  getBotInfo() { return this.get('/telegram/bot-info'); }
}

export const api = new ApiClient();
