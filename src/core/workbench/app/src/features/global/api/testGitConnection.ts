import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../lib/axios';

type GitConnectionTest = {
  url?: string;
  key_id?: number;
  user_repository_id?: number;
  project_id?: number;
  branch?: string;
  get_dbt_projects?: boolean;
};

export const testGitConnection = (data: GitConnectionTest) => {
  return axios.post(`api/setup/test-git-connection`, data);
};

export const useTestGitConnection = (triggerSuccess: boolean) => {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation(
    'testGitConnection',
    async (data: GitConnectionTest) => {
      return await testGitConnection(data);
    },
    {
      onSuccess: () => {
        if (triggerSuccess) {
          queryClient.invalidateQueries('profileSSHKeys');
          queryClient.invalidateQueries('projects');
          queryClient.invalidateQueries('getUserInfo');
          toast({
            render: () => {
              return createElement(ExpandibleToast, {
                message: 'Connection to the Git Repository was successful.',
                status: 'success',
              });
            },
            isClosable: true,
          });
        }
      },
      onError: (error: { response?: { data?: { message?: string; extra?: string } } }) => {
        const defaultMessage = 'Git repo could not be cloned.';
        const defaultExtraMessage =
          'Please check that repository and branch exist, and your SSH key was properly configured.';
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: error?.response?.data?.message || defaultMessage,
              extra: error?.response?.data?.extra || defaultExtraMessage,
              status: 'error',
            });
          },
          isClosable: true,
        });
      },
    }
  );
};
