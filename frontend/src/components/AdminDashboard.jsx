import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, CartesianGrid,
} from 'recharts';
import { API_CONFIG } from '../config';

const API = API_CONFIG.BASE_URL;

// Mock so the dashboard renders even offline / before the API has data.
const MOCK = {
  total: 1284,
  by_mode: { search: 720, analyze: 310, scrape: 180, news: 74 },
  by_provider: { gemini: 980, openai: 220 },
  cache_hit_rate: 0.38,
  avg_latency_ms: 2140,
  queries_by_day: { d1: 120, d2: 180, d3: 150, d4: 220, d5: 260, d6: 190, d7: 164 },
};

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
const toArr = (obj, k = 'name', v = 'value') =>
  Object.entries(obj || {}).map(([key, val]) => ({ [k]: key, [v]: val }));

const Card = ({ title, children }) => (
  <div className="rounded-xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-4">
    <h3 className="text-sm font-medium text-gray-500 dark:text-neutral-400 mb-3">{title}</h3>
    {children}
  </div>
);

const Stat = ({ label, value }) => (
  <div className="rounded-xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-4">
    <div className="text-2xl font-semibold text-black dark:text-white">{value}</div>
    <div className="text-xs text-gray-500 dark:text-neutral-400 mt-1">{label}</div>
  </div>
);

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [token, setToken] = useState(() => localStorage.getItem('admin_token') || '');
  const [creds, setCreds] = useState({ username: '', password: '' });
  const [data, setData] = useState(null);
  const [usingMock, setUsingMock] = useState(false);
  const [error, setError] = useState('');

  const loadSummary = useCallback(async (tok) => {
    try {
      const r = await fetch(`${API}/api/admin/analytics/summary`, {
        headers: { Authorization: `Bearer ${tok}` },
      });
      if (r.status === 401) { setToken(''); localStorage.removeItem('admin_token'); return; }
      if (!r.ok) throw new Error('bad response');
      const json = await r.json();
      setData(json.total ? json : MOCK);
      setUsingMock(!json.total);
    } catch {
      setData(MOCK);             // offline / unreachable → show mock so the UI renders
      setUsingMock(true);
    }
  }, []);

  useEffect(() => { if (token) loadSummary(token); }, [token, loadSummary]);

  const login = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const r = await fetch(`${API}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(creds),
      });
      if (!r.ok) { setError(r.status === 401 ? 'Invalid credentials' : 'Login unavailable'); return; }
      const { token: tok } = await r.json();
      localStorage.setItem('admin_token', tok);
      setToken(tok);
    } catch {
      setError('Could not reach the server');
    }
  };

  const logout = () => { localStorage.removeItem('admin_token'); setToken(''); setData(null); };

  if (!token) {
    return (
      <div className="min-h-screen bg-neutral-100 dark:bg-black flex items-center justify-center p-4">
        <form onSubmit={login} className="w-full max-w-sm rounded-2xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6">
          <h1 className="text-lg font-semibold text-black dark:text-white mb-1">Admin Dashboard</h1>
          <p className="text-xs text-gray-500 dark:text-neutral-400 mb-4">Private analytics — sign in to continue.</p>
          <input className="w-full mb-3 px-3 py-2 rounded-lg border border-gray-200 dark:border-neutral-700 bg-transparent text-sm text-black dark:text-white outline-none"
            placeholder="Username" value={creds.username}
            onChange={(e) => setCreds({ ...creds, username: e.target.value })} />
          <input type="password" className="w-full mb-4 px-3 py-2 rounded-lg border border-gray-200 dark:border-neutral-700 bg-transparent text-sm text-black dark:text-white outline-none"
            placeholder="Password" value={creds.password}
            onChange={(e) => setCreds({ ...creds, password: e.target.value })} />
          {error && <p className="text-xs text-red-500 mb-3">{error}</p>}
          <button className="w-full py-2 rounded-lg bg-black dark:bg-white text-white dark:text-black text-sm font-medium">Sign in</button>
          <button type="button" onClick={() => navigate('/')} className="w-full mt-2 py-2 text-xs text-gray-500 dark:text-neutral-400">Back home</button>
        </form>
      </div>
    );
  }

  const d = data || MOCK;
  const days = toArr(d.queries_by_day, 'day', 'count');
  const modes = toArr(d.by_mode);
  const providers = toArr(d.by_provider);

  return (
    <div className="min-h-screen bg-neutral-100 dark:bg-black p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-semibold text-black dark:text-white">Analytics</h1>
            {usingMock && <span className="text-xs text-amber-600 dark:text-amber-400">showing sample data (API unreachable or empty)</span>}
          </div>
          <button onClick={logout} className="text-sm text-gray-500 dark:text-neutral-400 hover:text-black dark:hover:text-white">Sign out</button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Stat label="Total queries" value={d.total} />
          <Stat label="Cache hit rate" value={`${Math.round((d.cache_hit_rate || 0) * 100)}%`} />
          <Stat label="Avg latency" value={`${Math.round(d.avg_latency_ms || 0)} ms`} />
          <Stat label="Providers" value={providers.length} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card title="Queries over time">
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={days}>
                <CartesianGrid strokeDasharray="3 3" stroke="#8884" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          <Card title="Queries by mode">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={modes}>
                <CartesianGrid strokeDasharray="3 3" stroke="#8884" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {modes.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card title="Provider mix (Gemini vs OpenAI fallback)">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={providers} dataKey="value" nameKey="name" outerRadius={80} label>
                  {providers.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>

          <Card title="Notes">
            <ul className="text-sm text-gray-600 dark:text-neutral-300 space-y-2 list-disc ml-4">
              <li>Data from <code>/api/admin/analytics/summary</code> (token-gated).</li>
              <li>Anonymous playground visitors tracked by client_id; API users by key.</li>
              <li>IPs stored hashed. Analytics off by default for self-host.</li>
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
