import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../lib/axios';

export const testDbConnection = (data: any) => {
  return axios.post(`api/setup/test-db-connection`, data);
};

export const useTestDbConnection = () => {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation(
    'testDbConnection',
    async ({ body }: { body: any }) => {
      return await testDbConnection(body);
    },
    {
      onSuccess: () => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Connection to the Data Warehouse was successful.',
              status: 'success',
            });
          },
          isClosable: true,
        });
        queryClient.invalidateQueries('profileCredentials');
        queryClient.invalidateQueries('serviceCredentials');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error testing Data Warehouse connection',
              extra: JSON.stringify(error.response.data),
              status: 'error',
            });
          },
          isClosable: true,
        });
        queryClient.invalidateQueries('profileCredentials');
        queryClient.invalidateQueries('serviceCredentials');
      },
    }
  );
};
