import { useQuery } from 'react-query';

import { axios } from '../../../../lib/axios';
import { Secret } from '../../../global/types';

export const getSecretById = (account?: string, id?: string): Promise<Secret> => {
  return axios.get(`/api/admin/${account}/secrets/${id}`);
};

export const useSecret = (account?: string, id?: string, options?: any) => {
  return useQuery('secret', async () => await getSecretById(account, id), options);
};
