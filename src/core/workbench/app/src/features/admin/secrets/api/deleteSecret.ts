import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const deleteSecrets = (account: string, id: string) => {
  return axios.delete(`/api/admin/${account}/secrets/${id}`);
};

export const useDeleteSecrets = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation(
    'deleteSecrets',
    async ({ account, id }: { account: string; id: string }) => {
      return await deleteSecrets(account, id);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('secrets');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting secret',
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
