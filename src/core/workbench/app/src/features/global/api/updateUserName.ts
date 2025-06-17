import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../lib/axios';

export const updateUserName = (data: any) => {
  return axios.put(`api/iam/profile`, data);
};

export const useUpdateUserName = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation(
    'updateUserName',
    async ({ body }: { body: any }) => {
      return await updateUserName(body);
    },
    {
      onSuccess: () => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Name updated successfully',
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
              message: 'Error updating name',
              extra: JSON.stringify(error.response.data),
              status: 'error',
            });
          },
          isClosable: true,
          // title: 'Error Updating Name',
          // description: JSON.stringify(error.response.data),
          // status: 'error',
        });
      },
    }
  );
};
