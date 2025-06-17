import { useQuery } from 'react-query';

import { axios } from '../../../lib/axios';
import { Account } from '../types';

export const getUserAccounts = (): Promise<Account[]> => {
  return axios.get('api/iam/accounts');
};

export const useGetUserAccounts = (options?: any) => {
  return useQuery(['getUserAccounts'], async () => await getUserAccounts(), options);
};
