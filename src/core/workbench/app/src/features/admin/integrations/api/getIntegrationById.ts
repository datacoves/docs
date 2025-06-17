import { useQuery } from 'react-query';

import { axios } from '../../../../lib/axios';
import { Integration } from '../../../global/types';

export const getIntegrationById = (account?: string, id?: string): Promise<Integration> => {
  return axios.get(`/api/admin/${account}/integrations/${id}`);
};

export const useIntegration = (account?: string, id?: string, options?: any) => {
  return useQuery('integration', async () => await getIntegrationById(account, id), options);
};
