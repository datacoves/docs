import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const createServiceCredential = (account: string, data: any) => {
  return axios.post(`/api/admin/${account}/servicecredentials`, data);
};

export const useCreateServiceCredential = () => {
  const toast = useToast();

  return useMutation(
    'createServiceCredential',
    async ({ account, body }: { account: string; body: any }) => {
      return await createServiceCredential(account, body);
    },
    {
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error creating Service Connection',
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
