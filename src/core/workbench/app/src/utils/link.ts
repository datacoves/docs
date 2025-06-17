import { getSiteContext } from './siteContext';

export const openLink = (link: string | undefined) => {
  const newWindow = window.open(link, '_blank', 'noopener,noreferrer');
  if (newWindow) newWindow.opener = null;
};

export const docsLink = (isExternal: boolean) => {
  return isExternal
    ? `https://docs.datacoves.com`
    : `https://docs.datacoves.com#/?navbar=false&logo=false`;
};

export const loadLink = () => {
  const env = getSiteContext();

  return `https://airbyte-${env.host}`;
};

export const transformLink = (slug: string) => {
  const env = getSiteContext();

  return `https://${slug}-transform-${env.host}`;
};

export const orchestrateLink = () => {
  const env = getSiteContext();

  return `https://airflow-${env.host}/home`;
};

export const analyzeLink = () => {
  const env = getSiteContext();

  return `https://superset-${env.host}`;
};

export const localAirflowLink = (slug: string) => {
  const env = getSiteContext();

  return `https://${slug}-airflow-${env.host}/home`;
};
