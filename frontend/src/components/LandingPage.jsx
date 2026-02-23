import React, { useRef, useEffect, useState } from 'react';
import ToolSelection from './ToolSelection';
import ToolDescriptionCards from './ToolDescriptionCards';
import DottedGrid from './UI_components/DottedGrid';

const LandingPage = ({ 
  query, 
  setQuery, 
  handleSearch, 
  handleKeyPress, 
  selectedTool, 
  setSelectedTool, 
  userName 
}) => {
  const textareaRef = useRef(null);
  const [currentDateTime, setCurrentDateTime] = useState(new Date());
  const [showAboutModal, setShowAboutModal] = useState(false);
  const [placeholderText, setPlaceholderText] = useState('');
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') === 'dark' ||
        (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
    }
    return false;
  });

  // Sync dark class on <html> and persist
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDark]);

  // Typewriter effect for placeholder
  useEffect(() => {
    const phrases = [
      'What do you want to know?',
      'Search the web for anything...',
      'Scrape data from any website...',
      'Analyze content from multiple sources...',
      'Find the latest news on any topic...',
    ];
    let phraseIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    let timeoutId;

    const tick = () => {
      const currentPhrase = phrases[phraseIndex];

      if (!isDeleting) {
        charIndex++;
        setPlaceholderText(currentPhrase.slice(0, charIndex));

        if (charIndex === currentPhrase.length) {
          // Pause at full phrase, then start deleting
          timeoutId = setTimeout(() => { isDeleting = true; tick(); }, 2000);
          return;
        }
        timeoutId = setTimeout(tick, 60);
      } else {
        charIndex--;
        setPlaceholderText(currentPhrase.slice(0, charIndex));

        if (charIndex === 0) {
          isDeleting = false;
          phraseIndex = (phraseIndex + 1) % phrases.length;
          timeoutId = setTimeout(tick, 400);
          return;
        }
        timeoutId = setTimeout(tick, 30);
      }
    };

    tick();
    return () => clearTimeout(timeoutId);
  }, []);

  // Auto-resize textarea as content changes
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [query]);

  // Update date and time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentDateTime(new Date());
    }, 1000);
    
    return () => clearInterval(timer);
  }, []);

  // Format the date and time
  const formatDate = (date) => {
    const options = { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    };
    return date.toLocaleDateString('en-US', options);
  };

  return (
    <div className="relative flex-1 flex flex-col items-center h-screen bg-gray-200 dark:bg-neutral-800 gap-[1px] overflow-hidden">
      {/* Animated glow overlay */}
      <div
        className="absolute left-0 top-0 w-[20%] h-[100%] pointer-events-none z-0 will-change-transform"
        style={{
          background: 'radial-gradient(ellipse at center, var(--color-glow-center) 0%, var(--color-glow-mid) 30%, var(--color-glow-edge) 55%, transparent 75%)',
          animation: 'glowTravel 6s ease-in-out infinite',
          filter: 'blur(100px)',
        }}
      />
      {/* first section — stretches on zoom */}
      <div className="relative z-10 flex w-full flex-1 min-h-[3rem] gap-[1px]">
        <div className="flex-1 bg-white dark:bg-black rounded-t-lg" />
        <div className="w-full max-w-4xl shrink-0 bg-white dark:bg-black rounded-t-lg flex items-center justify-between px-5"></div>
        <div className="flex-1 bg-white dark:bg-black rounded-t-lg" />
      </div>

      {/* navbar — fixed height, does not stretch */}
      <div className="relative z-10 flex w-full h-14 shrink-0 flex-nowrap gap-[1px]">
        <div className="flex-1 bg-white dark:bg-black rounded-lg" />
        <div className="w-full max-w-4xl shrink-0 bg-white dark:bg-black rounded-lg flex items-center justify-between px-5">
          {/* Left — Logo / Brand */}
          <div className="flex items-center">
            {/* Icon placeholder — replace with actual logo */}
            <div className="w-5 h-5 rounded-lg bg-white dark:bg-black flex items-center justify-center">
              <span className="material-icons text-black dark:text-white text-[22px] leading-none">search</span>
            </div>
            <span className="text-md font-semibold text-gray-800 dark:text-gray-100 tracking-tight">GPT</span>
          </div>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Right — Social links + theme toggle */}
          <div className="flex items-center gap-5">
            {/* GitHub */}
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-700 hover:text-black dark:text-gray-300 dark:hover:text-white transition-colors hover:scale-110"
              title="GitHub"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
              </svg>
            </a>

            {/* X (Twitter) */}
            <a
              href="https://x.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-700 hover:text-black dark:text-gray-300 dark:hover:text-white transition-colors hover:scale-110"
              title="X (Twitter)"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
            </a>

            {/* LinkedIn */}
            <a
              href="https://linkedin.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-700 hover:text-black dark:text-gray-300 dark:hover:text-white transition-colors hover:scale-110"
              title="LinkedIn"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
              </svg>
            </a>

            {/* Divider */}
            <div className="w-px h-6 bg-gray-800 dark:bg-neutral-200" />

            {/* Theme toggle */}
            <button
              type="button"
              className="flex items-center justify-center w-4 h-4 text-gray-700 hover:text-black dark:text-gray-300 dark:hover:text-white transition-colors hover:scale-110"
              title="Toggle theme"
              onClick={() => setIsDark(!isDark)}
            >
              <span className="material-icons text-[21px] leading-none">{isDark ? 'light_mode' : 'dark_mode'}</span>
            </button>
          </div>
        </div>
        <div className="flex-1  bg-white dark:bg-black rounded-lg" />
      </div>

      {/* middle section */}
      <div className="relative z-10 flex w-full h-12 shrink-0 flex-nowrap gap-[1px]">
        <div className="hidden sm:block flex-1 bg-white dark:bg-black rounded-lg shrink-0" />
        <div className="w-24 hidden sm:block shrink-0 bg-white dark:bg-black rounded-lg" />
        <div className="w-8 sm:w-16 bg-white shrink-0  dark:bg-black rounded-lg" />
        <div className="w-full max-w-4xl bg-white dark:bg-black rounded-lg">
        </div>
        <div className="w-8 sm:w-16 bg-white shrink-0  dark:bg-black rounded-lg" />
        <div className="w-24 hidden sm:block shrink-0 bg-white dark:bg-black rounded-lg" />
        <div className="hidden sm:block flex-1 bg-white dark:bg-black rounded-lg shrink-0" />
      </div>

      {/* content section */}
      <div className="relative z-10 w-full flex flex-nowrap items-stretch justify-center text-center gap-[1px]">
        {/* layer1 */}
        <div className="flex-1 min-w-0 flex flex-col gap-[1px] shrink-0 self-stretch min-h-0">
          <div className="flex-1 min-h-0 bg-white dark:bg-black rounded-lg" />
          <div className="h-24 shrink-0 bg-white dark:bg-black rounded-lg" />
          <div className="flex-1 min-h-0 bg-white dark:bg-black rounded-lg" />
        </div>
        {/* layer2 */}
        <div className="hidden sm:flex sm:w-24 shrink-0 self-stretch min-h-0 flex-col gap-[1px]">
          <div className="flex-1 min-h-0 bg-white dark:bg-black rounded-lg" />
          <div className="h-24 shrink-0 bg-white dark:bg-black rounded-lg" />
          <div className="flex-1 min-h-0 bg-white dark:bg-black rounded-lg" />
        </div>

        {/* layer3 */}
        <div className="w-8 sm:w-16 bg-green-500 shrink-0 bg-white dark:bg-black rounded-lg"></div>

        <div className="w-full relative max-w-4xl rounded-lg p-6 sm:p-8 overflow-hidden">
          <DottedGrid className="absolute inset-0 z-0 rounded-lg" />
          {/* Greeting */}
          <div className="relative z-10 text-center mb-8 sm:mb-12">
            <h1 className="text-3xl sm:text-4xl font-semibold mb-2 text-black dark:text-white">
              Welcome to {userName}
            </h1>
            <p className="text-lg text-gray-500 dark:text-neutral-400 ">Get Actionable Answers from the Open Web</p>
          </div>
          
          {/* Search Input */}
          <div className="relative z-10 w-full bg-white/10 dark:bg-white/5 backdrop-blur-md border border-gray-200 dark:border-neutral-800 rounded-xl p-4 shadow-lg dark:shadow-neutral-900">
            <form onSubmit={handleSearch}>
              <textarea
                ref={textareaRef}
                placeholder={placeholderText}
                className="w-full h-auto bg-transparent text-sm sm:text-md text-gray-800 dark:text-gray-100 placeholder-gray-500 dark:placeholder-neutral-400  outline-none resize-none overflow-hidden min-h-[40px] max-h-[100px]"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyPress}
                rows={1}
              />
              
              {/* Tool Selection with Send button inline */}
              <div className="mt-4 border-t border-gray-200 dark:border-neutral-800 pt-4">
                <ToolSelection 
                  selectedTool={selectedTool} 
                  setSelectedTool={setSelectedTool} 
                  includeSubmitButton={true}
                  dropdownDirection="down"
                />
              </div>
            </form>
          </div>
        </div>
        {/* layer3 */}
        <div className="w-8 sm:w-16 bg-green-500 shrink-0 bg-white dark:bg-black rounded-lg">
     
        </div>
        {/* layer2 */}
        <div className="hidden sm:flex sm:w-24 shrink-0 self-stretch min-h-0 flex-col gap-[1px]">
          <div className="flex-1 min-h-0 bg-white dark:bg-black rounded-lg" />
          <div className="h-24 shrink-0 bg-white dark:bg-black rounded-lg" />
          <div className="flex-1 min-h-0 bg-white dark:bg-black rounded-lg" />
        </div>
        {/* layer1 */}
        <div className="hidden sm:flex sm:flex-1 flex flex-col gap-[1px] shrink-0 self-stretch min-h-0">
          <div className="flex-1 min-h-0 bg-white dark:bg-black rounded-lg" />
          <div className="h-24 shrink-0 bg-white dark:bg-black rounded-lg" />
          <div className="flex-1 min-h-0 bg-white dark:bg-black rounded-lg" />
        </div>
      </div>

      {/* middle section */}
      <div className="relative z-10 flex w-full h-12 shrink-0 flex-nowrap gap-[1px]">
        <div className="flex-1 hidden sm:block bg-white dark:bg-black rounded-lg shrink-0" />
        <div className="w-24 hidden sm:block shrink-0 bg-white dark:bg-black rounded-lg" />
        <div className="w-8 sm:w-16 bg-white shrink-0  dark:bg-black rounded-lg" />
        <div className="w-full max-w-4xl bg-white dark:bg-black rounded-lg">
     
        </div>
        <div className="w-8 sm:w-16 bg-white shrink-0  dark:bg-black rounded-lg" />
        <div className="w-24 hidden sm:block shrink-0 bg-white dark:bg-black rounded-lg" />
        <div className="flex-1 hidden sm:block bg-white dark:bg-black rounded-lg shrink-0" />
      </div>

      {/* footer — fixed height, does not stretch */}
      <div className="relative z-10 flex w-full h-28 shrink-0 flex-nowrap gap-[1px]">
        <div className="flex-1  shrink-0 bg-white dark:bg-black rounded-lg" />
        <div className="w-full max-w-4xl shrink-0 bg-white dark:bg-black rounded-lg flex flex-col items-center justify-center py-4 gap-1">
          {/* About link */}
          <button
            type="button"
            onClick={() => setShowAboutModal(true)}
            className="text-sm font-medium tracking-wide text-gray-700 dark:text-neutral-300  hover:text-black dark:hover:text-gray-200 transition-colors"
          >
            About SearchGPT
          </button>

          {/* Server time */}
          <p className="text-[12px] text-gray-600 dark:text-neutral-400  tracking-wide">
            {formatDate(currentDateTime)}
          </p>

          {/* Copyright / trademark */}
          <p className="text-[12px] text-gray-600 dark:text-neutral-400  tracking-wider">
            &copy; {new Date().getFullYear()} SearchGPT - All rights reserved.
          </p>
        </div>
        <div className="flex-1  shrink-0 bg-white dark:bg-black rounded-lg" />
      </div>

      {/* last section — stretches on zoom */}
      <div className="relative z-10 flex w-full flex-1 min-h-[3rem] gap-[1px]">
        <div className="flex-1 bg-white dark:bg-black rounded-t-lg" />
        <div className="w-full max-w-4xl shrink-0 bg-white dark:bg-black rounded-t-lg flex items-center justify-between px-5"></div>
        <div className="flex-1 bg-white dark:bg-black rounded-t-lg" />
      </div>

      {/* About Modal */}
      {showAboutModal && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setShowAboutModal(false)}
        >
          <div
            className="bg-white dark:bg-black rounded-2xl p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto shadow-xl border border-gray-100 dark:border-neutral-800"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-black dark:text-white tracking-tight">About SearchGPT</h2>
              <button
                onClick={() => setShowAboutModal(false)}
                className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
              >
                <span className="material-icons text-xl">close</span>
              </button>
            </div>

            <div className="text-sm text-gray-600 dark:text-neutral-400 leading-relaxed space-y-5">
              <p>
                SearchGPT is a free, open-source web research agent that helps you find, extract, analyze, and synthesize information from the web - powered by playwright and gemini.
              </p>

              <div>
                <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2">Features</h3>
                <ul className="list-disc pl-5 space-y-1.5 text-gray-500 dark:text-neutral-400">
                  <li><span className="text-gray-700 dark:text-gray-300 font-medium">Web Search</span> — Search the web and retrieve relevant results</li>
                  <li><span className="text-gray-700 dark:text-gray-300 font-medium">Web Scraper</span> — Extract data from websites for further analysis</li>
                  <li><span className="text-gray-700 dark:text-gray-300 font-medium">Content Analyzer</span> — Analyze content from multiple sources for comprehensive answers</li>
                  <li><span className="text-gray-700 dark:text-gray-300 font-medium">News Aggregator</span> — Find the latest news articles on any topic</li>
                </ul>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2">How to Use</h3>
                <ol className="list-decimal pl-5 space-y-1.5 text-gray-500 dark:text-neutral-400">
                  <li>Select a tool from the available options</li>
                  <li>Enter your search query in the input field</li>
                  <li>Press Enter or click Send to submit</li>
                  <li>View the results in the chat interface</li>
                </ol>
              </div>

              <div className="pt-3 border-t border-gray-100 dark:border-neutral-800 flex items-center justify-between">
                <p className="text-[11px] text-gray-300 dark:text-neutral-400">
                  &copy; {new Date().getFullYear()} SearchGPT . All rights reserved.
                </p>
                <p className="text-[11px] text-gray-300 dark:text-neutral-400">
                  Open Source - MIT License
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LandingPage; 