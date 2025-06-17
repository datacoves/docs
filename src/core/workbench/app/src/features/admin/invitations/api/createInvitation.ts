import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';
import { useNavigate } from 'react-router-dom';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const createInvitation = (account: string, data: any) => {
  return axios.post(`/api/admin/${account}/invitations`, data);
};

export const useCreateInvitation = () => {
  const navigate = useNavigate();
  const toast = useToast();

  return useMutation(
    'createInvitation',
    async ({ account, body }: { account: string; body: any }) => {
      return await createInvitation(account, body);
    },
    {
      onSuccess: () => {
        navigate('/admin/invitations');
      },
      onError: (error: any) => {
        const desc = error.response.data.non_field_errors
          ? error.response.data.non_field_errors.toString()
          : error.response.data.toString();
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error creating invitation',
              extra: desc,
              status: 'error',
            });
          },
          isClosable: true,
        });
      },
    }
  );
};
