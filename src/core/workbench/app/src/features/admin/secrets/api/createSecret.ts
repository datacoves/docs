import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';
import { useNavigate } from 'react-router-dom';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const createSecret = (account: string, data: any) => {
  return axios.post(`/api/admin/${account}/secrets`, data);
};

export const useCreateSecret = () => {
  const navigate = useNavigate();
  const toast = useToast();

  return useMutation(
    'createSecret',
    async ({ account, body }: { account: string; body: any }) => {
      return await createSecret(account, body);
    },
    {
      onSuccess: () => {
        navigate('/admin/secrets');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error creating secret',
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
