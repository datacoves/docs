import { useQuery } from 'react-query';

import { axios } from '../../../../lib/axios';
import { Invitation } from '../types';

export const getInvitationById = (account?: string, id?: string): Promise<Invitation> => {
  return axios.get(`api/admin/${account}/invitations/${id}`);
};

export const useInvitation = (account?: string, id?: string, options?: any) => {
  return useQuery('invitation', async () => await getInvitationById(account, id), options);
};
