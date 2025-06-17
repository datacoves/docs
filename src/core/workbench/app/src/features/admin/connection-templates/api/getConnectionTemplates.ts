import { useQuery } from 'react-query';

import { axios } from '../../../../lib/axios';
import { IAPIPaginatedResponse } from '../../../../types';
import { ConnectionTemplate } from '../../../global/types';

interface IGetConnectionTemplates {
  account?: string;
  search?: string;
  project?: string;
  limit?: number;
  offset?: number;
}

interface IConnectionTemplatesResponse extends IAPIPaginatedResponse {
  results: ConnectionTemplate[];
}

export const getConnectionTemplates = ({
  account,
  search,
  project,
  limit,
  offset,
}: IGetConnectionTemplates): Promise<IConnectionTemplatesResponse> => {
  const params = {
    search: search ? search : undefined,
    project: project ? project : undefined,
    limit: limit ? limit : undefined,
    offset: offset ? offset : undefined,
  };
  return axios.get(`/api/admin/${account}/connectiontemplates`, { params: params });
};

export const useConnectionTemplates = ({
  account,
  search,
  project,
  limit,
  offset,
}: IGetConnectionTemplates) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['connectionTemplates', account, search, project, limit, offset],
    queryFn: () => getConnectionTemplates({ account, search, project, limit, offset }),
  });
};
