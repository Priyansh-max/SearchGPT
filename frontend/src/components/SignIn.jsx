import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import AnimatedSearchPanel from './AnimatedSearchPanel';
import { login, signup, loginWithGoogle } from '../services/auth';

const GoogleIcon = () => (
  <svg className="w-4 h-4" viewBox="0 0 48 48"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.4 29.3 35 24 35c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.1 5.1 29.3 3 24 3 12.4 3 3 12.4 3 24s9.4 21 21 21 21-9.4 21-21c0-1.2-.1-2.3-.4-3.5z" /><path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 13 24 13c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.1 5.1 29.3 3 24 3 16 3 9.1 7.6 6.3 14.7z" /><path fill="#4CAF50" d="M24 45c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 36 26.7 37 24 37c-5.3 0-9.7-2.6-11.3-7l-6.5 5C9 40.3 15.9 45 24 45z" /><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.3 4.2-4.1 5.6l6.2 5.2C40.9 36.6 45 31 45 24c0-1.2-.1-2.3-.4-3.5z" /></svg>
);

const SignIn = () => {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get('next') || '/developers';

  const [mode, setMode] = useState(params.get('mode') === 'signup' ? 'signup' : 'login'); // login | signup
  const [form, setForm] = useState({ email: '', password: '', name: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault(); setError(''); setBusy(true);
    try {
      if (mode === 'login') await login(form.email, form.password);
      else await signup(form.email, form.password, form.name);
      navigate(next, { replace: true });
    } catch (err) {
      setError(err.message || 'Something went wrong');
    } finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen flex bg-white dark:bg-black">
      {/* left — animated graphic (hidden on small screens) */}
      <div className="hidden md:block md:w-1/2 h-screen sticky top-0">
        <AnimatedSearchPanel />
      </div>

      {/* right — auth form */}
      <div className="w-full md:w-1/2 flex items-center justify-center p-6">
        <div className="w-full max-w-sm">
          <button onClick={() => navigate('/')} className="text-sm text-gray-500 dark:text-neutral-400 hover:text-black dark:hover:text-white mb-8">← Home</button>

          <h1 className="text-2xl font-semibold text-black dark:text-white">
            {mode === 'login' ? 'Sign in' : 'Create your account'}
          </h1>
          <p className="text-sm text-gray-500 dark:text-neutral-400 mt-1 mb-6">
            {mode === 'login' ? 'Access your API keys, usage, and credits.' : 'Get API keys and free monthly credits.'}
          </p>

          {/* Google */}
          <button
            onClick={() => loginWithGoogle(next)}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg border border-gray-300 dark:border-neutral-700 text-sm font-medium text-gray-800 dark:text-neutral-100 hover:bg-gray-50 dark:hover:bg-neutral-900 transition-colors"
          >
            <GoogleIcon /> Continue with Google
          </button>

          {/* divider */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-gray-200 dark:bg-neutral-800" />
            <span className="text-xs text-gray-400">or</span>
            <div className="flex-1 h-px bg-gray-200 dark:bg-neutral-800" />
          </div>

          {/* email / password */}
          <form onSubmit={submit} className="space-y-3">
            {mode === 'signup' && (
              <input className="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-neutral-700 bg-transparent text-sm text-black dark:text-white outline-none focus:border-gray-500"
                placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            )}
            <input type="email" required className="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-neutral-700 bg-transparent text-sm text-black dark:text-white outline-none focus:border-gray-500"
              placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <input type="password" required className="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-neutral-700 bg-transparent text-sm text-black dark:text-white outline-none focus:border-gray-500"
              placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />

            {error && <p className="text-xs text-red-500">{error}</p>}

            <button disabled={busy} className="w-full py-2.5 rounded-lg bg-black dark:bg-white text-white dark:text-black text-sm font-medium disabled:opacity-60">
              {busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>

          <p className="text-sm text-gray-500 dark:text-neutral-400 mt-5">
            {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
            <button onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setError(''); }}
              className="text-black dark:text-white font-medium underline">
              {mode === 'login' ? 'Sign up' : 'Sign in'}
            </button>
          </p>

          <p className="text-[11px] text-gray-400 dark:text-neutral-500 mt-8">
            By continuing you agree to our <a href="#" className="underline">Terms</a> and <a href="#" className="underline">Privacy Policy</a>.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SignIn;
