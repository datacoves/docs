import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';
import { useNavigate } from 'react-router-dom';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const updateUser = (account: string, id: string, data: any) => {
  return axios.put(`/api/admin/${account}/users/${id}`, data);
};

export const useUpdateUser = () => {
  const navigate = useNavigate();
  const toast = useToast();

  return useMutation(
    'updateUser',
    async ({ account, id, body }: { account: string; id: string; body: any }) => {
      return await updateUser(account, id, body);
    },
    {
      onSuccess: () => {
        navigate('/admin/users');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error updating user',
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
