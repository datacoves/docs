import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';
import { useNavigate } from 'react-router-dom';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const updateSecret = (account: string, id: string, data: any) => {
  return axios.put(`/api/admin/${account}/secrets/${id}`, data);
};

export const useUpdateSecret = () => {
  const navigate = useNavigate();
  const toast = useToast();

  return useMutation(
    'updateSecret',
    async ({ account, id, body }: { account: string; id: string; body: any }) => {
      return await updateSecret(account, id, body);
    },
    {
      onSuccess: () => {
        navigate('/admin/secrets');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error updating secret',
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
