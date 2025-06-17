import { useQuery } from 'react-query';

import { Account } from '../../../../context/AccountContext/types';
import { axios } from '../../../../lib/axios';

export const getAccountDetail = (account?: string): Promise<Account> => {
  return axios.get(`api/admin/${account}/settings`);
};

export const useAccountDetail = (account?: string, options?: any) => {
  return useQuery('accountDetail', async () => await getAccountDetail(account), options);
};
