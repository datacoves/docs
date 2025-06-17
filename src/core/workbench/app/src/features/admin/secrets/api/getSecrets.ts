import { useQuery } from 'react-query';

import { axios } from '../../../../lib/axios';
import { IAPIPaginatedResponse } from '../../../../types';
import { Secret } from '../../../global/types';

interface IGetSecrets {
  account?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

interface ISecretsResponse extends IAPIPaginatedResponse {
  results: Secret[];
}

export const getSecrets = ({
  account,
  search,
  limit,
  offset,
}: IGetSecrets): Promise<ISecretsResponse> => {
  const params = {
    search: search ? search : undefined,
    limit: limit ? limit : undefined,
    offset: offset ? offset : undefined,
  };
  return axios.get(`/api/admin/${account}/secrets`, { params: params });
};

export const useSecrets = ({ account, search, limit, offset }: IGetSecrets) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['secrets', account, search, limit, offset],
    queryFn: () => getSecrets({ account, search, limit, offset }),
  });
};

export const getAllSecrets = ({ account }: { account?: string }): Promise<Secret[]> => {
  // Returns all secrets (without pagination)
  return axios.get(`/api/admin/${account}/secrets`);
};
