import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const updateServiceCredential = (account: string, id: string, data: any) => {
  return axios.put(`/api/admin/${account}/servicecredentials/${id}`, data);
};

export const useUpdateServiceCredential = () => {
  const toast = useToast();

  return useMutation(
    'updateServiceCredential',
    async ({ account, id, body }: { account: string; id: string; body: any }) => {
      return await updateServiceCredential(account, id, body);
    },
    {
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error updating Service Connection',
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
