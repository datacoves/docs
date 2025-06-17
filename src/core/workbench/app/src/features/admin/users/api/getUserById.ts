import { useQuery } from 'react-query';

import { axios } from '../../../../lib/axios';
import { User } from '../types';

export const getUserById = (account?: string, id?: string): Promise<User> => {
  return axios.get(`api/admin/${account}/users/${id}`);
};

export const useUser = (account?: string, id?: string, options?: any) => {
  return useQuery('user', async () => await getUserById(account, id), options);
};
