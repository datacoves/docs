import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const deleteEnvironmentKey = (account: string, id: string, key: string) => {
  return axios.delete(`/api/admin/${account}/environments/${id}/keys/${key}`);
};

export const useDeleteEnvironmentKey = () => {
  const toast = useToast();

  return useMutation(
    'deleteEnvironmentKey',
    async ({ account, id, key }: { account: string; id: string; key: string }) => {
      return await deleteEnvironmentKey(account, id, key);
    },
    {
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting environment key',
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
