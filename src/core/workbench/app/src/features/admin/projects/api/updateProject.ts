import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const updateProject = (account: string, id: string, data: any) => {
  return axios.put(`/api/admin/${account}/projects/${id}`, data);
};

export const useUpdateProject = () => {
  const toast = useToast();

  return useMutation(
    'updateProject',
    async ({ account, id, body }: { account: string; id: string; body: any }) => {
      return await updateProject(account, id, body);
    },
    {
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error updating project',
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
