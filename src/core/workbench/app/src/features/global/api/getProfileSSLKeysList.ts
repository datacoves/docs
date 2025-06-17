import { useQuery } from 'react-query';

import { axios } from '../../../lib/axios';
import { UserSSLKey } from '../types';

export const getProfileSSLKeysList = (): Promise<UserSSLKey[]> => {
  return axios.get(`api/iam/profile/ssl-keys`);
};

export const useProfileSSLKeysList = () => {
  return useQuery({
    queryKey: ['profileSSLKeys'],
    queryFn: () => getProfileSSLKeysList(),
  });
};
