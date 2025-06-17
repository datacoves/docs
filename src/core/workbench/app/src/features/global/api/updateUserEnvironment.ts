import { useToast } from '@chakra-ui/toast';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../lib/axios';

export const updateUserEnvironmentVariables = (id: string, data: any) => {
  return axios.put(`api/iam/profile/user-environment/${id}/variables`, data);
};

export const useUpdateUserEnvironmentVariables = (envSlug: string) => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation(
    'updateUserEnvironmentVariables',
    async ({ id, body }: { id: string; body: any }) => {
      return await updateUserEnvironmentVariables(id, body);
    },
    {
      onSuccess: () => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: `VS Code environment variables on environemnt ${envSlug} updated successfully`,
              status: 'success',
            });
          },
          isClosable: true,
        });
        queryClient.invalidateQueries('getUserInfo');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error updating VS Code environment variables',
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
