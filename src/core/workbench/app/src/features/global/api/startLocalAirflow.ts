import { axios } from '../../../lib/axios';

export const startLocalAirflow = (envSlug: string) => {
  return axios.post(`api/workbench/${envSlug}/code-server/start-local-airflow`);
};
