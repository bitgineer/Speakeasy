/**
 * ModelLoadingBanner Component
 *
 * Displays a banner when the model is loading to inform users why they can't record yet.
 */

import React from "react";
import { Loader2 } from "lucide-react";

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
      className={`rounded-panel border border-accent-border bg-accent-muted p-4 ${className}`}
      role="status"
      aria-live="polite"
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          <Loader2 className="animate-spin h-5 w-5 text-accent-text" aria-hidden="true" />
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="text-ui font-semibold text-content-primary mb-1">
            Loading model...
          </h3>
          <p className="text-small text-content-secondary">
            {modelName ? (
              <>
                <span className="font-medium">{modelName}</span> is
                initializing. This can take 1–2 minutes on first load.
              </>
            ) : (
              "The transcription model is initializing. This can take 1–2 minutes on first load."
            )}
          </p>
          <p className="text-caption text-content-muted mt-2">
            Recording will be available once the model is ready.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ModelLoadingBanner;
