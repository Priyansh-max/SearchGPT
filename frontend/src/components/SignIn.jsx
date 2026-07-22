import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { FiArrowLeft, FiChevronRight, FiCode, FiCopy, FiKey } from 'react-icons/fi';
import { loginWithGoogle, startEmailSignIn, verifyEmailCode } from '../services/auth';

const previewSteps = [
  {
    nav: 'Quickstart',
    eyebrow: 'Docs / Quickstart',
    title: 'Make your first request',
    body: 'Send a query, get structured JSON, then render it however your app needs.',
    method: 'POST',
    endpoint: '/api/v1/query',
    label: 'cURL',
    code: `curl -X POST /api/v1/query \\
  -H "X-API-Key: sk_..." \\
  -d '{
    "mode": "analyze",
    "query": "summarize this URL"
  }'`,
    status: '200 OK',
    response: '{ "sources_used": 4, "cached": false }',
  },
  {
    nav: 'API Reference',
    eyebrow: 'Docs / API Reference',
    title: 'One JSON envelope',
    body: 'Every mode returns the same top-level shape: mode, query, data, answer, and meta.',
    method: 'JSON',
    endpoint: 'response envelope',
    label: 'Response',
    code: `{
  "mode": "search",
  "query": "latest browser automation",
  "data": { "results": [] },
  "meta": { "provider": "gemini" }
}`,
    status: 'typed',
    response: '{ "answer": "Structured summary ready" }',
  },
  {
    nav: 'Examples',
    eyebrow: 'Docs / Examples',
    title: 'Test links directly',
    body: 'Paste a URL and SearchBot reads that page directly with SSRF protection enabled.',
    method: 'LINK',
    endpoint: 'link mode',
    label: 'JavaScript',
    code: `await fetch('/api/v1/query', {
  method: 'POST',
  headers: { 'X-API-Key': key },
  body: JSON.stringify({
    mode: 'analyze',
    query: 'summarize https://example.com'
  })
})`,
    status: 'safe',
    response: '{ "link_mode": true, "sources_used": 1 }',
  },
];

const GoogleIcon = () => (
  <svg className="h-4 w-4 shrink-0" viewBox="0 0 48 48" aria-hidden="true">
    <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.4 29.3 35 24 35c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.1 5.1 29.3 3 24 3 12.4 3 3 12.4 3 24s9.4 21 21 21 21-9.4 21-21c0-1.2-.1-2.3-.4-3.5z" />
    <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 13 24 13c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.1 5.1 29.3 3 24 3 16 3 9.1 7.6 6.3 14.7z" />
    <path fill="#4CAF50" d="M24 45c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 36 26.7 37 24 37c-5.3 0-9.7-2.6-11.3-7l-6.5 5C9 40.3 15.9 45 24 45z" />
    <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.3 4.2-4.1 5.6l6.2 5.2C40.9 36.6 45 31 45 24c0-1.2-.1-2.3-.4-3.5z" />
  </svg>
);

const DocPreview = () => {
  const [active, setActive] = useState(0);
  const step = previewSteps[active];

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActive((current) => (current + 1) % previewSteps.length);
    }, 2600);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <section className="hidden h-screen w-1/2 overflow-hidden border-r border-gray-200 bg-gray-50 px-8 py-6 dark:border-neutral-800 dark:bg-neutral-950 lg:flex">
      <style>{`@keyframes signinPreviewIn { from { opacity: .35; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }`}</style>
      <div className="mx-auto flex h-full w-full max-w-lg flex-col justify-center">
        <div className="mb-5">
          <h2 className="max-w-xs text-2xl font-semibold leading-tight text-gray-950 dark:text-white">
            Developer access for live web data.
          </h2>
        </div>

        <div className="relative">
          <div className="absolute -right-3 top-8 h-28 w-28 rounded-full bg-emerald-100 opacity-60 blur-3xl dark:bg-emerald-500/10" />
          <div className="relative overflow-hidden rounded-lg border border-[#2b342f] bg-[#101411] shadow-2xl shadow-black/20">
            <div className="flex h-10 items-center justify-between border-b border-[#2b342f] px-3">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
                <span className="h-2.5 w-2.5 rounded-full bg-yellow-400" />
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
              </div>
              <span className="rounded-full bg-[#1b211d] px-2 py-1 text-[11px] font-medium text-[#9fa9a3]">docs.searchbot.dev</span>
            </div>

            <div className="grid h-[430px] grid-cols-[136px_1fr]">
              <aside className="border-r border-[#2b342f] bg-[#141a16] p-3">
                {['Quickstart', 'API Reference', 'Examples', 'Self-hosting'].map((item) => (
                  <div
                    key={item}
                    className={`mb-1 rounded-md px-2 py-1.5 text-xs transition-all duration-500 ${item === step.nav
                      ? 'translate-x-0 bg-[#d8f3df] font-medium text-[#101411] shadow-sm'
                      : 'text-[#98a39d]'}`}
                  >
                    {item}
                  </div>
                ))}
              </aside>

              <main className="relative overflow-hidden p-4">
                <div className="mb-4 flex items-center gap-2 text-xs text-[#8f9a94] transition-colors duration-500">
                  <span>{step.eyebrow.split(' / ')[0]}</span>
                  <FiChevronRight className="h-3 w-3" />
                  <span>{step.eyebrow.split(' / ')[1]}</span>
                </div>

                <div key={`copy-${active}`} style={{ animation: 'signinPreviewIn 420ms ease-out' }}>
                  <div className="mb-4">
                    <h3 className="text-lg font-semibold text-[#f4f7f2]">{step.title}</h3>
                  </div>

                  <div className="mb-3 flex gap-2">
                    <span className="rounded-md bg-[#d8f3df] px-2 py-1 text-[11px] font-medium text-[#101411]">{step.method}</span>
                    <span className="rounded-md border border-[#334039] px-2 py-1 font-mono text-[11px] text-[#b9c4be]">{step.endpoint}</span>
                  </div>

                  <div className="rounded-md border border-[#334039] bg-[#080b09] p-3">
                    <div className="mb-2 flex items-center justify-between text-[11px] text-[#87928c]">
                      <span>{step.label}</span>
                      <FiCopy className="h-3.5 w-3.5" />
                    </div>
                    <pre className="h-[116px] overflow-hidden text-[11px] leading-5 text-gray-100"><code>{step.code}</code></pre>
                  </div>
                </div>

                <div className="mt-3 rounded-md border border-[#334039] bg-[#141a16] p-2.5 text-[11px] shadow-sm transition-all duration-500">
                  <div className="mb-1.5 flex items-center justify-between text-[#98a39d]">
                    <span>Response</span>
                    <span className="flex items-center gap-1 font-medium text-[#9cedb6]">
                      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
                      {step.status}
                    </span>
                  </div>
                  <p key={`response-${active}`} className="font-mono text-[#dce5df]" style={{ animation: 'signinPreviewIn 420ms ease-out' }}>
                    {step.response}
                  </p>
                </div>

                <div className="mt-3 flex gap-1.5">
                  {previewSteps.map((item, index) => (
                    <button
                      key={item.nav}
                      aria-label={`Show ${item.nav}`}
                      onClick={() => setActive(index)}
                      className={`h-1.5 rounded-full transition-all duration-500 ${index === active
                        ? 'w-8 bg-[#d8f3df]'
                        : 'w-1.5 bg-[#3b453f]'}`}
                      type="button"
                    />
                  ))}
                </div>

                <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-[#101411] to-transparent" />
              </main>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

const SignIn = () => {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get('next') || '/';

  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [sent, setSent] = useState(false);
  const [devCode, setDevCode] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      if (!sent) {
        const result = await startEmailSignIn(email);
        setSent(true);
        setDevCode(result.dev_code || '');
      } else {
        const result = await verifyEmailCode(email, code);
        const destination = result.user?.onboarding_completed ? next : `/onboarding?next=${encodeURIComponent(next)}`;
        navigate(destination, { replace: true });
      }
    } catch (err) {
      setError(err.message || 'Something went wrong');
    } finally {
      setBusy(false);
    }
  };

  const editEmail = () => {
    setSent(false);
    setCode('');
    setDevCode('');
    setError('');
  };

  return (
    <main className="min-h-screen bg-white text-gray-950 dark:bg-black dark:text-white lg:flex lg:h-screen lg:overflow-hidden">
      <DocPreview />

      <section className="flex min-h-screen w-full items-center justify-center px-5 py-8 lg:h-screen lg:w-1/2 lg:min-h-0 lg:px-10 lg:py-6">
        <div className="w-full max-w-sm">
          <button
            onClick={() => navigate('/')}
            className="mb-9 inline-flex items-center gap-2 text-sm font-medium text-gray-500 transition-colors hover:text-gray-950 dark:text-neutral-500 dark:hover:text-white"
            type="button"
          >
            <FiArrowLeft className="h-4 w-4" />
            Home
          </button>

          <div className="mb-7">
            <h1 className="text-3xl font-semibold tracking-normal text-gray-950 dark:text-white">
              Sign in to your account
            </h1>
            <p className="mt-3 text-sm leading-6 text-gray-600 dark:text-neutral-400">
              {sent ? 'Enter the code we sent to your email.' : 'Use Google or continue with email.'}
            </p>
          </div>

          <button
            onClick={() => loginWithGoogle(next)}
            className="flex w-full items-center justify-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-800 transition-colors hover:bg-gray-50 dark:border-neutral-800 dark:bg-black dark:text-neutral-100 dark:hover:bg-neutral-950"
            type="button"
          >
            <GoogleIcon />
            Continue with Google
          </button>

          <div className="my-5 flex items-center gap-3">
            <div className="h-px flex-1 bg-gray-200 dark:bg-neutral-800" />
            <span className="text-xs text-gray-400 dark:text-neutral-600">or</span>
            <div className="h-px flex-1 bg-gray-200 dark:bg-neutral-800" />
          </div>

          <form onSubmit={submit} className="space-y-3">
            <label className="block">
              <span className="mb-1.5 block text-xs font-medium text-gray-600 dark:text-neutral-400">Email</span>
              <input
                type="email"
                required
                disabled={sent}
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-950 outline-none transition-colors placeholder:text-gray-400 focus:border-gray-500 disabled:bg-gray-50 disabled:text-gray-500 dark:border-neutral-800 dark:bg-black dark:text-white dark:placeholder:text-neutral-600 dark:focus:border-neutral-500 dark:disabled:bg-neutral-950 dark:disabled:text-neutral-500"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </label>

            {sent && (
              <label className="block">
                <span className="mb-1.5 block text-xs font-medium text-gray-600 dark:text-neutral-400">Code</span>
                <input
                  inputMode="numeric"
                  required
                  maxLength={6}
                  className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-sm tracking-[0.35em] text-gray-950 outline-none transition-colors placeholder:tracking-normal placeholder:text-gray-400 focus:border-gray-500 dark:border-neutral-800 dark:bg-black dark:text-white dark:placeholder:text-neutral-600 dark:focus:border-neutral-500"
                  placeholder="000000"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                />
              </label>
            )}

            {devCode && (
              <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-300">
                Dev code: <span className="font-mono">{devCode}</span>
              </p>
            )}

            {error && (
              <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">
                {error}
              </p>
            )}

            <button
              disabled={busy}
              className="w-full rounded-md bg-gray-950 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-black dark:hover:bg-neutral-200"
              type="submit"
            >
              {busy ? 'Please wait...' : sent ? 'Verify code' : 'Continue with email'}
            </button>
          </form>

          {sent && (
            <p className="mt-6 text-center text-sm text-gray-600 dark:text-neutral-400">
              Wrong email?{' '}
              <button onClick={editEmail} className="font-medium text-gray-950 underline underline-offset-4 dark:text-white" type="button">
                Change it
              </button>
            </p>
          )}
        </div>
      </section>
    </main>
  );
};

export default SignIn;