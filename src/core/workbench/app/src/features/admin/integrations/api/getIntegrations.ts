import { useQuery } from 'react-query';

import { axios } from '../../../../lib/axios';
import { IAPIPaginatedResponse } from '../../../../types';
import { Integration } from '../../../global/types';

interface IGetIntegrations {
  account?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

interface IIntegrationsResponse extends IAPIPaginatedResponse {
  results: Integration[];
}

export const getIntegrations = ({
  account,
  search,
  limit,
  offset,
}: IGetIntegrations): Promise<IIntegrationsResponse> => {
  const params = {
    search: search ? search : undefined,
    limit: limit ? limit : undefined,
    offset: offset ? offset : undefined,
  };
  return axios.get(`/api/admin/${account}/integrations`, { params: params });
};

export const useIntegrations = ({ account, search, limit, offset }: IGetIntegrations) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['integrations', account, search, limit, offset],
    queryFn: () => getIntegrations({ account, search, limit, offset }),
  });
};

export const getAllIntegrations = ({ account }: { account?: string }): Promise<Integration[]> => {
  // Returns all integrations (without pagination)
  return axios.get(`/api/admin/${account}/integrations`);
};

interface UseAllIntegrationsOptions {
  account?: string;
}

export const useAllIntegrations = ({ account }: UseAllIntegrationsOptions) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['integrations', account],
    queryFn: () => getAllIntegrations({ account }),
  });
};
