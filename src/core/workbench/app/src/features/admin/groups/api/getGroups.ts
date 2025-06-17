import { useQuery } from 'react-query';

import { axios } from '../../../../lib/axios';
import { IAPIPaginatedResponse } from '../../../../types';
import { Group } from '../types';

interface IGetGroups {
  account?: string;
  search?: string;
  group?: number;
  limit?: number;
  offset?: number;
}

interface IGroupsResponse extends IAPIPaginatedResponse {
  results: Group[];
}

export const getGroups = ({
  account,
  search,
  group,
  limit,
  offset,
}: IGetGroups): Promise<IGroupsResponse> => {
  const params = {
    search: search ? search : undefined,
    groups: group ? group : undefined,
    limit: limit ? limit : 10,
    offset: offset ? offset : undefined,
  };
  return axios.get(`api/admin/${account}/groups`, {
    params: params,
  });
};

export const getAllGroups = ({ account }: { account?: string }): Promise<Group[]> => {
  return axios.get(`api/admin/${account}/groups`);
};

export const useGroups = ({ account, search, group, limit, offset }: IGetGroups) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['groups', account, search, group, limit, offset],
    queryFn: () => getGroups({ account, search, group, limit, offset }),
  });
};

interface UseAllGroupsOptions {
  account?: string;
}

export const useAllGroups = ({ account }: UseAllGroupsOptions) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['groups', account],
    queryFn: () => getAllGroups({ account }),
  });
};
