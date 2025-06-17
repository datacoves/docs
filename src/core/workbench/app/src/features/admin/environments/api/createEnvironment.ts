import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';
import { useNavigate } from 'react-router-dom';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const createEnvironment = (account: string, data: any) => {
  return axios.post(`/api/admin/${account}/environments`, data);
};

export const useCreateEnvironment = () => {
  const navigate = useNavigate();
  const toast = useToast();

  return useMutation(
    'createEnvironment',
    async ({ account, body }: { account: string; body: any }) => {
      return await createEnvironment(account, body);
    },
    {
      onSuccess: () => {
        navigate('/admin/environments');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error creating environment',
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
