import { groupBy } from 'lodash';

import { Group } from '../../features/admin/groups/types';

export interface GroupFormValues {
  name: string;
  email: string;
  groups: string[];
}

export type ProjectGroupType = Record<
  string,
  { permissions: Group[]; environments: { [key: string]: Group[] } }
>;

export const generalGroups: Record<string, string> = {
  Developer: 'Developer',
  SysAdmin: 'Sys Admin',
  Viewer: 'Viewer',
  AccountAdmin: 'Account Admin',
  AccountDefault: 'Account Default',
};

export const getProjectsList = (groups: Group[] | undefined) =>
  (groups || [])?.filter(
    ({ extended_group }) => !!extended_group.project && !extended_group.environment
  );

export const getEnvironmentList = (groups: Group[] | undefined) =>
  (groups || [])?.filter(({ extended_group }) => !!extended_group.environment);

export const addProjectsIntoProjectGroup = (groups: Group[] | undefined) => {
  const projects = groupBy(getProjectsList(groups), 'extended_group.project.name');
  const grouppedProjects: ProjectGroupType = {};
  Object.keys(projects).forEach((key) => {
    grouppedProjects[key] = {
      permissions: projects[key],
      environments: {
        ...groupBy(
          getEnvironmentList(groups).filter(
            ({ extended_group }) =>
              extended_group.environment?.project === projects[key][0].extended_group.project?.id
          ),
          (group) => createGroupName(group)
        ),
      },
    };
  });

  return grouppedProjects;
};

export const labelGroup = (group: string): string => {
  if (group.endsWith('Developer')) {
    return generalGroups.Developer;
  }
  if (group.endsWith('Sys Admin')) {
    return generalGroups.SysAdmin;
  }
  if (group.endsWith('Viewer')) {
    return generalGroups.Viewer;
  }
  if (group.endsWith('Account Admin')) {
    return generalGroups.AccountAdmin;
  }
  if (group.endsWith('Account Default')) {
    return generalGroups.AccountDefault;
  }
  return group;
};

export const createGroupName = (group: Group) => {
  if (group.extended_group.environment)
    return `${group.extended_group.environment.name} (${group.extended_group.environment.slug})`;
  if (group.extended_group.project) return group.extended_group.project.name;
  return group.name;
};
