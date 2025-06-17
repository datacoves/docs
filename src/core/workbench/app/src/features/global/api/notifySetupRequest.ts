import { axios } from '../../../lib/axios';

export const notifySetupRequest = () => {
  return axios.post(`api/setup/notify`);
};
