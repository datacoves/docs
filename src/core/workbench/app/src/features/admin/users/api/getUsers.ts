import { useQuery } from 'react-query';

import { axios } from '../../../../lib/axios';
import { IAPIPaginatedResponse } from '../../../../types';
import { User } from '../types';

interface IGetUsers {
  account?: string;
  search?: string;
  group?: number;
  limit?: number;
  offset?: number;
}

interface IUsersResponse extends IAPIPaginatedResponse {
  results: User[];
}

export const getUsers = ({
  account,
  search,
  group,
  limit,
  offset,
}: IGetUsers): Promise<IUsersResponse> => {
  const params = {
    search: search ? search : undefined,
    groups: group ? group : undefined,
    limit: limit ? limit : undefined,
    offset: offset ? offset : undefined,
  };
  return axios.get(`/api/admin/${account}/users`, {
    params: params,
  });
};

export const useUsers = ({ account, search, group, limit, offset }: IGetUsers) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['users', account, search, group, limit, offset],
    queryFn: () => getUsers({ account, search, group, limit, offset }),
  });
};
