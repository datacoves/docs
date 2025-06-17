import { useQuery, DefaultOptions } from 'react-query';

import { axios } from '../../../lib/axios';
import { UserCredential } from '../types';

interface IGetProfileCredentials {
  environment: number | undefined;
}

export const getProfileCredentialsList = ({
  environment,
}: IGetProfileCredentials): Promise<UserCredential[]> => {
  const params = {
    environment: environment ? environment : undefined,
  };
  return axios.get(`api/iam/profile/credentials`, { params: params });
};

interface UseProfileCredentials extends IGetProfileCredentials {
  config?: DefaultOptions<typeof getProfileCredentialsList>;
}

export const useProfileCredentialsList = ({ environment, config }: UseProfileCredentials) => {
  return useQuery({
    ...config,
    queryKey: ['profileCredentials', environment],
    queryFn: () => getProfileCredentialsList({ environment }),
  });
};
