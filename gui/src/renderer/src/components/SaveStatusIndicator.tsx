import React, { useEffect, useState } from 'react';
import { Check, Loader2 } from 'lucide-react';
import { Button } from './ui/button';

interface SaveStatusIndicatorProps {
  status: 'idle' | 'unsaved' | 'saving' | 'saved';
  onSave?: () => void;
  className?: string;
}

export const SaveStatusIndicator: React.FC<SaveStatusIndicatorProps> = ({
  status,
  onSave,
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
      className={`save-state transition-opacity duration-base ${
        isVisible ? 'opacity-100' : 'opacity-0'
      } ${className}`}
      data-state={status}
      aria-live="polite"
    >
      {status === 'unsaved' && (
        <>
          <span className="save-dot" aria-hidden="true" />
          <span>Unsaved changes</span>
          {onSave && (
            <Button size="sm" onClick={onSave}>
              Save
            </Button>
          )}
        </>
      )}

      {status === 'saving' && (
        <>
          <Loader2 className="animate-spin" size={14} aria-hidden="true" />
          <span>Saving...</span>
        </>
      )}

      {status === 'saved' && (
        <>
          <Check size={14} aria-hidden="true" />
          <span>Saved</span>
        </>
      )}
    </div>
  );
};

export default SaveStatusIndicator;
