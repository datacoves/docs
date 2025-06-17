import { useQuery } from 'react-query';

import { Profile } from '../../../../context/UserContext/types';
import { axios } from '../../../../lib/axios';

export const getProfileById = (account?: string, id?: string): Promise<Profile> => {
  return axios.get(`/api/admin/${account}/profiles/${id}`);
};

export const useProfile = (account?: string, id?: string, options?: any) => {
  return useQuery('profile', () => getProfileById(account, id), options);
};
