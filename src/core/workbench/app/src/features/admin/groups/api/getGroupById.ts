import { useQuery } from 'react-query';

import { axios } from '../../../../lib/axios';
import { Group } from '../types';

export const getGroupById = (account?: string, id?: string): Promise<Group> => {
  return axios.get(`api/admin/${account}/groups/${id}`);
};

export const useGroup = (account?: string, id?: string, options?: any) => {
  return useQuery('group', async () => await getGroupById(account, id), options);
};
