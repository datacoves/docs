import React from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';

import { ErrorFallback } from '../components/Error';
import { queryClient } from '../lib/react-query';

import { UIProvider } from './UIProvider';

type AppProviderProps = {
  children: React.ReactNode;
};

declare global {
  interface Window {
    gtag: any;
  }
}

export const AppProvider = ({ children }: AppProviderProps) => {
  return (
    <React.Suspense
      fallback={<div className="h-screen w-screen flex items-center justify-center"></div>}
    >
      <QueryClientProvider client={queryClient}>
        {process.env.NODE_ENV !== 'test' && <ReactQueryDevtools position="bottom-right" />}
        <ErrorBoundary FallbackComponent={ErrorFallback}>
          <UIProvider>{children}</UIProvider>
        </ErrorBoundary>
      </QueryClientProvider>
    </React.Suspense>
  );
};
