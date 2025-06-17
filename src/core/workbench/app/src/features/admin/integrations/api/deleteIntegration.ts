import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const deleteIntegrations = (account: string, id: string) => {
  return axios.delete(`/api/admin/${account}/integrations/${id}`);
};

export const useDeleteIntegrations = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation(
    'deleteIntegrations',
    async ({ account, id }: { account: string; id: string }) => {
      return await deleteIntegrations(account, id);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('integrations');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting integration',
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
