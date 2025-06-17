import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const deleteAccount = (account: string) => {
  return axios.delete(`/api/admin/${account}/settings`);
};

export const useDeleteAccount = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const toast = useToast();
  return useMutation(
    'deleteAccount',
    async ({ account }: { account: string }) => {
      return await deleteAccount(account);
    },
    {
      onSuccess: () => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Account deleted successfully',
              status: 'success',
            });
          },
          isClosable: true,
        });
        queryClient.invalidateQueries('getUserAccounts');
        queryClient.invalidateQueries('getUserInfo');
        navigate('/launchpad');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting account',
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
