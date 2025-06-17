import { useToast } from '@chakra-ui/react';
import { createElement, useContext } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { AccountContext } from '../../../context/AccountContext';
import { Account } from '../../../context/AccountContext/types';
import { axios } from '../../../lib/axios';

export const accountSetup = (data: any) => {
  return axios.post(`api/accounts/setup`, data);
};

export const useAccountSetup = () => {
  const toast = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { setCurrentAccount } = useContext(AccountContext);
  return useMutation(
    'accountSetup',
    async ({ body }: { body: any }) => {
      const { data } = await accountSetup(body);
      const account: Account = data;
      setCurrentAccount(account);
      return data;
    },
    {
      onSuccess: () => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Account Created',
              extra: 'Account created successfully.',
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
              message: 'Error Setting Account',
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
