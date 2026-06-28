import React from 'react';

/**
 * Left-half graphic for the sign-in page: a dark dotted field with an animated "search radar"
 * (concentric pinging rings + a magnifier), floating web-node dots, and the SearchGPT brand.
 * Pure CSS/SVG animation — no deps.
 */
const NODES = [
  { top: '18%', left: '22%', d: '0s' },
  { top: '30%', left: '74%', d: '0.6s' },
  { top: '66%', left: '20%', d: '1.1s' },
  { top: '74%', left: '70%', d: '0.3s' },
  { top: '48%', left: '85%', d: '0.9s' },
  { top: '58%', left: '40%', d: '1.4s' },
];

const AnimatedSearchPanel = () => (
  <div className="relative h-full w-full overflow-hidden bg-neutral-950 text-white">
    <style>{`
      @keyframes sb-drift { from { background-position: 0 0; } to { background-position: 28px 28px; } }
      @keyframes sb-float { 0%,100% { transform: translateY(0); opacity:.7 } 50% { transform: translateY(-10px); opacity:1 } }
      @keyframes sb-ring { 0% { transform: scale(.4); opacity:.6 } 80% { opacity:0 } 100% { transform: scale(2.2); opacity:0 } }
      @keyframes sb-spin { to { transform: rotate(360deg); } }
    `}</style>

    {/* dotted field */}
    <div
      className="absolute inset-0 opacity-60"
      style={{
        backgroundImage: 'radial-gradient(rgba(255,255,255,0.18) 1px, transparent 1px)',
        backgroundSize: '28px 28px',
        animation: 'sb-drift 6s linear infinite',
      }}
    />
    {/* glow */}
    <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse at 50% 45%, rgba(59,130,246,0.25), transparent 60%)' }} />

    {/* floating web nodes */}
    {NODES.map((n, i) => (
      <div key={i} className="absolute" style={{ top: n.top, left: n.left, animation: `sb-float 3.6s ease-in-out ${n.d} infinite` }}>
        <div className="w-2 h-2 rounded-full bg-blue-400 shadow-[0_0_12px_2px_rgba(59,130,246,0.6)]" />
      </div>
    ))}

    {/* center radar + magnifier */}
    <div className="absolute inset-0 flex flex-col items-center justify-center">
      <div className="relative w-44 h-44 flex items-center justify-center">
        {[0, 1, 2].map((i) => (
          <span key={i} className="absolute w-44 h-44 rounded-full border border-blue-400/40"
            style={{ animation: `sb-ring 3s ease-out ${i * 1}s infinite` }} />
        ))}
        <div className="absolute w-44 h-44 rounded-full border border-dashed border-white/10" style={{ animation: 'sb-spin 24s linear infinite' }} />
        {/* magnifier */}
        <svg viewBox="0 0 24 24" className="w-16 h-16 text-white relative z-10" fill="none" stroke="currentColor" strokeWidth="1.6">
          <circle cx="11" cy="11" r="6.5" />
          <line x1="16" y1="16" x2="21" y2="21" strokeLinecap="round" />
        </svg>
      </div>

      <div className="mt-10 text-center px-8">
        <h2 className="text-2xl font-semibold tracking-tight">SearchGPT Agent</h2>
        <p className="mt-2 text-sm text-neutral-400 max-w-xs mx-auto">
          Search, scrape, and synthesize the web through one API. Build with your keys.
        </p>
      </div>
    </div>
  </div>
);

export default AnimatedSearchPanel;
