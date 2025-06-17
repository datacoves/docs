import { axios } from '../../../../lib/axios';
import { User } from '../../users/types';

export const getTotalUsers = (account: string): Promise<User[]> => {
  return axios.get(`api/admin/${account}/users`);
};
