import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { FiArrowRight, FiCheck, FiGift, FiUser } from 'react-icons/fi';
import { completeOnboarding, me } from '../services/auth';

const heardOptions = ['X / Twitter', 'LinkedIn', 'GitHub', 'Google', 'Friend', 'AI community', 'Other'];
const avatarSeeds = ['nova', 'pixel', 'orbit', 'atlas'];
const avatarForEmail = (email = '') => {
  const total = [...email].reduce((sum, char) => sum + char.charCodeAt(0), 0);
  const seed = avatarSeeds[total % avatarSeeds.length];
  return `https://api.dicebear.com/9.x/thumbs/svg?seed=${seed}&backgroundColor=f3f4f6,e5e7eb,d1d5db&radius=18`;
};

const useCaseOptions = [
  { id: 'fast-web-api', label: 'Fast web search API', body: 'Structured JSON for agents, tools, and Postman.' },
  { id: 'deep-research', label: 'Deep research', body: 'Scraped sources, synthesis, citations, and context packs.' },
  { id: 'custom-policies', label: 'Custom context policies', body: 'Control sources, cleanup, output format, and guardrails.' },
  { id: 'observability', label: 'Observability', body: 'Trace what was fetched, skipped, used, and cached.' },
  { id: 'self-hosting', label: 'Self-hosting', body: 'Run the core engine with your own keys and infrastructure.' },
  { id: 'playground', label: 'Playground demo', body: 'Use the product UI to test workflows before integrating.' },
];

const Confetti = () => (
  <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
    {Array.from({ length: 42 }).map((_, i) => (
      <span
        key={i}
        className={`${i % 4 === 0 ? 'h-1.5 w-4' : 'h-3 w-1.5'} absolute -top-6 rounded-sm opacity-80`}
        style={{
          left: `${4 + ((i * 19) % 92)}%`,
          background: ['#111827', '#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'][i % 6],
          animation: `confettiFall ${3.2 + (i % 6) * 0.36}s linear ${i * 0.08}s infinite`,
        }}
      />
    ))}
  </div>
);


const Onboarding = () => {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get('next') || '/';
  const [step, setStep] = useState(1);
  const [user, setUser] = useState(null);
  const [name, setName] = useState('');
  const [picture, setPicture] = useState('');
  const [heardAbout, setHeardAbout] = useState('');
  const [heardAboutOther, setHeardAboutOther] = useState('');
  const [useCases, setUseCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);

  useEffect(() => {
    let alive = true;
    me().then((current) => {
      if (!alive) return;
      if (!current) {
        navigate('/signin?next=/onboarding', { replace: true });
        return;
      }
      if (current.onboarding_completed) {
        navigate(next, { replace: true });
        return;
      }
      setUser(current);
      setName(current.name || '');
      setPicture(current.picture || avatarForEmail(current.email));
      setLoading(false);
    });
    return () => { alive = false; };
  }, [navigate, next]);

  const initials = useMemo(() => {
    const label = name || user?.email || 'S';
    return label.split(/[\s@.]+/).filter(Boolean).slice(0, 2).map((x) => x[0]?.toUpperCase()).join('') || 'S';
  }, [name, user]);

  const toggleCase = (id) => {
    setUseCases((current) => current.includes(id) ? current.filter((x) => x !== id) : [...current, id]);
  };

  const heardAboutValue = heardAbout === 'Other' ? `Other: ${heardAboutOther.trim()}` : heardAbout;

  const submitProfile = (event) => {
    event.preventDefault();
    setError('');
    if (!name.trim()) {
      setError('Add your name to continue.');
      return;
    }
    if (!heardAbout.trim()) {
      setError('Select where you heard about us.');
      return;
    }
    if (heardAbout === 'Other' && !heardAboutOther.trim()) {
      setError('Fields cannot be empty.');
      return;
    }
    setStep(2);
  };

  const finish = async () => {
    setError('');
    if (useCases.length === 0) {
      setError('Pick at least one reason.');
      return;
    }
    setBusy(true);
    try {
      await completeOnboarding({
        name: name.trim(),
        picture: picture.trim(),
        heard_about: heardAboutValue,
        use_cases: useCases,
      });
      setDone(true);
    } catch (err) {
      setError(err.message || 'Could not finish onboarding');
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-white text-black dark:bg-black dark:text-white">
        <p className="text-sm text-gray-500 dark:text-neutral-400">Preparing your workspace...</p>
      </main>
    );
  }

  const trackerStep = done ? 3 : step;
  const tracker = [
    { id: 1, label: 'About you' },
    { id: 2, label: 'Intent' },
    { id: 3, label: 'Ready' },
  ];
  const progress = done ? 100 : step === 2 ? 66 : 18;

  return (
    <main className="relative flex h-screen flex-col overflow-hidden bg-white text-black dark:bg-black dark:text-white">
      <style>{`
        @keyframes confettiFall {
          0% { opacity: 0; transform: translateY(-24px) rotate(0deg); }
          8% { opacity: .95; }
          100% { opacity: 0; transform: translateY(112vh) rotate(520deg); }
        }
        @keyframes successIn {
          0% { opacity: 0; transform: translateY(10px); }
          100% { opacity: 1; transform: translateY(0); }
        }
        .success-copy { animation: successIn .45s ease-out both; }
      `}</style>
      {done && <Confetti />}

      <header className="mx-auto flex h-14 w-full max-w-3xl items-center justify-center px-5">
        <div className="text-sm font-semibold">Onboarding</div>
      </header>

      <section className="mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col px-5 pb-6 pt-2">
        <nav className="mx-auto mb-7 w-full max-w-2xl" aria-label="Onboarding progress">
          <div className="relative pt-4">
            <div className="absolute left-0 right-0 top-5 h-1 rounded-full bg-gray-100 dark:bg-neutral-900" />
            <div className="absolute left-0 top-5 h-1 rounded-full bg-black transition-all duration-500 dark:bg-white" style={{ width: `${progress}%` }} />
            <div className="relative grid grid-cols-3">
              {tracker.map((item) => {
                const active = trackerStep === item.id;
                const complete = trackerStep > item.id;
                return (
                  <div key={item.id} className={`flex ${item.id === 1 ? 'justify-start' : item.id === 2 ? 'justify-center' : 'justify-end'}`}>
                    <div className="flex flex-col items-center gap-2">
                      <span className={`h-3 w-3 rounded-full border-2 transition-colors ${active || complete ? 'border-black bg-black dark:border-white dark:bg-white' : 'border-gray-200 bg-white dark:border-neutral-800 dark:bg-black'}`} />
                      <span className={`text-xs font-medium ${active ? 'text-black dark:text-white' : complete ? 'text-gray-500 dark:text-neutral-500' : 'text-gray-300 dark:text-neutral-700'}`}>{item.label}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </nav>

        {done ? (
          <div className="relative z-10 flex flex-1 flex-col items-center justify-center text-center">
            <div className="success-copy">
              <div className="mb-3 inline-flex items-center rounded-md border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-normal text-emerald-700 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-300">
                Free credits unlocked
              </div>
              <h1 className="text-4xl font-semibold tracking-normal sm:text-5xl">1000 free credits</h1>
              <p className="mt-3 text-sm text-gray-500 dark:text-neutral-400">Added to your account.</p>
              <button
                type="button"
                onClick={() => navigate('/', { replace: true })}
                className="mt-8 inline-flex items-center justify-center gap-2 rounded-md bg-black px-6 py-3 text-sm font-medium text-white hover:bg-gray-800 dark:bg-white dark:text-black dark:hover:bg-neutral-200"
              >
                Continue <FiArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        ) : step === 1 ? (
          <form onSubmit={submitProfile} className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center">
            <div className="mb-5">
              <h1 className="text-2xl font-semibold tracking-normal sm:text-3xl">Make it yours</h1>
            </div>

            <div className="mb-5 flex items-center gap-3">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-gray-200 bg-gray-50 text-lg font-semibold text-gray-700 dark:border-neutral-800 dark:bg-neutral-950 dark:text-neutral-200">
                {picture ? <img src={picture} alt="Profile avatar" className="h-full w-full object-cover" /> : initials}
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-medium text-black dark:text-white">{user?.email}</div>
                <div className="mt-1 text-xs text-gray-500 dark:text-neutral-500">Profile can be changed later.</div>
              </div>
            </div>

            <label className="block">
              <span className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-gray-600 dark:text-neutral-400"><FiUser className="h-3.5 w-3.5" /> Name</span>
              <input value={name} onChange={(e) => setName(e.target.value)} className="w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-gray-500 dark:border-neutral-800 dark:bg-black dark:text-white" placeholder="Your name" />
            </label>

            <div className="mt-5">
              <div className="mb-3 text-xs font-medium text-gray-600 dark:text-neutral-400">Where did you hear about us?</div>
              <div className="flex flex-wrap gap-2">
                {heardOptions.map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => {
                      setHeardAbout(item);
                      if (item !== 'Other') setHeardAboutOther('');
                    }}
                    className={`rounded-md border px-3 py-1.5 text-sm transition-colors ${heardAbout === item ? 'border-black bg-black text-white dark:border-white dark:bg-white dark:text-black' : 'border-gray-300 text-gray-600 hover:border-gray-500 dark:border-neutral-800 dark:text-neutral-300 dark:hover:border-neutral-600'}`}
                  >
                    {item}
                  </button>
                ))}
              </div>
              {heardAbout === 'Other' && (
                <input
                  value={heardAboutOther}
                  onChange={(e) => setHeardAboutOther(e.target.value)}
                  className="mt-3 w-full rounded-md border border-gray-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-gray-500 dark:border-neutral-800 dark:bg-black dark:text-white"
                  placeholder="Where did you hear about us?"
                />
              )}
            </div>

            {error && <p className="mt-5 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">{error}</p>}

            <div className="mt-6 flex justify-end">
              <button type="submit" className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-black px-5 py-2.5 text-sm font-medium text-white hover:bg-gray-800 dark:bg-white dark:text-black dark:hover:bg-neutral-200 sm:w-auto">
                Continue <FiArrowRight className="h-4 w-4" />
              </button>
            </div>
          </form>
        ) : (
          <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center">
            <div className="mb-5">
              <h1 className="text-2xl font-semibold tracking-normal sm:text-3xl">What are you building?</h1>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              {useCaseOptions.map((item) => {
                const active = useCases.includes(item.id);
                return (
                  <button key={item.id} type="button" onClick={() => toggleCase(item.id)} className={`min-h-[92px] rounded-lg border p-3 text-left transition-colors ${active ? 'border-black bg-black text-white dark:border-white dark:bg-white dark:text-black' : 'border-gray-200 bg-white text-black hover:border-gray-400 dark:border-neutral-800 dark:bg-black dark:text-white dark:hover:border-neutral-600'}`}>
                    <div className="flex items-start justify-between gap-3">
                      <span className="text-sm font-semibold leading-5">{item.label}</span>
                      <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border ${active ? 'border-white bg-white text-black dark:border-black dark:bg-black dark:text-white' : 'border-gray-300 dark:border-neutral-700'}`}>
                        {active && <FiCheck className="h-3.5 w-3.5" />}
                      </span>
                    </div>
                    <p className={`mt-2 text-xs leading-5 ${active ? 'text-gray-200 dark:text-neutral-700' : 'text-gray-500 dark:text-neutral-400'}`}>{item.body}</p>
                  </button>
                );
              })}
            </div>

            {error && <p className="mt-5 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">{error}</p>}

            <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
              <button type="button" onClick={() => setStep(1)} className="rounded-md border border-gray-300 px-5 py-2.5 text-sm font-medium text-gray-600 hover:border-gray-500 dark:border-neutral-800 dark:text-neutral-300 dark:hover:border-neutral-600">Back</button>
              <button type="button" disabled={busy} onClick={finish} className="inline-flex items-center justify-center gap-2 rounded-md bg-black px-5 py-2.5 text-sm font-medium text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-black dark:hover:bg-neutral-200">
                {busy ? 'Finishing...' : 'Finish setup'} <FiGift className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </section>
    </main>
  );
};

export default Onboarding;