import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const resendInvitation = (account: string, id: string) => {
  return axios.put(`/api/admin/${account}/invitations/${id}/resend`);
};

export const useResendInvitation = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation(
    'resendInvitation',
    async ({ account, id }: { account: string; id: string }) => {
      return await resendInvitation(account, id);
    },
    {
      onSuccess: () => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Invitation email was sent successfully.',
              status: 'success',
            });
          },
          isClosable: true,
        });
        queryClient.invalidateQueries('invitations');
      },
      onError: (error: any) => {
        const desc = error.response.data.non_field_errors
          ? error.response.data.non_field_errors.toString()
          : error.response.data.toString();
        toast({
          title: 'Error Resending Invitation',
          description: desc,
          status: 'error',
          isClosable: true,
        });
      },
    }
  );
};
