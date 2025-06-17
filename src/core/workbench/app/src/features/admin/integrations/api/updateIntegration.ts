import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';
import { useNavigate } from 'react-router-dom';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const updateIntegration = (account: string, id: string, data: any) => {
  return axios.put(`/api/admin/${account}/integrations/${id}`, data);
};

export const useUpdateIntegration = () => {
  const navigate = useNavigate();
  const toast = useToast();

  return useMutation(
    'updateIntegration',
    async ({ account, id, body }: { account: string; id: string; body: any }) => {
      return await updateIntegration(account, id, body);
    },
    {
      onSuccess: () => {
        navigate('/admin/integrations');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error updating integration',
              extra: JSON.stringify(error.response.data),
              status: 'error',
            });
          },
          isClosable: true,
        });
      },
    }
  );
};
