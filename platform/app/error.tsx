"use client";

import { useEffect } from "react";

export default function RootError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Sanitized log — full error server-side only, never rendered to the client.
    console.error("Unhandled platform error:", error.digest || error.message);
  }, [error]);

  return (
    <div className="min-h-screen bg-canvas text-ink flex flex-col items-center justify-center p-6 font-sans">
      <div className="panel max-w-md w-full p-8 border border-border text-center">
        <p className="font-mono text-xs tracking-widest text-accent uppercase mb-2">
          SYSTEM NOTICE
        </p>
        <h1 className="font-serif text-2xl mb-4 text-ink">An unexpected error occurred</h1>
        <p className="text-sm text-muted mb-6">
          The operation could not be completed. Please try refreshing or return to the dashboard.
        </p>
        <button
          onClick={() => reset()}
          className="bg-accent hover:bg-accent-bright text-canvas-deep text-sm font-semibold py-2 px-6 rounded transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
