import { useQuery } from 'react-query';

import { axios } from '../../../../lib/axios';
import { ConnectionTemplate } from '../../../global/types';

export const getConnectionTemplateById = (
  account?: string,
  id?: string
): Promise<ConnectionTemplate> => {
  return axios.get(`/api/admin/${account}/connectiontemplates/${id}`);
};

export const useConnectionTemplate = (account?: string, id?: string, options?: any) => {
  return useQuery(
    'connectionTemplate',
    async () => await getConnectionTemplateById(account, id),
    options
  );
};
