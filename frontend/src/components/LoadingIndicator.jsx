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
      <div className="bg-gray-800 text-white rounded-lg rounded-tl-none p-4 max-w-[80%]">
        <div className="flex items-center">
          <span className="mr-2">{message}</span>
          <div className="flex space-x-1">
            <div className="w-2 h-2 rounded-full bg-gray-300 animate-bounce"></div>
            <div className="w-2 h-2 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: '0.4s' }}></div>
          </div>
          <div className="ml-2 text-xs text-gray-400">
            {formatTime(elapsedTime)}
          </div>
        </div>
        <div className="text-xs text-gray-400 mt-1">
          This usually takes about a minute
        </div>
      </div>
    </div>
  );
};

export default LoadingIndicator; 