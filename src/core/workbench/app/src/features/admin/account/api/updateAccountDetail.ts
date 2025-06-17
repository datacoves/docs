import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const updateAccountDetail = (account: string, data: any) => {
  return axios.put(`api/admin/${account}/settings`, data);
};

export const useUpdateAccountDetail = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const toast = useToast();

  return useMutation(
    'updateAccountDetail',
    async ({ account, body }: { account: string; body: any }) => {
      return await updateAccountDetail(account, body);
    },
    {
      onSuccess: () => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Account updated successfully',
              status: 'success',
            });
          },
          isClosable: true,
        });
        queryClient.invalidateQueries('getUserAccounts');
        navigate('/launchpad');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error updating account',
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
