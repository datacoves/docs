import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../../lib/axios';

export const deleteProject = (account: string, id: string) => {
  return axios.delete(`/api/admin/${account}/projects/${id}`);
};

export const useDeleteProject = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation(
    'deleteProject',
    async ({ account, id }: { account: string; id: string }) => {
      return await deleteProject(account, id);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('projects');
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting project',
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
