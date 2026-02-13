import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { UI_CONFIG } from '../config';

const TOOL_TIPS = UI_CONFIG.TOOL_DESCRIPTIONS;

const TOOLS = [
  { id: 'search', label: 'Web Search', icon: 'search', description: TOOL_TIPS.search },
  { id: 'scraper', label: 'Web Scraper', icon: 'code', description: TOOL_TIPS.scraper },
  { id: 'analyzer', label: 'Content Analyzer', icon: 'analytics', description: TOOL_TIPS.analyzer },
  { id: 'news', label: 'News Aggregator', icon: 'newspaper', description: TOOL_TIPS.news },
];

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

const ToolSelection = ({ selectedTool, setSelectedTool, includeSubmitButton = false, isDisabled = false, dropdownDirection = 'down' }) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isDropdownOpen]);

  const selectedToolData = TOOLS.find(tool => tool.id === selectedTool) || TOOLS[0];

  const handleToolSelect = (toolId) => {
    if (!isDisabled) {
      setSelectedTool(toolId);
      setIsDropdownOpen(false);
    }
  };

  return (
    <div className="flex flex-wrap gap-2 items-center relative md:flex-nowrap" ref={dropdownRef}>
      {/* Mobile Layout */}
      <div className="md:hidden flex justify-between items-center w-full gap-2">
        {/* Mobile Dropdown */}
        <div className="relative">
          <button
            type="button"
            onClick={() => !isDisabled && setIsDropdownOpen(!isDropdownOpen)}
            disabled={isDisabled}
            className={`flex items-center text-sm px-4 py-2 rounded-lg border transition-colors shrink-0 ${
              isDisabled
                ? 'opacity-70 cursor-not-allowed bg-gray-100 border-gray-300 text-gray-400 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-600'
                : 'bg-white dark:bg-neutral-900 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-neutral-700 hover:bg-gray-50 dark:hover:bg-neutral-800'
            }`}
          >
            <div className="flex items-center">
              <span className="material-icons text-sm mr-2">{selectedToolData.icon}</span>
              {selectedToolData.label}
            </div>
            <span className="material-icons text-sm ml-2">
              {dropdownDirection === 'down' ? 'arrow_drop_down' : 'arrow_drop_up'}
            </span>
          </button>

          {isDropdownOpen && (
            <div
              className={`absolute left-0 z-50 mt-1 bg-white dark:bg-neutral-900 border border-gray-300 dark:border-neutral-700 rounded-lg shadow-lg overflow-hidden min-w-[200px] ${
                dropdownDirection === 'down' ? 'top-full' : 'bottom-full mb-1'
              }`}
            >
              {TOOLS.map((tool) => (
                <button
                  key={tool.id}
                  type="button"
                  onClick={() => handleToolSelect(tool.id)}
                  className={`w-full flex items-center text-sm px-4 py-2 text-left transition-colors ${
                    selectedTool === tool.id
                      ? 'bg-zinc-200 dark:bg-zinc-800 text-black dark:text-neutral-200'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-neutral-800'
                  } ${isDisabled ? 'opacity-70 cursor-not-allowed' : ''}`}
                  disabled={isDisabled}
                >
                  <span className="material-icons text-sm mr-2">{tool.icon}</span>
                  {tool.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Mobile Send Button */}
        {includeSubmitButton && (
          <button
            type="submit"
            className={`flex items-center justify-center text-sm px-4 py-1 rounded-full border transition-colors shrink-0 ${
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

      {/* Desktop Buttons */}
      <div className="hidden md:flex flex-wrap gap-2 items-center">
        {TOOLS.map((tool) => (
          <Tooltip key={tool.id} text={tool.description}>
            <button
              type="button"
              className={`flex items-center text-sm px-4 py-1 rounded-full border transition-colors ${
                selectedTool === tool.id
                  ? 'bg-zinc-200 text-black border-gray-900 dark:bg-zinc-800 dark:text-neutral-200 dark:border-neutral-400'
                  : 'text-gray-600 border-gray-300 hover:bg-gray-100 dark:text-neutral-400 dark:border-neutral-700 dark:hover:bg-neutral-900'
              } ${isDisabled ? 'opacity-70 cursor-not-allowed' : ''}`}
              onClick={() => !isDisabled && setSelectedTool(tool.id)}
              disabled={isDisabled}
            >
              <span className="material-icons text-sm mr-2">{tool.icon}</span>
              {tool.label}
            </button>
          </Tooltip>
        ))}
      </div>

      {/* Desktop Send Button */}
      {includeSubmitButton && (
        <button
          type="submit"
          className={`hidden md:flex md:ml-auto items-center justify-center text-sm px-4 py-1 rounded-full border transition-colors shrink-0 ${
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
};

export default ToolSelection; 