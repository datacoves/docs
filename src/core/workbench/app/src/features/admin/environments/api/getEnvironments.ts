import { useQuery } from 'react-query';

import { Environment } from '../../../../context/UserContext/types';
import { axios } from '../../../../lib/axios';
import { IAPIPaginatedResponse } from '../../../../types';

interface IGetEnvironments {
  account?: string;
  search?: string;
  project?: string;
  limit?: number;
  offset?: number;
  options?: any;
}

interface IEnvironmentsResponse extends IAPIPaginatedResponse {
  results: Environment[];
}

export const getEnvironments = ({
  account: account,
  ...rest
}: IGetEnvironments): Promise<IEnvironmentsResponse> => {
  return axios.get(`/api/admin/${account}/environments`, { params: rest });
};

export const useEnvironments = ({ options: options, ...rest }: IGetEnvironments) => {
  return useQuery(['environments', ...Object.values(rest)], () => getEnvironments(rest), {
    enabled: rest.account !== undefined,
    ...options,
  });
};

export const getAllEnvironments = ({ account }: { account?: string }): Promise<Environment[]> => {
  // Returns all environments (without pagination)
  return axios.get(`/api/admin/${account}/environments`);
};

interface UseAllProjectsOptions {
  account?: string;
}

export const useAllEnvironments = ({ account }: UseAllProjectsOptions) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['environments', account],
    queryFn: () => getAllEnvironments({ account }),
  });
};
