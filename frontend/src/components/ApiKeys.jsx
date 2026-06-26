import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const SAMPLE_KEY = 'sbk_live_3f9a1c7e8b24d05f6a1e9c2b7d4f8a30';

const CodeBlock = ({ children }) => (
  <pre className="text-xs bg-neutral-100 dark:bg-neutral-900 border border-gray-200 dark:border-neutral-800 rounded-lg p-3 overflow-x-auto text-gray-800 dark:text-neutral-200 whitespace-pre-wrap">
    {children}
  </pre>
);

const ApiKeys = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [key] = useState(SAMPLE_KEY);
  const [copied, setCopied] = useState('');

  const copy = async (text, what) => {
    try { await navigator.clipboard.writeText(text); setCopied(what); setTimeout(() => setCopied(''), 1500); } catch {}
  };

  return (
    <div className="min-h-screen bg-neutral-100 dark:bg-black p-4 md:p-8">
      <div className="max-w-3xl mx-auto">
        <button onClick={() => navigate('/')} className="text-sm text-gray-500 dark:text-neutral-400 hover:text-black dark:hover:text-white mb-4">← Back</button>
        <h1 className="text-2xl font-semibold text-black dark:text-white mb-2">Get an API key</h1>
        <p className="text-sm text-gray-600 dark:text-neutral-400 mb-6">
          One key, one endpoint. Use it from your app or right here in the playground.
        </p>

        {/* Hosted */}
        <div className="rounded-2xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-5 mb-4">
          <h2 className="text-base font-medium text-black dark:text-white mb-1">Hosted — magic link</h2>
          <p className="text-xs text-gray-500 dark:text-neutral-400 mb-3">Enter your email, click the link, and your key appears below. No password.</p>
          <div className="flex gap-2">
            <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com"
              className="flex-1 px-3 py-2 rounded-lg border border-gray-200 dark:border-neutral-700 bg-transparent text-sm text-black dark:text-white outline-none" />
            <button className="px-4 py-2 rounded-lg bg-black dark:bg-white text-white dark:text-black text-sm font-medium">Send link</button>
          </div>

          <div className="mt-4">
            <div className="text-xs text-gray-500 dark:text-neutral-400 mb-1">Your API key</div>
            <div className="flex items-center gap-2">
              <code className="flex-1 text-sm px-3 py-2 rounded-lg bg-neutral-100 dark:bg-neutral-950 border border-gray-200 dark:border-neutral-800 text-black dark:text-white truncate">{key}</code>
              <button onClick={() => copy(key, 'key')} className="px-3 py-2 rounded-lg border border-gray-200 dark:border-neutral-700 text-sm text-gray-700 dark:text-neutral-200">
                {copied === 'key' ? 'Copied' : 'Copy'}
              </button>
            </div>
          </div>
        </div>

        {/* Usage */}
        <div className="rounded-2xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-5 mb-4">
          <h2 className="text-base font-medium text-black dark:text-white mb-3">Use it (Postman / curl)</h2>
          <CodeBlock>{`curl -X POST ${'{BASE_URL}'}/api/v1/query \\
  -H "X-API-Key: ${key}" \\
  -H "Content-Type: application/json" \\
  -d '{"mode":"search","query":"best laptops 2026","options":{"synthesize":true}}'`}</CodeBlock>
          <button onClick={() => copy(`curl -X POST {BASE_URL}/api/v1/query -H "X-API-Key: ${key}" -H "Content-Type: application/json" -d '{"mode":"search","query":"best laptops 2026","options":{"synthesize":true}}'`, 'curl')}
            className="mt-2 text-xs text-blue-600 dark:text-blue-400">{copied === 'curl' ? 'Copied ✓' : 'Copy curl'}</button>
        </div>

        {/* Self-host */}
        <div className="rounded-2xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-5">
          <h2 className="text-base font-medium text-black dark:text-white mb-1">Prefer to self-host?</h2>
          <p className="text-xs text-gray-500 dark:text-neutral-400 mb-3">Run the open-source engine with your own keys — no quota, no Supabase needed.</p>
          <CodeBlock>{`git clone <repo> && cd backend
cp .env.example .env   # set SERPAPI_KEY, GEMINI_API_KEY, and your own API_KEY
docker compose up`}</CodeBlock>
        </div>
      </div>
    </div>
  );
};

export default ApiKeys;
