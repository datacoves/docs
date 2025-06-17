import { useQuery } from 'react-query';

import { axios } from '../../../lib/axios';
import { SSLKey } from '../types';

type TGetSSLKey = {
  key_format: string;
};

export const getSSLKey = (params: TGetSSLKey): Promise<SSLKey> => {
  return axios.get(`api/setup/generate-ssl-key`, { params });
};

export const useSSLKey = (key_format: string, options: any) => {
  return useQuery('ssl-key-' + key_format, async () => await getSSLKey({ key_format }), options);
};
