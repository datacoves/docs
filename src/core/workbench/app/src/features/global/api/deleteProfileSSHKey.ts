import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../lib/axios';

export const deleteProfileSSHKey = (id: string) => {
  return axios.delete(`/api/iam/profile/ssh-keys/${id}`);
};

export const useDeleteProfileSSHKey = () => {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation(
    'deleteProfileSSHKey',
    async (id: string) => {
      return await deleteProfileSSHKey(id);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('profileSSHKeys');
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'SSH Key successfully deleted.',
              status: 'success',
            });
          },
          isClosable: true,
        });
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting SSH Key.',
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
