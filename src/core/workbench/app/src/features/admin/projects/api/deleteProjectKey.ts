import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const deleteProjectKey = (account: string, id: string, key: string) => {
  return axios.delete(`/api/admin/${account}/projects/${id}/keys/${key}`);
};

export const useDeleteProjectKey = () => {
  const toast = useToast();

  return useMutation(
    'deleteProjectKey',
    async ({ account, id, key }: { account: string; id: string; key: string }) => {
      return await deleteProjectKey(account, id, key);
    },
    {
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting project key',
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
