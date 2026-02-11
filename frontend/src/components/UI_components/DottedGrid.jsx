import { useRef, useEffect } from 'react';

const DottedGrid = ({ className = '' }) => {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const activeDots = useRef([]); // dots currently animating bigger

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const spacing = 20;
    const baseSize = 1.2; // all dots same size
    const maxGrowSize = 1.5; // how big a dot can grow
    const growDuration = 2000; // ms for a dot to grow and shrink back (full cycle)

    // Detect dark mode
    const isDarkMode = () => {
      return document.documentElement.classList.contains('dark');
    };

    // Periodically pick random dots to "pop"
    const popInterval = setInterval(() => {
      const rect = canvas.getBoundingClientRect();
      const cols = Math.ceil(rect.width / spacing) + 1;
      const rows = Math.ceil(rect.height / spacing) + 1;

      // Pick 2-5 random dots each interval
      const count = 40 + Math.floor(Math.random() * 45);
      for (let i = 0; i < count; i++) {
        const col = Math.floor(Math.random() * cols);
        const row = Math.floor(Math.random() * rows);
        activeDots.current.push({
          col,
          row,
          startTime: Date.now()
        });
      }
    }, 400);

    const draw = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;

      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const w = rect.width;
      const h = rect.height;

      ctx.clearRect(0, 0, w, h);

      const darkMode = isDarkMode();
      
      // Background: white for light mode, black for dark mode
      ctx.fillStyle = darkMode ? '#000000' : '#ffffff';
      ctx.fillRect(0, 0, w, h);

      const cols = Math.ceil(w / spacing) + 1;
      const rows = Math.ceil(h / spacing) + 1;
      const cx = w / 2;
      const cy = h / 2;
      const maxDist = Math.sqrt(cx * cx + cy * cy);
      const now = Date.now();

      // Build a lookup of active dot sizes for fast access
      const activeMap = new Map();
      activeDots.current = activeDots.current.filter(dot => {
        const elapsed = now - dot.startTime;
        if (elapsed > growDuration) return false; // expired

        // Smooth ease: sine curve 0 -> 1 -> 0
        const progress = elapsed / growDuration;
        const scale = Math.sin(progress * Math.PI); // 0 at start, 1 at midpoint, 0 at end
        const smoothScale = scale * scale; // ease-in-out feel

        const key = `${dot.col},${dot.row}`;
        const existing = activeMap.get(key) || 0;
        activeMap.set(key, Math.max(existing, smoothScale));
        return true;
      });

      for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
          const x = col * spacing;
          const y = row * spacing;

          // Distance from center for edge fade
          const dx = x - cx;
          const dy = y - cy;
          const dist = Math.sqrt(dx * dx + dy * dy);

          const fadeFactor = 1 - Math.pow(dist / maxDist, 1.5);
          if (fadeFactor <= 0) continue;

          // Check if this dot is actively growing
          const key = `${col},${row}`;
          const growFactor = activeMap.get(key) || 0;

          // Size: base + extra growth
          const size = baseSize + growFactor * (maxGrowSize - baseSize);

          // Opacity: base fade + brighter when growing
          const alpha = (0.2 + growFactor * 0.4) * fadeFactor;

          ctx.beginPath();
          ctx.arc(x, y, size, 0, Math.PI * 2);
          
          // Dot color: dark gray/black for light mode, white for dark mode
          if (darkMode) {
            ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
          } else {
            // Use dark gray/black dots for light mode
            ctx.fillStyle = `rgba(0, 0, 0, ${alpha})`; // Darker dots, slightly lower opacity
          }
          ctx.fill();
        }
      }

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();

    // Watch for theme changes
    const observer = new MutationObserver(draw);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class']
    });

    return () => {
      clearInterval(popInterval);
      observer.disconnect();
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 z-0 w-full h-full ${className}`}
      style={{ display: 'block' }}
    />
  );
};

export default DottedGrid;
