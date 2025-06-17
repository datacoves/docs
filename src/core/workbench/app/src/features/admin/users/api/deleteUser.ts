import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const deleteUser = (account: string, id: string) => {
  return axios.delete(`/api/admin/${account}/users/${id}`);
};

export const useDeleteUser = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation(
    'deleteUser',
    async ({ account, id }: { account: string; id: string }) => {
      return await deleteUser(account, id);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('users');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting user',
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
