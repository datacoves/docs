import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../lib/axios';
import { UserSSLKey } from '../types';

export const createProfileSSLKeys = (privateKey?: string): Promise<UserSSLKey[]> => {
  const data = privateKey === undefined ? undefined : { private: privateKey };
  return axios.post(`api/iam/profile/ssl-keys`, data);
};

export const useCreateProfileSSLKeys = (onSuccess: (() => void) | undefined) => {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation(
    'createProfileSSLKeys',
    async (privateKey?: string) => {
      return await createProfileSSLKeys(privateKey);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('profileSSLKeys');
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'SSL key pairs successfully created',
              status: 'success',
            });
          },
          isClosable: true,
        });
        onSuccess?.();
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error Creating SSL key pairs',
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
