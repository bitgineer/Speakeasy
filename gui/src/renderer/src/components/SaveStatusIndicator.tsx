import React, { useEffect, useState } from 'react';

interface SaveStatusIndicatorProps {
  status: 'idle' | 'unsaved' | 'saving' | 'saved';
  className?: string;
}

export const SaveStatusIndicator: React.FC<SaveStatusIndicatorProps> = ({
  status,
  className = '',
}) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    let timeoutId: NodeJS.Timeout;

    if (status === 'saved') {
      setIsVisible(true);
      timeoutId = setTimeout(() => {
        setIsVisible(false);
      }, 3000);
    } else if (status === 'idle') {
      setIsVisible(false);
    } else {
      // For 'unsaved' and 'saving', always show immediately
      setIsVisible(true);
    }

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [status]);

  if (status === 'idle' && !isVisible) return null;

  return (
    <div
      className={`inline-flex items-center gap-2 text-sm font-medium transition-opacity duration-500 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      } ${className}`}
      aria-live="polite"
    >
      {status === 'unsaved' && (
        <>
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-yellow-500"></span>
          </span>
          <span className="text-gray-400">Unsaved changes</span>
        </>
      )}

      {status === 'saving' && (
        <>
          <svg
            className="animate-spin h-4 w-4 text-blue-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          <span className="text-gray-400">Saving...</span>
        </>
      )}

      {status === 'saved' && (
        <>
          <svg
            className="h-4 w-4 text-green-500"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path d="M5 13l4 4L19 7"></path>
          </svg>
          <span className="text-gray-400">Saved</span>
        </>
      )}
    </div>
  );
};

export default SaveStatusIndicator;
