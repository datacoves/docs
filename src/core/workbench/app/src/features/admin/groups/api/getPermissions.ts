import { useQuery } from 'react-query';

import { axios } from '../../../../lib/axios';
import { Permission } from '../types';

export const getAllPermissions = ({ account }: { account?: string }): Promise<Permission[]> => {
  return axios.get(`api/admin/${account}/permissions`);
};

interface UsePermissionsOptions {
  account?: string;
}

export const useAllPermissions = ({ account }: UsePermissionsOptions) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['permissions', account],
    queryFn: () => getAllPermissions({ account }),
  });
};
