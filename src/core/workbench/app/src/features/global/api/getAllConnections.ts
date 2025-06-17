import { useQuery } from 'react-query';

import { axios } from '../../../lib/axios';
import { RConnectionTemplate } from '../types';

interface IGetProjectConnections {
  account?: string;
  project?: number;
  forUsers?: boolean;
}

export const getAllConnectionTemplates = ({
  account,
  project,
  forUsers,
}: IGetProjectConnections): Promise<RConnectionTemplate[]> => {
  const params = {
    project: project ? project : undefined,
    for_users: forUsers,
  };
  return axios.get(`api/accounts/${account}/connectiontemplates`, { params: params });
};

export const useAllConnectionTemplates = ({
  account,
  project,
  forUsers,
}: IGetProjectConnections) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['allConnections', account, project],
    queryFn: () => getAllConnectionTemplates({ account, project, forUsers }),
  });
};
