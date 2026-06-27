import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_CONFIG } from '../config';

const API = API_CONFIG.BASE_URL;

const MODES = [
  ['search', 'Web search results (raw links + snippets).'],
  ['scrape', 'Full text extracted from the result pages.'],
  ['analyze', 'Synthesized summary + key points across sources (always uses the LLM).'],
  ['news', 'Recent news articles for the query.'],
];

const fmtDate = (t) => (t ? new Date(t * 1000).toLocaleDateString() : '—');

const Section = ({ title, subtitle, children }) => (
  <section className="mb-8">
    <h2 className="text-lg font-semibold text-black dark:text-white">{title}</h2>
    {subtitle && <p className="text-sm text-gray-500 dark:text-neutral-400 mt-0.5 mb-4">{subtitle}</p>}
    {!subtitle && <div className="mb-4" />}
    {children}
  </section>
);

const Code = ({ children }) => (
  <pre className="text-xs bg-neutral-100 dark:bg-neutral-950 border border-gray-200 dark:border-neutral-800 rounded-lg p-3 overflow-x-auto text-gray-800 dark:text-neutral-200 whitespace-pre-wrap">{children}</pre>
);

const UsageBar = ({ used, quota }) => {
  if (!quota) return <span className="text-xs text-gray-500 dark:text-neutral-400">{used} used · unlimited</span>;
  const pct = Math.min(100, Math.round((used / quota) * 100));
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-gray-500 dark:text-neutral-400 mb-1">
        <span>{used} / {quota}</span><span>{pct}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-gray-200 dark:bg-neutral-800 overflow-hidden">
        <div className={`h-full ${pct >= 100 ? 'bg-red-500' : 'bg-blue-500'}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
};

const Developers = () => {
  const navigate = useNavigate();
  const [token, setToken] = useState(() => localStorage.getItem('admin_token') || '');
  const [creds, setCreds] = useState({ username: '', password: '' });
  const [keys, setKeys] = useState([]);
  const [newKey, setNewKey] = useState(null);   // plaintext shown once
  const [name, setName] = useState('');
  const [quota, setQuota] = useState('');
  const [copied, setCopied] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const authHeaders = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const loadKeys = useCallback(async (tok) => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/keys`, { headers: { Authorization: `Bearer ${tok}` } });
      if (r.status === 401) { setToken(''); localStorage.removeItem('admin_token'); return; }
      if (!r.ok) throw new Error();
      setKeys((await r.json()).keys || []);
      setError('');
    } catch {
      setError('Could not reach the API. Start the backend, then reload.');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { if (token) loadKeys(token); }, [token, loadKeys]);

  const login = async (e) => {
    e.preventDefault(); setError('');
    try {
      const r = await fetch(`${API}/api/admin/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(creds),
      });
      if (!r.ok) { setError(r.status === 401 ? 'Invalid credentials' : 'Login unavailable'); return; }
      const { token: tok } = await r.json();
      localStorage.setItem('admin_token', tok); setToken(tok);
    } catch { setError('Could not reach the server'); }
  };

  const createKey = async () => {
    try {
      const body = { name: name || 'key', quota: quota ? Number(quota) : null };
      const r = await fetch(`${API}/api/keys`, { method: 'POST', headers: authHeaders, body: JSON.stringify(body) });
      if (!r.ok) throw new Error();
      const data = await r.json();
      setNewKey(data.key); setName(''); setQuota('');
      loadKeys(token);
    } catch { setError('Could not create key'); }
  };

  const rotateKey = async (id) => {
    if (!window.confirm('Rotate this key? The old secret stops working immediately.')) return;
    const r = await fetch(`${API}/api/keys/${id}/rotate`, { method: 'POST', headers: authHeaders });
    if (r.ok) { setNewKey((await r.json()).key); loadKeys(token); }
  };

  const revokeKey = async (id) => {
    if (!window.confirm('Revoke this key? It can no longer be used (do this if it leaked).')) return;
    const r = await fetch(`${API}/api/keys/${id}`, { method: 'DELETE', headers: authHeaders });
    if (r.ok) loadKeys(token);
  };

  const copy = async (text, what) => {
    try { await navigator.clipboard.writeText(text); setCopied(what); setTimeout(() => setCopied(''), 1500); } catch {}
  };

  return (
    <div className="min-h-screen bg-neutral-100 dark:bg-black">
      <header className="border-b border-gray-200 dark:border-neutral-800 bg-white/80 dark:bg-neutral-900/80 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <button onClick={() => navigate('/')} className="text-sm text-gray-600 dark:text-neutral-300 hover:text-black dark:hover:text-white">← SearchGPT Agent</button>
          <h1 className="text-base font-medium text-black dark:text-white">Developers</h1>
          {token
            ? <button onClick={() => { localStorage.removeItem('admin_token'); setToken(''); }} className="text-xs text-gray-500 dark:text-neutral-400">Sign out</button>
            : <span className="w-20" />}
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <p className="text-sm text-gray-600 dark:text-neutral-400 mb-8">
          One endpoint, four modes. Use your key from any app, or right here in the playground.
          Heavy usage? <button onClick={() => { document.getElementById('selfhost')?.scrollIntoView({ behavior: 'smooth' }); }} className="text-blue-600 dark:text-blue-400 underline">self-host</button> with your own keys — no per-call meter.
        </p>

        {/* ---- API KEYS ---- */}
        <Section title="Your API keys" subtitle="Create, rotate, and revoke keys. Each key has its own usage and quota.">
          {!token ? (
            <form onSubmit={login} className="rounded-xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-5 max-w-sm">
              <p className="text-sm text-gray-600 dark:text-neutral-300 mb-3">Sign in (owner) to manage keys.</p>
              <input className="w-full mb-2 px-3 py-2 rounded-lg border border-gray-200 dark:border-neutral-700 bg-transparent text-sm text-black dark:text-white outline-none" placeholder="Username" value={creds.username} onChange={(e) => setCreds({ ...creds, username: e.target.value })} />
              <input type="password" className="w-full mb-3 px-3 py-2 rounded-lg border border-gray-200 dark:border-neutral-700 bg-transparent text-sm text-black dark:text-white outline-none" placeholder="Password" value={creds.password} onChange={(e) => setCreds({ ...creds, password: e.target.value })} />
              {error && <p className="text-xs text-red-500 mb-2">{error}</p>}
              <button className="w-full py-2 rounded-lg bg-black dark:bg-white text-white dark:text-black text-sm font-medium">Sign in</button>
            </form>
          ) : (
            <div className="space-y-4">
              {newKey && (
                <div className="rounded-xl border border-emerald-300 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-500/10 p-4">
                  <p className="text-xs text-emerald-700 dark:text-emerald-300 mb-2">Copy this key now — you won't see it again.</p>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 text-sm px-3 py-2 rounded-lg bg-white dark:bg-neutral-950 border border-gray-200 dark:border-neutral-800 text-black dark:text-white truncate">{newKey}</code>
                    <button onClick={() => copy(newKey, 'new')} className="px-3 py-2 rounded-lg border border-gray-200 dark:border-neutral-700 text-sm">{copied === 'new' ? 'Copied' : 'Copy'}</button>
                    <button onClick={() => setNewKey(null)} className="px-3 py-2 text-sm text-gray-500">Done</button>
                  </div>
                </div>
              )}

              {/* create */}
              <div className="flex flex-wrap gap-2 items-end rounded-xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-4">
                <div className="flex-1 min-w-[160px]">
                  <label className="block text-xs text-gray-500 dark:text-neutral-400 mb-1">Key name</label>
                  <input className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-neutral-700 bg-transparent text-sm text-black dark:text-white outline-none" placeholder="e.g. production" value={name} onChange={(e) => setName(e.target.value)} />
                </div>
                <div className="w-32">
                  <label className="block text-xs text-gray-500 dark:text-neutral-400 mb-1">Daily quota</label>
                  <input className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-neutral-700 bg-transparent text-sm text-black dark:text-white outline-none" placeholder="0 = ∞" value={quota} onChange={(e) => setQuota(e.target.value.replace(/\D/g, ''))} />
                </div>
                <button onClick={createKey} className="px-4 py-2 rounded-lg bg-black dark:bg-white text-white dark:text-black text-sm font-medium">Create key</button>
              </div>

              {error && <p className="text-xs text-red-500">{error}</p>}
              {loading && <p className="text-xs text-gray-500">Loading…</p>}

              {/* list */}
              {keys.length === 0 && !loading ? (
                <p className="text-sm text-gray-500 dark:text-neutral-400">No keys yet — create one above.</p>
              ) : (
                <div className="space-y-2">
                  {keys.map((k) => (
                    <div key={k.id} className={`rounded-xl border p-4 ${k.revoked ? 'border-red-200 dark:border-red-500/20 opacity-60' : 'border-gray-200 dark:border-neutral-800'} bg-white dark:bg-neutral-900`}>
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-black dark:text-white">{k.name}</span>
                            {k.revoked && <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-300">revoked</span>}
                          </div>
                          <code className="text-xs text-gray-500 dark:text-neutral-400">{k.prefix}</code>
                          <div className="text-[11px] text-gray-400 dark:text-neutral-500 mt-1">created {fmtDate(k.created_at)} · last used {fmtDate(k.last_used_at)}</div>
                        </div>
                        {!k.revoked && (
                          <div className="flex gap-2 shrink-0">
                            <button onClick={() => rotateKey(k.id)} className="text-xs px-2 py-1 rounded border border-gray-200 dark:border-neutral-700 text-gray-600 dark:text-neutral-300">Rotate</button>
                            <button onClick={() => revokeKey(k.id)} className="text-xs px-2 py-1 rounded border border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-400">Revoke</button>
                          </div>
                        )}
                      </div>
                      <div className="mt-3"><UsageBar used={k.usage_count} quota={k.quota} /></div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </Section>

        {/* ---- DOCS ---- */}
        <Section title="The API" subtitle="One endpoint. The mode selects the tool; the response is always JSON.">
          <Code>{`POST ${'{BASE_URL}'}/api/v1/query
X-API-Key: <your key>
Content-Type: application/json

{ "mode": "search", "query": "best laptops 2026",
  "options": { "synthesize": true, "max_sources": 10, "urls": [] } }`}</Code>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-gray-500 dark:text-neutral-400 text-xs"><th className="py-1 pr-4">mode</th><th className="py-1">what you get</th></tr></thead>
              <tbody className="text-gray-700 dark:text-neutral-300">
                {MODES.map(([m, d]) => (
                  <tr key={m} className="border-t border-gray-100 dark:border-neutral-800">
                    <td className="py-2 pr-4"><code>{m}</code></td><td className="py-2">{d}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <ul className="text-sm text-gray-600 dark:text-neutral-300 list-disc ml-5 mt-4 space-y-1">
            <li><code>synthesize: true</code> adds an LLM <code>answer</code> field on top of the raw <code>data</code> (analyze always synthesizes). It costs more, so it counts heavier against quota.</li>
            <li><b>Link mode:</b> put a URL in <code>query</code> or <code>options.urls</code> → those pages are read directly (SSRF-guarded), no web search.</li>
            <li><b>Auth:</b> send <code>X-API-Key</code>. Missing/invalid → <code>401</code>; over quota → <code>429</code>.</li>
            <li><b>Caching:</b> identical queries within the TTL return instantly (<code>meta.cached: true</code>).</li>
          </ul>

          <p className="text-sm text-gray-600 dark:text-neutral-400 mt-4">
            Full schema / Postman import: <code>{'{BASE_URL}'}/openapi.json</code> · interactive docs at <code>{'{BASE_URL}'}/docs</code>.
          </p>
        </Section>

        {/* ---- SELF-HOST ---- */}
        <Section title="Self-host" subtitle="Run the open-source engine with your own keys — no quota, no Supabase needed.">
          <div id="selfhost">
            <Code>{`git clone <repo> && cd backend
cp .env.example .env     # set SERPAPI_KEY, GEMINI_API_KEY, API_KEY (any secret)
docker compose up        # -> http://localhost:8000/api/v1/query`}</Code>
          </div>
        </Section>
      </div>
    </div>
  );
};

export default Developers;
