import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';
import { useNavigate } from 'react-router-dom';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const createIntegration = (account: string, data: any) => {
  return axios.post(`/api/admin/${account}/integrations`, data);
};

export const useCreateIntegration = () => {
  const navigate = useNavigate();
  const toast = useToast();

  return useMutation(
    'createIntegration',
    async ({ account, body }: { account: string; body: any }) => {
      return await createIntegration(account, body);
    },
    {
      onSuccess: () => {
        navigate('/admin/integrations');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error creating integration',
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
