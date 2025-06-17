import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const updateEnvironment = (account: string, id: string, data: any) => {
  return axios.put(`/api/admin/${account}/environments/${id}`, data);
};

export const useUpdateEnvironment = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation(
    'updateEnvironment',
    async ({ account, id, body }: { account: string; id: string; body: any }) => {
      return await updateEnvironment(account, id, body);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('getUserInfo');
        navigate('/admin/environments');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error updating environment',
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
