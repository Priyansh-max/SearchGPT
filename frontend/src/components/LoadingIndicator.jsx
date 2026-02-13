import React, { useState, useEffect } from 'react';

const LoadingIndicator = ({ startTime, message = "Searching the web" }) => {
  const [elapsedTime, setElapsedTime] = useState(0);
  
  useEffect(() => {
    const timer = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      setElapsedTime(elapsed);
    }, 1000);
    
    return () => clearInterval(timer);
  }, [startTime]);
  
  // Format elapsed time as mm:ss
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  return (
    <div className="flex w-full mb-4 justify-start">
      <div className="relative rounded-lg rounded-tl-none p-4 max-w-[80%]">
        {/* Content */}
        <div className="relative flex items-center">
          <span 
            className="mr-2 text-sm font-medium text-shimmer-light dark:text-shimmer-dark"
            style={{
              backgroundSize: '200% 100%',
              animation: 'shimmer 2s infinite',
              WebkitBackgroundClip: 'text',
              backgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            {message}
          </span>
          <div className="flex space-x-1">
            <div className="w-1 h-1 rounded-full bg-gray-600 dark:bg-neutral-600 animate-bounce"></div>
            <div className="w-1 h-1 rounded-full bg-gray-600 dark:bg-neutral-600 animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-1 h-1 rounded-full bg-gray-600 dark:bg-neutral-600 animate-bounce" style={{ animationDelay: '0.4s' }}></div>
          </div>
          <div className="ml-2 text-[10px] text-gray-600 dark:text-neutral-600 font-mono tabular-nums">
            {formatTime(elapsedTime)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingIndicator; 