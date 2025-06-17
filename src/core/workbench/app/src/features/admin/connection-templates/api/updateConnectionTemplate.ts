import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';
import { useNavigate } from 'react-router-dom';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const updateConnectionTemplate = (account: string, id: string, data: any) => {
  return axios.put(`/api/admin/${account}/connectiontemplates/${id}`, data);
};

export const useUpdateConnectionTemplate = () => {
  const navigate = useNavigate();
  const toast = useToast();

  return useMutation(
    'updateConnectionTemplate',
    async ({ account, id, body }: { account: string; id: string; body: any }) => {
      return await updateConnectionTemplate(account, id, body);
    },
    {
      onSuccess: () => {
        navigate('/admin/connection-templates');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error updating connection template',
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
