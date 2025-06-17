import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';
import { useNavigate } from 'react-router-dom';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const createConnectionTemplate = (account: string, data: any) => {
  return axios.post(`/api/admin/${account}/connectiontemplates`, data);
};

export const useCreateConnectionTemplate = () => {
  const navigate = useNavigate();
  const toast = useToast();

  return useMutation(
    'createConnectionTemplate',
    async ({ account, body }: { account: string; body: any }) => {
      return await createConnectionTemplate(account, body);
    },
    {
      onSuccess: () => {
        navigate('/admin/connection-templates');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error creating connection template',
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
