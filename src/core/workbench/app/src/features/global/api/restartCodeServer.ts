import { axios } from '../../../lib/axios';

export const restartCodeServer = (envSlug: string) => {
  return axios.post(`api/workbench/${envSlug}/code-server/restart`);
};
