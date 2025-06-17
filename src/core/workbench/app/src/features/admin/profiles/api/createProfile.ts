import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';
import { useNavigate } from 'react-router-dom';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const createProfile = (account: string, data: any) => {
  return axios.post(`/api/admin/${account}/profiles`, data);
};

export const useCreateProfile = () => {
  const navigate = useNavigate();
  const toast = useToast();

  return useMutation(
    'createProfile',
    async ({ account, body }: { account: string; body: any }) => {
      return await createProfile(account, body);
    },
    {
      onSuccess: () => {
        navigate('/admin/profiles');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error creating profile',
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
