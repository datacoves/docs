import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const deleteGroup = (account: string, id: string) => {
  return axios.delete(`/api/admin/${account}/groups/${id}`);
};

export const useDeleteGroup = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation(
    'deleteGroup',
    async ({ account, id }: { account: string; id: string }) => {
      return await deleteGroup(account, id);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('groups');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting group',
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
