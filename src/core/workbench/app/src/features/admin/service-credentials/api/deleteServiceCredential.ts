import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const deleteServiceCredentials = (account: string, id: string) => {
  return axios.delete(`/api/admin/${account}/servicecredentials/${id}`);
};

export const useDeleteServiceCredentials = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation(
    'deleteServiceCredentials',
    async ({ account, id }: { account: string; id: string }) => {
      return await deleteServiceCredentials(account, id);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('serviceCredentials');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting Service Connection',
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
