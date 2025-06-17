import { useQuery } from 'react-query';

import { axios } from '../../../../lib/axios';
import { ServiceCredential } from '../../../global/types';

export const getServiceCredentialById = (
  account?: string,
  id?: string
): Promise<ServiceCredential> => {
  return axios.get(`/api/admin/${account}/servicecredentials/${id}`);
};

export const useServiceCredential = (account?: string, id?: string, options?: any) => {
  return useQuery(
    'serviceCredentials',
    async () => await getServiceCredentialById(account, id),
    options
  );
};
