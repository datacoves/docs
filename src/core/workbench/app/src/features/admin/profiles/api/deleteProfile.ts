import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const deleteProfiles = (account: string, id: string) => {
  return axios.delete(`/api/admin/${account}/profiles/${id}`);
};

export const useDeleteProfiles = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation(
    'deleteProfile',
    async ({ account, id }: { account: string; id: string }) => {
      return await deleteProfiles(account, id);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('profiles');
        queryClient.invalidateQueries('getUserInfo');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting profile',
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
