/**
 * WebSocket manager for /ws/notifications.
 * Auto-reconnects, exposes reactive state via $state.
 */

let _ws = null;
let _listeners = new Set();
let _reconnectTimer = null;
let _reconnectDelay = 1000;
const MAX_DELAY = 30000;

let _connected = $state(false);
let _lastEvent = $state(null);
let _events = $state([]);

export function getWsState() {
  return {
    get connected() { return _connected; },
    get lastEvent() { return _lastEvent; },
    get events() { return _events; },
  };
}

export function onWsEvent(callback) {
  _listeners.add(callback);
  return () => _listeners.delete(callback);
}

function _getToken() {
  return localStorage.getItem('admin_token') || '';
}

function _connect() {
  if (_ws && (_ws.readyState === WebSocket.OPEN || _ws.readyState === WebSocket.CONNECTING)) {
    return;
  }

  const token = _getToken();
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = `${proto}//${location.host}/ws/notifications?token=${encodeURIComponent(token)}`;

  try {
    _ws = new WebSocket(url);
  } catch (e) {
    _scheduleReconnect();
    return;
  }

  _ws.onopen = () => {
    _connected = true;
    _reconnectDelay = 1000;
    _startPing();
  };

  _ws.onmessage = (ev) => {
    if (ev.data === 'pong') return;
    try {
      const event = JSON.parse(ev.data);
      _lastEvent = event;
      _events = [event, ..._events].slice(0, 50);
      for (const fn of _listeners) {
        try { fn(event); } catch (_) {}
      }
    } catch (_) {}
  };

  _ws.onclose = () => {
    _connected = false;
    _scheduleReconnect();
  };

  _ws.onerror = () => {
    _connected = false;
  };
}

let _pingInterval = null;
function _startPing() {
  if (_pingInterval) clearInterval(_pingInterval);
  _pingInterval = setInterval(() => {
    if (_ws && _ws.readyState === WebSocket.OPEN) {
      try { _ws.send('ping'); } catch (_) {}
    }
  }, 25000);
}

function _scheduleReconnect() {
  if (_reconnectTimer) clearTimeout(_reconnectTimer);
  _reconnectTimer = setTimeout(() => {
    _reconnectDelay = Math.min(_reconnectDelay * 1.5, MAX_DELAY);
    _connect();
  }, _reconnectDelay);
}

export function wsConnect() {
  _connect();
}

export function wsDisconnect() {
  if (_pingInterval) { clearInterval(_pingInterval); _pingInterval = null; }
  if (_reconnectTimer) { clearTimeout(_reconnectTimer); _reconnectTimer = null; }
  if (_ws) {
    _ws.onclose = null;
    _ws.close();
    _ws = null;
  }
  _connected = false;
}
