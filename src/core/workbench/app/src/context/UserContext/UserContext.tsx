import { createContext } from 'react';

import { getSiteContext } from '../../utils/siteContext';

import { User, IUserContext } from './types';

export const UserContext = createContext<IUserContext>({
  currentUser: undefined,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  setCurrentUser: (user: User | undefined) => {},
});

export const tabPermissions: Record<string, string[]> = {
  docs: [],
  load: ['airbyte'],
  transform: ['code-server'],
  observe: ['dbt-docs', 'local-dbt-docs', 'datahub'],
  orchestrate: ['airflow'],
  analyze: ['superset'],
};

export const HasTabAccess = function (user: User, tab: string) {
  return tab === 'docs'
    ? HasWorkbenchAccess(user)
    : HasWorkbenchServiceAccess(user, tabPermissions[tab]);
};

export const HasWorkbenchServiceAccess = function (user: User, codes: string[]) {
  const envSlug = getSiteContext().env;
  const project = user.projects.find((project) =>
    project.environments.find((environment) => environment.slug === envSlug)
  );
  const env = project && project.environments.find((environment) => environment.slug === envSlug);
  return (
    user &&
    env &&
    confirmUserPermissions(user, codes, envSlug, project.slug) &&
    codes.some((code) => env.services[code].enabled && env.services[code].valid)
  );
};

export const confirmUserPermissions = (
  user: User,
  codes: string[],
  envSlug: string | undefined,
  projectSlug: string | undefined
) =>
  user.permissions.find((permission) =>
    codes.some(
      (code) =>
        permission.includes(`${envSlug}|workbench:${code}`) ||
        permission.includes(`${projectSlug}|workbench:${code}`)
    )
  );

export const HasWorkbenchAccess = function (user: User) {
  const envSlug = getSiteContext().env;
  const project = user.projects.find((project) =>
    project.environments.find((environment) => environment.slug === envSlug)
  );
  const env = project && project.environments.find((environment) => environment.slug === envSlug);
  return (
    user &&
    env &&
    user.permissions.find(
      (permission) =>
        permission.includes(`${envSlug}|workbench:`) ||
        permission.includes(`${project.slug}|workbench:`)
    )
  );
};

export const GetEnvironmentNameAndSlug = function (user: User | undefined) {
  const envSlug = getSiteContext().env;
  const project = user?.projects.find((project) =>
    project.environments.find((environment) => environment.slug === envSlug)
  );
  const env = project && project.environments.find((environment) => environment.slug === envSlug);
  return {
    currentEnvName: env?.name,
    currentEnvSlug: env?.slug.toUpperCase(),
  };
};
