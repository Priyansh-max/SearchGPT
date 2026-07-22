import React, { useState, useEffect } from 'react';

/**
 * Left-half graphic for the sign-in page: an animated aurora mesh-gradient on near-black,
 * a faint grid, the SearchGPT brand, and a tagline whose verb cycles
 * (search → scrape → analyze → synthesize). Premium / Linear-Vercel style. Pure CSS + one timer.
 */
const PHRASES = [
  { verb: 'search', tail: 'the web' },
  { verb: 'scrape', tail: 'any page' },
  { verb: 'analyze', tail: 'sources' },
  { verb: 'synthesize', tail: 'answers' },
];

const AnimatedSearchPanel = () => {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((p) => (p + 1) % PHRASES.length), 2400);
    return () => clearInterval(t);
  }, []);
  const phrase = PHRASES[i];

  return (
    <div className="relative h-full w-full overflow-hidden" style={{ background: '#07070b' }}>
      <style>{`
        @keyframes sb-blob1 { 0%,100% { transform: translate(-10%,-10%) scale(1); } 50% { transform: translate(10%,8%) scale(1.25); } }
        @keyframes sb-blob2 { 0%,100% { transform: translate(8%,12%) scale(1.1); } 50% { transform: translate(-8%,-6%) scale(0.9); } }
        @keyframes sb-blob3 { 0%,100% { transform: translate(0%,6%) scale(1); } 50% { transform: translate(6%,-10%) scale(1.2); } }
        @keyframes sb-word { 0% { opacity:0; transform: translateY(8px); } 12%,88% { opacity:1; transform: translateY(0); } 100% { opacity:0; transform: translateY(-8px); } }
      `}</style>

      {/* aurora blobs */}
      <div className="absolute -top-1/4 -left-1/4 w-[70%] h-[70%] rounded-full blur-[90px] opacity-70"
        style={{ background: 'radial-gradient(circle, #2563eb 0%, transparent 70%)', animation: 'sb-blob1 14s ease-in-out infinite' }} />
      <div className="absolute top-1/3 -right-1/4 w-[65%] h-[65%] rounded-full blur-[90px] opacity-60"
        style={{ background: 'radial-gradient(circle, #7c3aed 0%, transparent 70%)', animation: 'sb-blob2 18s ease-in-out infinite' }} />
      <div className="absolute -bottom-1/4 left-1/4 w-[60%] h-[60%] rounded-full blur-[90px] opacity-50"
        style={{ background: 'radial-gradient(circle, #06b6d4 0%, transparent 70%)', animation: 'sb-blob3 16s ease-in-out infinite' }} />

      {/* faint grid */}
      <div className="absolute inset-0 opacity-[0.12]"
        style={{ backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)', backgroundSize: '46px 46px' }} />
      {/* vignette for text legibility */}
      <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse at center, transparent 30%, rgba(0,0,0,0.55) 100%)' }} />

      {/* brand + tagline */}
      <div className="relative h-full flex flex-col items-center justify-center text-center px-10 text-white">
        <div className="flex items-center gap-2 mb-8">
          <svg viewBox="0 0 24 24" className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth="1.8">
            <circle cx="11" cy="11" r="6.5" /><line x1="16" y1="16" x2="21" y2="21" strokeLinecap="round" />
          </svg>
          <span className="text-xl font-semibold tracking-tight" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>SearchGPT Agent</span>
        </div>

        <h2 className="text-3xl font-semibold tracking-tight leading-tight" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
          One API to
        </h2>
        <div className="h-10 mt-1 overflow-hidden">
          <span key={i} className="inline-flex items-baseline gap-2 text-3xl font-semibold tracking-tight"
            style={{ fontFamily: "'Space Grotesk', sans-serif", animation: 'sb-word 2.4s ease-in-out' }}>
            <span style={{ background: 'linear-gradient(90deg,#60a5fa,#a78bfa,#22d3ee)', WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' }}>
              {phrase.verb}
            </span>
            <span className="text-white/90">{phrase.tail}</span>
          </span>
        </div>

        <p className="mt-8 text-sm text-white/50 max-w-xs">
          Build with your keys. Free monthly credits, one endpoint, four modes.
        </p>
      </div>
    </div>
  );
};

export default AnimatedSearchPanel;
