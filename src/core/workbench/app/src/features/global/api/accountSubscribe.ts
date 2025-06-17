import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../lib/axios';

export const accountSubscribe = (data: any) => {
  return axios.post(`api/billing/subscribe`, data);
};

export const useAccountSubscribe = () => {
  const toast = useToast();
  return useMutation(
    'accountSubscribe',
    async ({ body }: { body: any }) => {
      return await accountSubscribe(body);
    },
    {
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error creating account subscription',
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
