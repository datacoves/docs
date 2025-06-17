import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';
import { useNavigate } from 'react-router-dom';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const createGroup = (account: string, data: any) => {
  return axios.post(`/api/admin/${account}/groups`, data);
};

export const useCreateGroup = () => {
  const navigate = useNavigate();
  const toast = useToast();

  return useMutation(
    'createGroup',
    async ({ account, body }: { account: string; body: any }) => {
      return await createGroup(account, body);
    },
    {
      onSuccess: () => {
        navigate('/admin/groups');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error creating group',
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
