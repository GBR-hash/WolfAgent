const API_BASE = 'http://localhost:8000';

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('wolf_token');
  return token ? { 'Authorization': 'Bearer ' + token } : {};
}

export async function register(username: string, password: string) {
  const res = await fetch(API_BASE + '/auth/register', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Register failed'); }
  return res.json() as Promise<{ token: string; user_id: number; username: string }>;
}

export async function login(username: string, password: string) {
  const res = await fetch(API_BASE + '/auth/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Login failed'); }
  return res.json() as Promise<{ token: string; user_id: number; username: string }>;
}

export async function newGame(role: string = 'random', playStyle: string = 'balanced') {
  const token = localStorage.getItem('wolf_token') || undefined;
  const res = await fetch(API_BASE + '/game/new', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role, play_style: playStyle, token }),
  });
  if (!res.ok) throw new Error('Failed to create game');
  return res.json() as Promise<{ game_id: string; human_role: string; message: string }>;
}

export async function submitAction(gameId: string, action: string) {
  const res = await fetch(API_BASE + '/game/' + gameId + '/action', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  });
  if (!res.ok) throw new Error('Action failed');
  return res.json();
}

export function createSSEConnection(gameId: string, onMessage: (state: unknown) => void, onError: (err: Event) => void): EventSource {
  const es = new EventSource(API_BASE + '/game/' + gameId + '/stream');
  es.addEventListener('state', (e: MessageEvent) => {
    try { onMessage(JSON.parse(e.data)); } catch (err) { console.error('SSE parse error:', err); }
  });
  es.addEventListener('heartbeat', () => {});
  es.onerror = onError;
  return es;
}

export async function fetchRecords() {
  const res = await fetch(API_BASE + '/records', { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error('Failed to fetch records');
  return res.json();
}

export async function fetchRecordDetail(gameId: string) {
  const res = await fetch(API_BASE + '/records/' + gameId, { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error('Failed to fetch record');
  return res.json();
}