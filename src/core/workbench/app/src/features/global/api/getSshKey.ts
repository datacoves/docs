import { useQuery } from 'react-query';

import { axios } from '../../../lib/axios';
import { SSHKey } from '../types';

type TGetSSHKey = {
  usage: string;
  ssh_key_type?: string;
};

export const getSSHKey = (params: TGetSSHKey): Promise<SSHKey> => {
  return axios.get(`api/setup/generate-ssh-key`, { params });
};

export const useSSHKey = (usage: string, options: any) => {
  return useQuery('ssh-key-' + usage, async () => await getSSHKey({ usage: usage }), options);
};
