import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const FONTS = [
  { name: 'Geist', stack: "'Geist', sans-serif", note: "Vercel's font — clean, premium dev-tool" },
  { name: 'Space Grotesk', stack: "'Space Grotesk', sans-serif", note: 'Geometric, techy, distinctive' },
  { name: 'Inter', stack: "'Inter', sans-serif", note: 'Clean modern standard (current)' },
  { name: 'Satoshi', stack: "'Satoshi', sans-serif", note: 'Stylish geometric (Fontshare)' },
];

const Sample = ({ font }) => (
  <div className="rounded-2xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6" style={{ fontFamily: font.stack }}>
    <div className="flex items-baseline justify-between mb-4">
      <h2 className="text-xl font-semibold text-black dark:text-white">{font.name}</h2>
      <span className="text-xs text-gray-400" style={{ fontFamily: 'Inter, sans-serif' }}>{font.note}</span>
    </div>
    <h1 className="text-3xl font-semibold text-black dark:text-white tracking-tight">Unlock the Web's Intelligence Instantly</h1>
    <p className="text-sm text-gray-500 dark:text-neutral-400 mt-2">
      Search, scrape, and synthesize the web through one API. Build with your keys — 1,234 credits left this month.
    </p>
    <div className="flex items-center gap-3 mt-5">
      <button className="px-4 py-2 rounded-lg bg-black dark:bg-white text-white dark:text-black text-sm font-medium">Create API key</button>
      <span className="text-sm font-medium text-gray-700 dark:text-neutral-200">Developers</span>
      <span className="text-2xl font-semibold text-black dark:text-white tabular-nums">8,420</span>
    </div>
    <p className="mt-4 text-xs text-gray-500" style={{ fontFamily: "'Geist Mono', monospace" }}>
      POST /api/v1/query · 0123456789 · search scrape analyze news
    </p>
  </div>
);

const FontPreview = () => {
  const navigate = useNavigate();
  const [dark, setDark] = useState(document.documentElement.classList.contains('dark'));
  const toggle = () => { const d = !dark; document.documentElement.classList.toggle('dark', d); setDark(d); };

  return (
    <div className="min-h-screen bg-neutral-100 dark:bg-black p-6">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6" style={{ fontFamily: 'Inter, sans-serif' }}>
          <button onClick={() => navigate('/')} className="text-sm text-gray-500 dark:text-neutral-400 hover:text-black dark:hover:text-white">← Home</button>
          <h1 className="text-base font-medium text-black dark:text-white">Font preview — pick one</h1>
          <button onClick={toggle} className="text-xs text-gray-500 dark:text-neutral-400">{dark ? 'Light' : 'Dark'}</button>
        </div>
        <div className="space-y-4">
          {FONTS.map((f) => <Sample key={f.name} font={f} />)}
        </div>
        <p className="text-center text-xs text-gray-400 mt-6" style={{ fontFamily: 'Inter, sans-serif' }}>
          Tell me the name and I'll apply it site-wide.
        </p>
      </div>
    </div>
  );
};

export default FontPreview;
