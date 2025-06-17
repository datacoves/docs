import { useQuery } from 'react-query';

import { Template } from '../../../../context/UserContext/types';
import { axios } from '../../../../lib/axios';

interface IGetTemplates {
  account?: string;
  contextType?: string;
  enabled_for?: string;
}

export const getAllTemplates = ({
  account,
  contextType,
  enabled_for,
}: IGetTemplates): Promise<Template[]> => {
  const params = {
    context_type: contextType ? contextType : undefined,
    enabled_for: enabled_for ? enabled_for : undefined,
  };
  return axios.get(`/api/admin/${account}/templates`, {
    params: params,
  });
};

export const useAllTemplates = ({ account, contextType, enabled_for }: IGetTemplates) => {
  return useQuery({
    enabled: account !== undefined,
    queryKey: ['templates', account, contextType, enabled_for],
    queryFn: () => getAllTemplates({ account, contextType, enabled_for }),
  });
};
