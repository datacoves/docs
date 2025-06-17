import { useQuery } from 'react-query';

import { Project } from '../../../../context/UserContext/types';
import { axios } from '../../../../lib/axios';

export const getProjectById = (account?: string, id?: string): Promise<Project> => {
  return axios.get(`api/admin/${account}/projects/${id}`);
};

export const useProject = (account?: string, id?: string, options?: any) => {
  return useQuery('project', async () => await getProjectById(account, id), options);
};

export const useDependantProject = (account?: string, id?: string, options?: any) => {
  return useQuery(['project', id], async () => await getProjectById(account, id), options);
};
