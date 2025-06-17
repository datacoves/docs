import { ColorModeScript } from '@chakra-ui/react';
import * as Sentry from '@sentry/react';
import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import {
  useLocation,
  useNavigationType,
  createRoutesFromChildren,
  matchRoutes,
} from 'react-router-dom';

import App from './App';
import { ENV_SLUG, LAUNCHPAD_HOST } from './config';
import reportWebVitals from './reportWebVitals';

if (LAUNCHPAD_HOST !== 'datacoveslocal.com') {
  Sentry.init({
    dsn: 'https://f9363d6cdb8f4d8685e926eb7111d3a2@o1145668.ingest.sentry.io/6213367',
    // This enables automatic instrumentation (highly recommended)
    // If you only want to use custom instrumentation:
    // * Remove the `BrowserTracing` integration
    // * add `Sentry.addTracingExtensions()` above your Sentry.init() call
    integrations: [
      Sentry.metrics.metricsAggregatorIntegration(),
      Sentry.browserTracingIntegration(),
      // Or, if you are using react router, use the appropriate integration
      // See docs for support for different versions of react router
      // https://docs.sentry.io/platforms/javascript/guides/react/configuration/integrations/react-router/
      Sentry.reactRouterV6BrowserTracingIntegration({
        useEffect: React.useEffect,
        useLocation,
        useNavigationType,
        createRoutesFromChildren,
        matchRoutes,
      }),
    ],
    environment: LAUNCHPAD_HOST,
    tracesSampler: (samplingContext) => {
      // We want all the workspace load times.  Everything else can be
      // 1 in 10.
      if (samplingContext.name == 'Workbench Load Time') {
        return 1;
      } else {
        return 0.1;
      }
    },
  });
  Sentry.setTag('env.slug', ENV_SLUG);
}

const container = document.getElementById('root');
// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
const root = createRoot(container!);
root.render(
  <React.StrictMode>
    <ColorModeScript />
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
