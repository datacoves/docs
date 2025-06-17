import { useQuery } from 'react-query';

import { axios } from '../../../lib/axios';
import { User } from '../types';

type TGetUserInfo = {
  environment?: string;
  account?: string;
};

export const getUserInfo = (params: TGetUserInfo): Promise<User> => {
  return axios.get('api/iam/user-info', { params });
};

export const useGetUserInfo = (params: TGetUserInfo, options?: any) => {
  return useQuery(
    ['getUserInfo', params.account, params.environment],
    async () => await getUserInfo(params),
    options
  );
};
