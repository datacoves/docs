import { useQuery } from 'react-query';

import { Environment } from '../../../../context/UserContext/types';
import { axios } from '../../../../lib/axios';

export const getEnvironmentById = (account?: string, id?: string): Promise<Environment> => {
  return axios.get(`/api/admin/${account}/environments/${id}`);
};

export const useEnvironment = (account?: string, id?: string, options?: any) => {
  return useQuery('environment', () => getEnvironmentById(account, id), options);
};
