import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, CartesianGrid,
} from 'recharts';
import { me, authFetch, isAuthed, logout } from '../services/auth';
import CodeTabs, { buildQuerySnippets } from './CodeTabs';

const TABS = [['keys', 'API Keys'], ['usage', 'Usage'], ['docs', 'Docs'], ['selfhost', 'Self-host']];
const MODES = ['search', 'scrape', 'analyze', 'news'];
const MODE_DESC = {
  search: 'Web search results (links + snippets).',
  scrape: 'Full text extracted from result pages.',
  analyze: 'Synthesized summary + key points (uses the LLM).',
  news: 'Recent news articles for the query.',
};
const MODE_COST = { search: 1, news: 1, scrape: 2, analyze: 3 };
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
const fmtDate = (t) => (t ? new Date(t * 1000).toLocaleDateString() : '—');

const Code = ({ children }) => (
  <pre className="text-xs bg-neutral-100 dark:bg-neutral-950 border border-gray-200 dark:border-neutral-800 rounded-lg p-3 overflow-x-auto text-gray-800 dark:text-neutral-200 whitespace-pre-wrap">{children}</pre>
);

const Developers = () => {
  const navigate = useNavigate();
  const [tab, setTab] = useState('keys');
  const [user, setUser] = useState(null);
  const [keys, setKeys] = useState([]);
  const [usage, setUsage] = useState(null);
  const [creating, setCreating] = useState(false);
  const [newKey, setNewKey] = useState(null);
  const [form, setForm] = useState({ name: '', scopes: [...MODES] });
  const [copied, setCopied] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const gotoSignin = useCallback(() => navigate('/signin?next=/developers'), [navigate]);

  const loadAll = useCallback(async () => {
    setLoading(true);
    const u = await me();
    setUser(u);
    if (u) {
      try {
        const [kr, ur] = await Promise.all([authFetch('/api/account/keys'), authFetch('/api/account/usage')]);
        if (kr.ok) setKeys((await kr.json()).keys || []);
        if (ur.ok) setUsage(await ur.json());
      } catch { setError('Could not reach the API.'); }
    }
    setLoading(false);
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const startCreate = () => {
    if (!isAuthed()) { gotoSignin(); return; }   // gate the ACTION, not the tab
    setError(''); setForm({ name: '', scopes: [...MODES] }); setCreating(true);
  };
  const toggleScope = (m) =>
    setForm((f) => ({ ...f, scopes: f.scopes.includes(m) ? f.scopes.filter((x) => x !== m) : [...f.scopes, m] }));
  const submitCreate = async () => {
    if (form.scopes.length === 0) { setError('Pick at least one mode'); return; }
    try {
      const r = await authFetch('/api/account/keys', { method: 'POST', body: JSON.stringify({ name: form.name || 'key', scopes: form.scopes }) });
      if (!r.ok) throw new Error();
      setNewKey((await r.json()).key); setCreating(false); loadAll();
    } catch { setError('Could not create key'); }
  };
  const rotateKey = async (id) => {
    if (!window.confirm('Rotate this key? The old secret stops working immediately.')) return;
    const r = await authFetch(`/api/account/keys/${id}/rotate`, { method: 'POST' });
    if (r.ok) { setNewKey((await r.json()).key); loadAll(); }
  };
  const revokeKey = async (id) => {
    if (!window.confirm('Revoke this key? Use this if it leaked.')) return;
    const r = await authFetch(`/api/account/keys/${id}`, { method: 'DELETE' });
    if (r.ok) loadAll();
  };
  const copy = async (t, w) => { try { await navigator.clipboard.writeText(t); setCopied(w); setTimeout(() => setCopied(''), 1500); } catch {} };

  const acct = usage?.account || user;
  const remaining = acct ? acct.credits_remaining : 0;
  const quota = acct ? acct.monthly_quota : 0;
  const used = acct ? acct.credits_used : 0;
  const pct = quota ? Math.min(100, Math.round((used / quota) * 100)) : 0;
  const perKey = (usage?.per_key || []).filter((k) => k.credits_spent > 0);

  return (
    <div className="min-h-screen bg-neutral-100 dark:bg-black">
      <header className="border-b border-gray-200 dark:border-neutral-800 bg-white/80 dark:bg-neutral-900/80 backdrop-blur-sm sticky top-0 z-20">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <button onClick={() => navigate('/')} className="text-sm text-gray-600 dark:text-neutral-300 hover:text-black dark:hover:text-white">← SearchGPT Agent</button>
          <h1 className="text-base font-medium text-black dark:text-white">Developers</h1>
          {user
            ? <button onClick={() => { logout(); setUser(null); setKeys([]); setUsage(null); }} className="text-xs text-gray-500 dark:text-neutral-400 hover:text-black dark:hover:text-white">Sign out</button>
            : <button onClick={gotoSignin} className="text-xs text-black dark:text-white font-medium">Sign in</button>}
        </div>
        <div className="max-w-5xl mx-auto px-6">
          <nav className="flex gap-1">
            {TABS.map(([id, label]) => (
              <button key={id} onClick={() => setTab(id)}
                className={`px-4 py-2.5 text-sm -mb-px border-b-2 transition-colors ${
                  tab === id ? 'border-black dark:border-white text-black dark:text-white font-medium'
                             : 'border-transparent text-gray-500 dark:text-neutral-400 hover:text-black dark:hover:text-white'}`}>
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-8">
        {/* ===== API KEYS — info + Create button; form only on click (after auth) ===== */}
        {tab === 'keys' && (
          <div className="space-y-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-black dark:text-white">API keys</h2>
                <p className="text-sm text-gray-500 dark:text-neutral-400 mt-1 max-w-xl">
                  Create a key, choose which modes it can use, and call <code>/api/v1/query</code> with the
                  <code> X-API-Key</code> header. All your keys share one monthly credit pool.
                </p>
              </div>
              <button onClick={startCreate} className="shrink-0 inline-flex items-center gap-1 px-4 py-2 rounded-lg bg-black dark:bg-white text-white dark:text-black text-sm font-medium">
                <span className="text-base leading-none">+</span> Create API key
              </button>
            </div>

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

            {/* create form — only after clicking Create (and being signed in) */}
            {creating && (
              <div className="rounded-xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-5">
                <h3 className="text-sm font-medium text-black dark:text-white mb-3">New key</h3>
                <input className="w-full mb-3 px-3 py-2 rounded-lg border border-gray-200 dark:border-neutral-700 bg-transparent text-sm text-black dark:text-white outline-none"
                  placeholder="Key name (e.g. production)" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                <div className="text-xs text-gray-500 dark:text-neutral-400 mb-2">Allowed modes</div>
                <div className="flex flex-wrap gap-2 mb-4">
                  {MODES.map((m) => (
                    <button key={m} type="button" onClick={() => toggleScope(m)}
                      className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                        form.scopes.includes(m) ? 'border-black dark:border-white bg-black dark:bg-white text-white dark:text-black'
                                                : 'border-gray-300 dark:border-neutral-700 text-gray-600 dark:text-neutral-300'}`}>
                      {m}
                    </button>
                  ))}
                </div>
                {error && <p className="text-xs text-red-500 mb-2">{error}</p>}
                <div className="flex gap-2">
                  <button onClick={submitCreate} className="px-4 py-2 rounded-lg bg-black dark:bg-white text-white dark:text-black text-sm font-medium">Create</button>
                  <button onClick={() => setCreating(false)} className="px-4 py-2 rounded-lg border border-gray-200 dark:border-neutral-700 text-sm text-gray-600 dark:text-neutral-300">Cancel</button>
                </div>
              </div>
            )}

            {/* list (only when signed in) */}
            {isAuthed() && (loading ? <p className="text-xs text-gray-500">Loading…</p> : keys.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-neutral-400">No keys yet.</p>
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
                        <div className="flex flex-wrap gap-1 mt-2">
                          {(k.scopes || []).map((s) => <span key={s} className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-neutral-800 text-gray-600 dark:text-neutral-300">{s}</span>)}
                        </div>
                        <div className="text-[11px] text-gray-400 mt-2">created {fmtDate(k.created_at)} · {k.credits_spent} credits used</div>
                      </div>
                      {!k.revoked && (
                        <div className="flex gap-2 shrink-0">
                          <button onClick={() => rotateKey(k.id)} className="text-xs px-2 py-1 rounded border border-gray-200 dark:border-neutral-700 text-gray-600 dark:text-neutral-300">Rotate</button>
                          <button onClick={() => revokeKey(k.id)} className="text-xs px-2 py-1 rounded border border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-400">Revoke</button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}

        {/* ===== USAGE — credit balance (cool) + graphs; sign-in gated ===== */}
        {tab === 'usage' && (
          !isAuthed() ? (
            <div className="rounded-xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-8 text-center">
              <p className="text-sm text-gray-600 dark:text-neutral-300 mb-4">Sign in to see your credits and usage.</p>
              <button onClick={gotoSignin} className="px-5 py-2.5 rounded-lg bg-black dark:bg-white text-white dark:text-black text-sm font-medium">Sign in</button>
            </div>
          ) : (
            <div className="space-y-5">
              {/* cool gradient credit card */}
              <div className="relative overflow-hidden rounded-2xl p-6 text-white"
                style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 55%, #2563eb 100%)' }}>
                <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'radial-gradient(rgba(255,255,255,0.5) 1px, transparent 1px)', backgroundSize: '22px 22px' }} />
                <div className="relative">
                  <div className="text-xs uppercase tracking-wider text-blue-200">Credits this month</div>
                  <div className="mt-1 text-4xl font-semibold">{remaining.toLocaleString()}<span className="text-lg font-normal text-blue-200"> / {quota.toLocaleString()}</span></div>
                  <div className="mt-4 h-2 rounded-full bg-white/20 overflow-hidden">
                    <div className="h-full bg-white" style={{ width: `${pct}%` }} />
                  </div>
                  <div className="mt-2 flex justify-between text-xs text-blue-100">
                    <span>{used.toLocaleString()} used</span><span>resets monthly · shared across keys</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="rounded-xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-4">
                  <h3 className="text-sm font-medium text-gray-500 dark:text-neutral-400 mb-3">Credits spent per key</h3>
                  {perKey.length === 0 ? <p className="text-sm text-gray-400 py-12 text-center">No usage yet.</p> : (
                    <ResponsiveContainer width="100%" height={240}>
                      <BarChart data={perKey}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#8884" />
                        <XAxis dataKey="name" tick={{ fontSize: 11 }} /><YAxis tick={{ fontSize: 11 }} /><Tooltip />
                        <Bar dataKey="credits_spent" radius={[4, 4, 0, 0]}>{perKey.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
                <div className="rounded-xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-4">
                  <h3 className="text-sm font-medium text-gray-500 dark:text-neutral-400 mb-3">Share of credits</h3>
                  {perKey.length === 0 ? <p className="text-sm text-gray-400 py-12 text-center">No usage yet.</p> : (
                    <ResponsiveContainer width="100%" height={240}>
                      <PieChart><Pie data={perKey} dataKey="credits_spent" nameKey="name" outerRadius={90} label>{perKey.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie><Tooltip /></PieChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>
            </div>
          )
        )}

        {/* ===== DOCS — multi-language snippets ===== */}
        {tab === 'docs' && (
          <div>
            <h2 className="text-lg font-semibold text-black dark:text-white mb-1">The API</h2>
            <p className="text-sm text-gray-500 dark:text-neutral-400 mb-4">One endpoint. The mode selects the tool; the response is always JSON.</p>
            <CodeTabs tabs={buildQuerySnippets({})} />
            <div className="mt-5 overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="text-left text-gray-500 dark:text-neutral-400 text-xs"><th className="py-1 pr-4">mode</th><th className="py-1 pr-4">credits</th><th className="py-1">what you get</th></tr></thead>
                <tbody className="text-gray-700 dark:text-neutral-300">
                  {MODES.map((m) => (
                    <tr key={m} className="border-t border-gray-100 dark:border-neutral-800">
                      <td className="py-2 pr-4"><code>{m}</code></td><td className="py-2 pr-4">{MODE_COST[m]}</td><td className="py-2">{MODE_DESC[m]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <ul className="text-sm text-gray-600 dark:text-neutral-300 list-disc ml-5 mt-4 space-y-1">
              <li><code>synthesize: true</code> adds an LLM <code>answer</code> (+2 credits). Analyze always synthesizes.</li>
              <li><b>Scopes:</b> a key only works for the modes you granted it; others return <code>403</code>.</li>
              <li><b>Link mode:</b> a URL in <code>query</code> or <code>options.urls</code> reads those pages directly (SSRF-guarded).</li>
              <li>Out of credits / invalid key → <code>429</code> / <code>401</code>. Caching returns <code>meta.cached: true</code>.</li>
            </ul>
            <p className="text-sm text-gray-600 dark:text-neutral-400 mt-4">Schema / Postman: <code>{'{BASE_URL}'}/openapi.json</code> · interactive docs at <code>{'{BASE_URL}'}/docs</code>.</p>
          </div>
        )}

        {/* ===== SELF-HOST ===== */}
        {tab === 'selfhost' && (
          <div>
            <h2 className="text-lg font-semibold text-black dark:text-white mb-1">Self-host</h2>
            <p className="text-sm text-gray-500 dark:text-neutral-400 mb-3">Run the open-source engine with your own keys — no credits, no Supabase needed.</p>
            <Code>{`git clone <repo> && cd backend
cp .env.example .env     # set SERPAPI_KEY, GEMINI_API_KEY, API_KEY (any secret)
docker compose up        # -> http://localhost:8000/api/v1/query`}</Code>
            <p className="text-sm text-gray-500 dark:text-neutral-400 mt-5 mb-2">Then call it the same way — in any language:</p>
            <CodeTabs tabs={buildQuerySnippets({ base: 'http://localhost:8000', apiKey: 'your_API_KEY' })} />
          </div>
        )}
      </div>
    </div>
  );
};

export default Developers;
