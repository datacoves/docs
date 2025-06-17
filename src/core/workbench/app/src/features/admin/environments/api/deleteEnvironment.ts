import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const deleteEnvironments = (account: string, id: string) => {
  return axios.delete(`/api/admin/${account}/environments/${id}`);
};

export const useDeleteEnvironments = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation(
    'deleteEnvironments',
    async ({ account, id }: { account: string; id: string }) => {
      return await deleteEnvironments(account, id);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('environments');
        queryClient.invalidateQueries('getUserInfo');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting environment',
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
