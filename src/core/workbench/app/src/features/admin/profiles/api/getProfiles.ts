import { useQuery } from 'react-query';

import { Environment as Profile } from '../../../../context/UserContext/types';
import { axios } from '../../../../lib/axios';
import { IAPIPaginatedResponse } from '../../../../types';

interface IGetProfiles {
  account?: string;
  search?: string;
  project?: string;
  limit?: number;
  offset?: number;
  options?: any;
}

interface IProfilesResponse extends IAPIPaginatedResponse {
  results: Profile[];
}

export const getProfiles = ({
  account: account,
  ...rest
}: IGetProfiles): Promise<IProfilesResponse> => {
  return axios.get(`/api/admin/${account}/profiles`, { params: rest });
};

export const useProfiles = ({ options: options, ...rest }: IGetProfiles) => {
  return useQuery(['profiles', ...Object.values(rest)], () => getProfiles(rest), {
    enabled: rest.account !== undefined,
    ...options,
  });
};

export const getAllProjects = ({ account }: { account?: string }): Promise<Profile[]> => {
  // Returns all profiles (without pagination)
  return axios.get(`/api/admin/${account}/profiles`);
};

interface UseAllProjectsOptions {
  account?: string;
}

export const useAllProjects = ({ account }: UseAllProjectsOptions) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['projects', account],
    queryFn: () => getAllProjects({ account }),
  });
};
