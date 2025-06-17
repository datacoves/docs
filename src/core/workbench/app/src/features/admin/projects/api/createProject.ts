import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const createProject = (account: string, data: any) => {
  return axios.post(`/api/admin/${account}/projects`, data);
};

export const useCreateProject = () => {
  const toast = useToast();

  return useMutation(
    'createProject',
    async ({ account, body }: { account: string; body: any }) => {
      return await createProject(account, body);
    },
    {
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error creating project',
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
