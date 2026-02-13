import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { UI_CONFIG } from '../config';

const TOOL_TIPS = UI_CONFIG.TOOL_DESCRIPTIONS;

const Tooltip = ({ text, children }) => {
  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState({ top: 0, left: 0 });
  const triggerRef = useRef(null);

  const updatePosition = () => {
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      setCoords({
        top: rect.top - 8,
        left: rect.left + rect.width / 2,
      });
    }
  };

  const show = () => {
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      setCoords({ top: rect.top - 8, left: rect.left + rect.width / 2 });
    }
    setVisible(true);
  };
  const hide = () => setVisible(false);

  useEffect(() => {
    if (!visible) return;
    const onScrollOrResize = () => updatePosition();
    window.addEventListener('scroll', onScrollOrResize, true);
    window.addEventListener('resize', onScrollOrResize);
    return () => {
      window.removeEventListener('scroll', onScrollOrResize, true);
      window.removeEventListener('resize', onScrollOrResize);
    };
  }, [visible]);

  const tooltipEl = visible && (
    <span
      role="tooltip"
      className="fixed px-3 py-2 text-xs font-medium text-white bg-gray-800 dark:bg-neutral-900 rounded-lg shadow-lg opacity-100 z-[99999] pointer-events-none text-center w-[320px] -translate-x-1/2"
      style={{
        top: coords.top,
        left: coords.left,
        transform: 'translate(-50%, -100%)',
      }}
    >
      <span
        className="absolute left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-800 dark:border-t-neutral-900"
        style={{ top: '100%', marginTop: '-1px' }}
      />
      {text}
    </span>
  );

  return (
    <>
      <div
        ref={triggerRef}
        className="inline-block"
        onMouseEnter={show}
        onMouseLeave={hide}
      >
        {children}
      </div>
      {typeof document !== 'undefined' && createPortal(tooltipEl, document.body)}
    </>
  );
};

const ToolSelection = ({ selectedTool, setSelectedTool, includeSubmitButton = false, isDisabled = false }) => (
  <div className="flex flex-wrap gap-2 items-center">
    <Tooltip text={TOOL_TIPS.search}>
      <button 
        type="button"
        className={`flex items-center text-sm px-4 py-1 rounded-full border transition-colors ${
          selectedTool === 'search' 
            ? 'bg-zinc-200 text-black border-gray-900 dark:bg-zinc-800 dark:text-neutral-200 dark:border-neutral-400' 
            : 'text-gray-600 border-gray-300 hover:bg-gray-100 dark:text-neutral-400 dark:border-neutral-700 dark:hover:bg-neutral-900'
        } ${isDisabled ? 'opacity-70 cursor-not-allowed' : ''}`}
        onClick={() => !isDisabled && setSelectedTool('search')}
        disabled={isDisabled}
      >
        <span className="material-icons text-sm mr-2">search</span> Web Search
      </button>
    </Tooltip>
    
    <Tooltip text={TOOL_TIPS.scraper}>
      <button 
        type="button"
        className={`flex items-center text-sm px-4 py-1 rounded-full border transition-colors ${
          selectedTool === 'scraper' 
            ? 'bg-zinc-200 text-black border-gray-900 dark:bg-zinc-800 dark:text-neutral-200 dark:border-neutral-400' 
            : 'text-gray-600 border-gray-300 hover:bg-gray-100 dark:text-neutral-400 dark:border-neutral-700 dark:hover:bg-neutral-900'
        } ${isDisabled ? 'opacity-70 cursor-not-allowed' : ''}`}
        onClick={() => !isDisabled && setSelectedTool('scraper')}
        disabled={isDisabled}
      >
        <span className="material-icons text-sm mr-2">code</span> Web Scraper
      </button>
    </Tooltip>
    
    <Tooltip text={TOOL_TIPS.analyzer}>
      <button 
        type="button"
        className={`flex items-center text-sm px-4 py-1 rounded-full border transition-colors ${
          selectedTool === 'analyzer' 
            ? 'bg-zinc-200 text-black border-gray-900 dark:bg-zinc-800 dark:text-neutral-200 dark:border-neutral-400' 
            : 'text-gray-600 border-gray-300 hover:bg-gray-100 dark:text-neutral-400 dark:border-neutral-700 dark:hover:bg-neutral-900'
        } ${isDisabled ? 'opacity-70 cursor-not-allowed' : ''}`}
        onClick={() => !isDisabled && setSelectedTool('analyzer')}
        disabled={isDisabled}
      >
        <span className="material-icons text-sm mr-2">analytics</span> Content Analyzer
      </button>
    </Tooltip>
    
    <Tooltip text={TOOL_TIPS.news}>
      <button 
        type="button"
        className={`flex items-center text-sm px-4 py-1 rounded-full border transition-colors ${
          selectedTool === 'news' 
            ? 'bg-zinc-200 text-black border-gray-900 dark:bg-zinc-800 dark:text-neutral-200 dark:border-neutral-400' 
            : 'text-gray-600 border-gray-300 hover:bg-gray-100 dark:text-neutral-400 dark:border-neutral-700 dark:hover:bg-neutral-900'
        } ${isDisabled ? 'opacity-70 cursor-not-allowed' : ''}`}
        onClick={() => !isDisabled && setSelectedTool('news')}
        disabled={isDisabled}
      >
        <span className="material-icons text-sm mr-2">newspaper</span> News Aggregator
      </button>
    </Tooltip>
    
    {includeSubmitButton && (
      <button 
        type="submit"
        className={`ml-auto flex items-center text-sm px-4 py-1 rounded-full border transition-colors ${
          isDisabled 
            ? 'opacity-70 cursor-not-allowed bg-gray-100 border-gray-300 text-gray-400 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-600' 
            : 'bg-gray-800 text-white border-gray-900 hover:bg-gray-800 dark:bg-neutral-100 dark:text-gray-900 dark:border-white dark:hover:bg-gray-200'
        }`}
        disabled={isDisabled}
      >
        <span className="material-icons text-sm mr-2">send</span> Send
      </button>
    )}
  </div>
);

export default ToolSelection; 