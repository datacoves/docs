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
  Table,
  Thead,
  Tr,
  Th,
  Tbody,
  Flex,
} from '@chakra-ui/react';
import React, { useContext, useEffect, useState, createElement } from 'react';

import ExpandibleToast from '../../../components/ExpandibleToast/ExpandibleToast';
import { HeadingGroup } from '../../../components/ProfileForm/HeadingGroup';
import { UserContext } from '../../../context/UserContext';
import { useCreateProfileSSHKeys, useCreateProfileRSASSHKeys } from '../api/createProfileSSHKeys';
import { useProfileSSHKeysList } from '../api/getProfileSSHKeysList';
import { UserRepository, UserSSHKey } from '../types';

import { DeleteProfileSSHKey } from './DeleteProfileSSHKey';
import { ProfileAddSSHKeysMenu } from './ProfileAddSSHKeysMenu';
import { ProfileSSHKeyRepo } from './ProfileSSHKeyRepo';
export const ProfileSSHKeys = () => {
  const { data: userSSHKeys, isSuccess: userSSHKeysSuccess } = useProfileSSHKeysList();
  const [valueToCopy, setValueToCopy] = useState('');
  const toast = useToast();
  const { currentUser } = useContext(UserContext);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(valueToCopy);
    toast({
      render: () => {
        return createElement(ExpandibleToast, {
          message: 'SSH key copied to clipboard',
          status: 'success',
        });
      },
      duration: 3000,
      isClosable: true,
    });
  };
  const createMutation = useCreateProfileSSHKeys(undefined);
  const createRsaMutation = useCreateProfileRSASSHKeys(undefined);

  const handleGenerate = (keyType?: string) => {
    if (keyType == 'rsa') {
      createRsaMutation.mutate(undefined);
    } else {
      createMutation.mutate(undefined);
    }
  };

  useEffect(() => {
    if (userSSHKeysSuccess && userSSHKeys && userSSHKeys.length > 0) {
      setValueToCopy(userSSHKeys[0].public);
    }
  }, [userSSHKeysSuccess, userSSHKeys]);

  const filterSSHKeysByUser = () =>
    (userSSHKeys || []).filter(({ repos }) => filterReposByUser(repos));

  const filterReposByUser = (repos: UserRepository[]) =>
    repos.filter(({ url }) =>
      (currentUser?.projects || []).find(({ repository }) => repository.git_url == url)
    );

  return (
    <Stack as="section" spacing="6">
      <HStack>
        <HeadingGroup
          title="Git SSH Keys"
          description="Add this SSH key to your git server account to clone your repos."
          flexGrow="1"
        />
        <Menu>
          <MenuButton
            as={Button}
            size="sm"
            colorScheme="blue"
            rightIcon={<ChevronDownIcon />}
            isDisabled={
              (userSSHKeysSuccess && userSSHKeys && userSSHKeys.length > 0) ||
              createMutation.isLoading
            }
            isLoading={createMutation.isLoading}
          >
            Add
          </MenuButton>
          <ProfileAddSSHKeysMenu handleGenerate={handleGenerate} />
        </Menu>
      </HStack>
      <Stack spacing="5" pt="8">
        {userSSHKeysSuccess && userSSHKeys && userSSHKeys.length === 0 && (
          <Text>No keys created yet.</Text>
        )}
        {userSSHKeysSuccess &&
          userSSHKeys &&
          filterSSHKeysByUser().map((ssh_key: UserSSHKey) => (
            <Box key={ssh_key.id}>
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
                  onClick={copyToClipboard}
                >
                  COPY
                </Button>
              </Stack>
              <FormLabel htmlFor={`key-${ssh_key.id}`}>Public key ({ssh_key.key_type})</FormLabel>
              <Textarea
                name={`key-${ssh_key.id}`}
                isReadOnly={true}
                value={ssh_key.public}
                zIndex={1}
              />
              <Flex w="full" justifyContent="flex-end">
                <DeleteProfileSSHKey id={ssh_key.id} />
              </Flex>
              <FormLabel mt="4" fontWeight="bold">
                Repositories
              </FormLabel>
              <Table mb="8" borderWidth="1px" fontSize="sm">
                <Thead>
                  <Tr>
                    <Th>URL</Th>
                    <Th />
                  </Tr>
                </Thead>
                <Tbody>
                  {filterReposByUser(ssh_key.repos)
                    .sort((a, b) => (a.url > b.url ? 1 : -1))
                    .map((repo: UserRepository, id: number) => (
                      <ProfileSSHKeyRepo repo={repo} key={id} />
                    ))}
                </Tbody>
              </Table>
            </Box>
          ))}
      </Stack>
    </Stack>
  );
};
