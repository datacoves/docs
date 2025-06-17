import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../lib/axios';

export const deleteProfileSSLKey = (id: string) => {
  return axios.delete(`/api/iam/profile/ssl-keys/${id}`);
};

export const useDeleteProfileSSLKey = () => {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation(
    'deleteProfileSSLKey',
    async (id: string) => {
      return await deleteProfileSSLKey(id);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('profileSSLKeys');
        queryClient.invalidateQueries('profileCredentials');
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'SSL Key successfully deleted.',
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
              message: 'Error deleting SSL Key.',
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
