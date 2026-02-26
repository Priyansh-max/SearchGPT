import React, { useState, useEffect, useRef } from 'react';

/**
 * Displays text with a fade-in and typewriter effect; each letter appears
 * with a blur-to-sharp animation. Use for welcome/empty state on new chat or reload.
 */
const TypewriterBlurFade = ({
  text = 'How can I help you today?',
  charDelayMs = 60,
  startDelayMs = 200,
  fadeDurationMs = 400,
  className = '',
}) => {
  const [visibleLength, setVisibleLength] = useState(0);
  const [fadeDone, setFadeDone] = useState(false);
  const mounted = useRef(true);

  // Initial fade-in of the container
  useEffect(() => {
    mounted.current = true;
    const t = setTimeout(() => {
      if (mounted.current) setFadeDone(true);
    }, startDelayMs);
    return () => {
      mounted.current = false;
      clearTimeout(t);
    };
  }, [startDelayMs]);

  // Typewriter: reveal one character at a time after fade has started
  useEffect(() => {
    if (!fadeDone || visibleLength >= text.length) return;

    const t = setTimeout(() => {
      if (mounted.current) setVisibleLength((n) => Math.min(n + 1, text.length));
    }, charDelayMs);

    return () => clearTimeout(t);
  }, [fadeDone, visibleLength, text.length, charDelayMs]);

  return (
    <div
      className={`flex items-center justify-center min-h-[120px] ${className}`}
      style={{
        opacity: fadeDone ? 1 : 0,
        transition: `opacity ${fadeDurationMs}ms ease-out`,
      }}
    >
      <p className="text-2xl sm:text-2xl text-center text-neutral-500 dark:text-neutral-400 font-medium tracking-tight">
        {text.slice(0, visibleLength).split('').map((char, i) => (
          <span key={i} className="typewriter-char">
            {char === ' ' ? '\u00A0' : char}
          </span>
        ))}
      </p>
    </div>
  );
};

export default TypewriterBlurFade;
