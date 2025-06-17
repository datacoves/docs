import { useQuery } from 'react-query';

import { axios } from '../../../../lib/axios';
import { IAPIPaginatedResponse } from '../../../../types';
import { Invitation } from '../types';

interface IGetInvitations {
  account?: string;
  search?: string;
  group?: number;
  limit?: number;
  offset?: number;
}

interface IInvitationsResponse extends IAPIPaginatedResponse {
  results: Invitation[];
}

export const getInvitations = ({
  account,
  search,
  group,
  limit,
  offset,
}: IGetInvitations): Promise<IInvitationsResponse> => {
  const params = {
    search: search ? search : undefined,
    groups: group ? group : undefined,
    limit: limit ? limit : undefined,
    offset: offset ? offset : undefined,
  };
  return axios.get(`/api/admin/${account}/invitations`, {
    params: params,
  });
};

export const useInvitations = ({ account, search, group, limit, offset }: IGetInvitations) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['invitations', account, search, group, limit, offset],
    queryFn: () => getInvitations({ account, search, group, limit, offset }),
  });
};
