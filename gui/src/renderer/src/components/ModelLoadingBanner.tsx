/**
 * ModelLoadingBanner Component
 *
 * Displays a banner when the model is loading to inform users why they can't record yet.
 */

import React from "react";

interface ModelLoadingBannerProps {
  modelName?: string | null;
  className?: string;
}

const ModelLoadingBanner: React.FC<ModelLoadingBannerProps> = ({
  modelName,
  className = "",
}) => {
  return (
    <div
      className={`bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-lg p-4 ${className}`}
      role="status"
      aria-live="polite"
    >
      <div className="flex items-start gap-3">
        {/* Animated spinner */}
        <div className="flex-shrink-0 mt-0.5">
          <svg
            className="animate-spin h-5 w-5 text-blue-400"
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
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-blue-200 mb-1">
            Loading Model...
          </h3>
          <p className="text-sm text-gray-300">
            {modelName ? (
              <>
                <span className="font-medium">{modelName}</span> is
                initializing. This can take 1-2 minutes on first load.
              </>
            ) : (
              "The transcription model is initializing. This can take 1-2 minutes on first load."
            )}
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Recording will be available once the model is ready.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ModelLoadingBanner;
