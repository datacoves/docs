import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation } from 'react-query';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../lib/axios';
export const deleteProfile = () => {
  return axios.delete(`/api/iam/profile`);
};

export const useDeleteProfile = () => {
  const toast = useToast();
  const waitFor = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  return useMutation(
    'deleteProfile',
    async () => {
      return await deleteProfile();
    },
    {
      onSuccess: () => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Profile deleted successfully',
              status: 'success',
            });
          },
          isClosable: true,
        });
        waitFor(500).then(() => (window.location.href = 'https://datacoves.com'));
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error deleting profile',
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
