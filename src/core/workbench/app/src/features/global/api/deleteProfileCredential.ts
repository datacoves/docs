import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../lib/axios';

export const deleteProfileCredential = (id: string) => {
  return axios.delete(`api/iam/profile/credentials/${id}`);
};

export const useDeleteProfileCredential = () => {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation(
    'deleteProfileCredential ',
    async ({ id }: { id: string }) => {
      return await deleteProfileCredential(id);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('profileCredentials');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting Profile Credential',
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
