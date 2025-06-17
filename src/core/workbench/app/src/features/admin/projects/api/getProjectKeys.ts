import { useQuery } from 'react-query';

import { ProjectKeys } from '../../../../context/UserContext/types';
import { axios } from '../../../../lib/axios';

export const getProjectKeys = (account?: string, id?: string): Promise<ProjectKeys> => {
  return axios.get(`/api/admin/${account}/projects/${id}/keys`);
};

export const useProjectKeys = (account?: string, id?: string, options?: any) => {
  return useQuery('projectKeys', () => getProjectKeys(account, id), options);
};
