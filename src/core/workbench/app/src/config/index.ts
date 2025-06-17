const regex = /^[^.]+/;
const suffix = location.hostname.match(regex)?.shift();
export const IS_WORKBENCH = suffix && suffix.length === 6;
export const ENV_SLUG = IS_WORKBENCH ? suffix : undefined;
export const HOST = location.hostname;

const apiUrl = IS_WORKBENCH ? location.hostname.replace(regex, 'api') : 'api.' + location.hostname;
export const API_URL = `https://${apiUrl}`;
export const WS_URL = `wss://${apiUrl}`;

export const LAUNCHPAD_HOST = IS_WORKBENCH
  ? location.hostname.replace(/^[^.]+\./, '')
  : location.hostname;
