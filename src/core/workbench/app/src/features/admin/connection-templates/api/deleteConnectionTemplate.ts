import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const deleteConnectionTemplates = (account: string, id: string) => {
  return axios.delete(`/api/admin/${account}/connectiontemplates/${id}`);
};

export const useDeleteConnectionTemplates = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation(
    'deleteConnectionTemplates',
    async ({ account, id }: { account: string; id: string }) => {
      return await deleteConnectionTemplates(account, id);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('connectionTemplates');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting connection template',
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
