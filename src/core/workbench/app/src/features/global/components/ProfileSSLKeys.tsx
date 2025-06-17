import { ChevronDownIcon } from '@chakra-ui/icons';
import {
  Stack,
  Textarea,
  Box,
  FormLabel,
  Button,
  useToast,
  HStack,
  Menu,
  MenuButton,
  Text,
  Flex,
} from '@chakra-ui/react';
import { createElement } from 'react';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { HeadingGroup } from '../../../components/ProfileForm/HeadingGroup';
import { useCreateProfileSSLKeys } from '../api/createProfileSSLKeys';
import { useProfileSSLKeysList } from '../api/getProfileSSLKeysList';
import { UserSSLKey } from '../types';

import { DeleteProfileSSLKey } from './DeleteProfileSSLKey';
import { ProfileAddSSLKeysMenu } from './ProfileAddSSLKeysMenu';

export const ProfileSSLKeys = () => {
  const { data: userSSLKeys, isSuccess: userSSLKeysSuccess } = useProfileSSLKeysList();
  const toast = useToast();

  const formatKeyForDisplay = (publicKey: string) => {
    return publicKey.startsWith('--') ? publicKey.split('\n').slice(1, -1).join('') : publicKey;
  };

  const copyToClipboard = (publicKey: string) => {
    const copyKey = formatKeyForDisplay(publicKey);
    navigator.clipboard.writeText(copyKey);
    toast({
      render: () => {
        return createElement(ExpandibleToast, {
          message: 'PEM key copied to clipboard',
          status: 'success',
        });
      },
      duration: 3000,
      isClosable: true,
    });
  };

  const createMutation = useCreateProfileSSLKeys(undefined);
  const handleGenerate = () => {
    createMutation.mutate(undefined);
  };

  return (
    <Stack as="section" spacing="6">
      <HStack>
        <HeadingGroup
          title="Database Authorization Keys"
          description="Add this authorization key to your database account for key-based authentication."
          flexGrow="1"
        />
        <Menu>
          <MenuButton
            as={Button}
            size="sm"
            colorScheme="blue"
            rightIcon={<ChevronDownIcon />}
            isDisabled={createMutation.isLoading}
            isLoading={createMutation.isLoading}
          >
            Add
          </MenuButton>
          <ProfileAddSSLKeysMenu handleGenerate={handleGenerate} />
        </Menu>
      </HStack>
      <Stack spacing="5" pt="8">
        {userSSLKeysSuccess && userSSLKeys && userSSLKeys.length === 0 && (
          <Text>No keys created yet.</Text>
        )}
        {userSSLKeysSuccess &&
          userSSLKeys &&
          userSSLKeys.map((ssl_key: UserSSLKey) => (
            <Box key={ssl_key.id}>
              <Stack
                direction="row"
                justifyContent="flex-end"
                alignItems="center"
                w="full"
                mb={-6}
                zIndex={2}
              >
                <Button
                  colorScheme="green"
                  size="xs"
                  alignSelf="baseline"
                  onClick={() => copyToClipboard(ssl_key.public)}
                >
                  COPY
                </Button>
              </Stack>
              <FormLabel htmlFor={`key-${ssl_key.id}`}>Public key ({ssl_key.key_type})</FormLabel>
              <Textarea
                name={`key-${ssl_key.id}`}
                isReadOnly={true}
                value={formatKeyForDisplay(ssl_key.public)}
                zIndex={1}
                rows={7}
              />
              <Flex w="full" justifyContent="flex-end">
                <DeleteProfileSSLKey id={ssl_key.id} />
              </Flex>
            </Box>
          ))}
      </Stack>
    </Stack>
  );
};
