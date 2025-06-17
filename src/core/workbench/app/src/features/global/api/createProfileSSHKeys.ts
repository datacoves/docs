import { useToast } from '@chakra-ui/react';
import { createElement } from 'react';
import { useMutation, useQueryClient } from 'react-query';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { axios } from '../../../lib/axios';
import { UserSSHKey } from '../types';
export const createProfileSSHKeys = (
  privateKey?: string,
  keyType?: string
): Promise<UserSSHKey[]> => {
  const data = {
    private: privateKey,
    key_type: keyType,
  };

  return axios.post(`api/iam/profile/ssh-keys`, data);
};

export const useCreateProfileSSHKeys = (onSuccess: (() => void) | undefined) => {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation(
    'createProfileSSHKeys',
    async (privateKey?: string) => {
      return await createProfileSSHKeys(privateKey);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('profileSSHKeys');
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'SSH key pairs successfully created',
              status: 'success',
            });
          },
          isClosable: true,
        });
        onSuccess?.();
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error Creating SSH key pairs',
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

/*
 * useMutation / mutate can only take one parameter, my options are to
 * refactor the use of useCreateProfileSSHKeys to take a dictionary
 * or duplicate it for RSA keys.  I'm chosing to duplicate because it is
 * less work and I'm trying to wrap this up.
 *
 * This should be a one-off, I don't imagine we're adding more kinds of
 * SSH anytime soon.  If we do, we should refactor this as part of a larger
 * effort.
 */
export const useCreateProfileRSASSHKeys = (onSuccess: (() => void) | undefined) => {
  const toast = useToast();
  const queryClient = useQueryClient();

  return useMutation(
    'createProfileSSHKeys',
    async (privateKey?: string) => {
      return await createProfileSSHKeys(privateKey, 'rsa');
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('profileSSHKeys');
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'SSH key pairs successfully created',
              status: 'success',
            });
          },
          isClosable: true,
        });
        onSuccess?.();
      },
      onError: (error: any) => {
        toast({
          render: () => {
            return createElement(ExpandibleToast, {
              message: 'Error Creating SSH key pairs',
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
