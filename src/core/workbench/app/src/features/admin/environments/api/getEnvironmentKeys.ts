import { useQuery } from 'react-query';

import { EnvironmentKeys } from '../../../../context/UserContext/types';
import { axios } from '../../../../lib/axios';

export const getEnvironmentKeys = (account?: string, id?: string): Promise<EnvironmentKeys> => {
  return axios.get(`/api/admin/${account}/environments/${id}/keys`);
};

export const useEnvironmentKeys = (account?: string, id?: string, options?: any) => {
  return useQuery('environmentKeys', () => getEnvironmentKeys(account, id), options);
};
