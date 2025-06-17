import { useQuery } from 'react-query';

import { axios } from '../../../lib/axios';
import { ConnectionType } from '../types';

interface IGetConnectionTypes {
  account?: string;
}

export const getConnectionTypes = ({ account }: IGetConnectionTypes): Promise<ConnectionType[]> => {
  return axios.get(`api/accounts/${account}/connectiontypes`);
};

export const useConnectionTypes = ({ account }: IGetConnectionTypes) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['connectionTypes', account],
    queryFn: () => getConnectionTypes({ account }),
  });
};
