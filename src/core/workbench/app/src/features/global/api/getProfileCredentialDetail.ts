import { useQuery } from 'react-query';

import { axios } from '../../../lib/axios';
import { UserCredential } from '../types';

export const getProfileCredentialDetail = (id: string): Promise<UserCredential> => {
  return axios.get(`api/iam/profile/credentials/${id}`);
};

export const useProfileCredentialDetail = (id: string, options: any) => {
  return useQuery(
    'profileCredentialDetail',
    async () => await getProfileCredentialDetail(id),
    options
  );
};
