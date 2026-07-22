/**
 * Frontend auth for the multi-user Developers model (approach B).
 * Talks to our own backend (self-handled Google OAuth + passwordless email codes); our session JWT
 * is stored in localStorage. Endpoints are wired on the backend separately.
 */
import { API_CONFIG } from '../config';

const API = API_CONFIG.BASE_URL;
const TOKEN_KEY = 'sb_session';

export const getToken = () => localStorage.getItem(TOKEN_KEY) || '';
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);
export const isAuthed = () => !!getToken();

export const authFetch = (path, opts = {}) =>
  fetch(`${API}${path}`, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(opts.headers || {}),
      Authorization: `Bearer ${getToken()}`,
    },
  });

const parseError = async (r) => {
  try { return (await r.json()).detail || 'Request failed'; } catch { return 'Request failed'; }
};

export const startEmailSignIn = async (email) => {
  const r = await fetch(`${API}/api/auth/email/start`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  if (!r.ok) throw new Error(await parseError(r));
  return r.json();
};

export const verifyEmailCode = async (email, code) => {
  const r = await fetch(`${API}/api/auth/email/verify`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, code }),
  });
  if (!r.ok) throw new Error(await parseError(r));
  const body = await r.json();
  setToken(body.token);
  return body;
};

export const me = async () => {
  if (!getToken()) return null;
  try {
    const r = await authFetch('/api/auth/me');
    if (!r.ok) { if (r.status === 401) clearToken(); return null; }
    return await r.json();
  } catch { return null; }
};

/** Kicks off the backend-hosted Google OAuth flow; backend redirects back with our token. */
export const loginWithGoogle = (next = '/') => {
  window.location.href = `${API}/api/auth/google/login?next=${encodeURIComponent(next)}`;
};

export const completeOnboarding = async ({ name, picture, heard_about, use_cases }) => {
  const r = await authFetch('/api/account/onboarding', {
    method: 'POST',
    body: JSON.stringify({ name, picture, heard_about, use_cases }),
  });
  if (!r.ok) throw new Error(await parseError(r));
  return r.json();
};

export const logout = () => clearToken();
