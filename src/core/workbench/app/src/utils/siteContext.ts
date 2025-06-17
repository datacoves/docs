import { ENV_SLUG, HOST, IS_WORKBENCH, LAUNCHPAD_HOST } from '../config';

export function getSiteContext() {
  return {
    env: ENV_SLUG,
    host: HOST,
    isWorkbench: IS_WORKBENCH,
    launchpadHost: LAUNCHPAD_HOST,
  };
}
