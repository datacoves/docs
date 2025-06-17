import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../lib/axios';

export const createProfileCredential = (id: string, data: any) => {
  return axios.post(`api/iam/profile/credentials?environment=${id}`, data);
};

export const useCreateProfileCredential = () => {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation(
    'createProfileCredential',
    async ({ environmentId, body }: { environmentId: string; body: any }) => {
      return await createProfileCredential(environmentId, body);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('profileCredentials');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error creating database connection',
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
