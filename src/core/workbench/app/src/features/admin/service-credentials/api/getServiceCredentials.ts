import { useQuery } from 'react-query';

import { axios } from '../../../../lib/axios';
import { IAPIPaginatedResponse } from '../../../../types';
import { ServiceCredential } from '../../../global/types';

interface IGetEnvironmentConnections {
  account?: string;
  environment?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

interface IServiceCredentialsResponse extends IAPIPaginatedResponse {
  results: ServiceCredential[];
}

export const getServiceCredentials = ({
  account,
  environment,
  search,
  limit,
  offset,
}: IGetEnvironmentConnections): Promise<IServiceCredentialsResponse> => {
  const params = {
    search: search ? search : undefined,
    environment: environment ? environment : undefined,
    limit: limit ? limit : undefined,
    offset: offset ? offset : undefined,
  };
  return axios.get(`/api/admin/${account}/servicecredentials`, {
    params: params,
  });
};

export const useServiceCredentials = ({
  account,
  environment,
  search,
  limit,
  offset,
}: IGetEnvironmentConnections) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['serviceCredentials', account, environment, search, limit, offset],
    queryFn: () => getServiceCredentials({ account, environment, search, limit, offset }),
  });
};
