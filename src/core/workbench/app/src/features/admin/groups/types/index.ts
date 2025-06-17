import { Environment, Project } from '../../../../context/UserContext/types';

export type ExtendedGroup = {
  identity_groups: string[];
  description: string;
  name: string;
  project?: Project;
  environment?: Environment;
};

export type Group = {
  id: string;
  name: string;
  extended_group: ExtendedGroup;
  permissions: Permission[];
  users_count: number;
};

export type Permission = {
  project?: string;
  environment?: string;
  project_id?: string;
  environment_id?: string;
  account: string;
  resource: string;
  action: string;
  id: string;
  scope: string;
};
