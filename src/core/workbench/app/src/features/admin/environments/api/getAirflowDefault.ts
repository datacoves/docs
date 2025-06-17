import { useQuery } from 'react-query';

import { AirflowConfig, CodeServerConfig } from '../../../../context/UserContext/types';
import { axios } from '../../../../lib/axios';

interface AdaptersDefaultValues {
  airbyte: object;
  airflow: AirflowConfig;
  'dbt-docs': object;
  supersetIcon: object;
  'code-server': CodeServerConfig;
}

export const getAdaptersDefaultValues = (): Promise<AdaptersDefaultValues> => {
  return axios.get('api/admin/adapters/default-values');
};

export const useAdaptersDefaultValues = (options?: any) => {
  return useQuery('adapters', () => getAdaptersDefaultValues(), options);
};
