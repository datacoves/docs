import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../lib/axios';

export const updateProfileCredential = (id: string, data: any) => {
  return axios.put(`api/iam/profile/credentials/${id}`, data);
};

export const useUpdateProfileCredential = () => {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation(
    'updateProfileCredential ',
    async ({ id, body }: { id: string; body: any }) => {
      return await updateProfileCredential(id, body);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('profileCredentials');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error updating database connection',
              extra: JSON.stringify(error.response.data),
              status: 'error',
            });
          },
        });
      },
    }
  );
};
