import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const deleteInvitation = (account: string, id: string) => {
  return axios.delete(`/api/admin/${account}/invitations/${id}`);
};

export const useDeleteInvitation = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation(
    'deleteInvitation',
    async ({ account, id }: { account: string; id: string }) => {
      return await deleteInvitation(account, id);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('invitations');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting invitation',
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
