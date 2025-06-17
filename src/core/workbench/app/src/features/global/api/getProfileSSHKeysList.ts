import { useQuery } from 'react-query';

import { axios } from '../../../lib/axios';
import { UserSSHKey } from '../types';

export const getProfileSSHKeysList = (): Promise<UserSSHKey[]> => {
  return axios.get(`api/iam/profile/ssh-keys`);
};

export const useProfileSSHKeysList = () => {
  return useQuery({
    queryKey: ['profileSSHKeys'],
    queryFn: () => getProfileSSHKeysList(),
  });
};
