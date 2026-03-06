'use client';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Forward errors to production error reporting service (e.g., Sentry)
    // In production: Sentry.captureException(error);
    // For now, log to console in development only
    if (process.env.NODE_ENV === 'development') {
      console.error('Global error:', error);
    }
    // In production, you would call: Sentry.captureException(error, { extra: { digest: error.digest } });
  }, [error]);

  return (
    <html>
      <body>
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#0f172a',
          color: '#f8fafc',
          fontFamily: 'system-ui, sans-serif',
          padding: '2rem',
        }}>
          <div style={{
            maxWidth: '400px',
            textAlign: 'center',
          }}>
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: 'bold',
              marginBottom: '1rem',
              color: '#f87171',
            }}>
              Something went wrong
            </h2>
            <p style={{
              color: '#94a3b8',
              marginBottom: '1.5rem',
            }}>
              An unexpected error occurred
            </p>
            <button
              onClick={() => reset()}
              style={{
                backgroundColor: '#7c3aed',
                color: 'white',
                padding: '0.75rem 1.5rem',
                borderRadius: '0.5rem',
                border: 'none',
                cursor: 'pointer',
                fontSize: '1rem',
                fontWeight: '500',
              }}
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
