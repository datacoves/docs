import { DeleteIcon } from '@chakra-ui/icons';
import { Box, Button, Link, Table, Tbody, Td, Tr, Text, VStack, useToast } from '@chakra-ui/react';
import { createElement, useContext, useState } from 'react';
import { useParams } from 'react-router-dom';

import { BasePage } from '../../../../components/AdminLayout';
import { AlertDialog } from '../../../../components/AlertDialog';
import { Card } from '../../../../components/Card';
import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { ProjectKeys } from '../../../../context/UserContext/types';
import { axios } from '../../../../lib/axios';
import { useDeleteProjectKey } from '../api/deleteProjectKey';
import { useProjectKeys } from '../api/getProjectKeys';
import { ProjectKeyBox } from '../components/ProjectKeyBox';

export const ProjectKeysPage = () => {
  const { id } = useParams();
  const { currentAccount } = useContext(AccountContext);

  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [selectedKey, setSelectedKey] = useState<string>();
  const [project, setProject] = useState<ProjectKeys>();
  const [newToken, setNewToken] = useState<string>();
  const [buttonDisabled, setButtonDisabled] = useState<boolean>();

  const onClose = () => setIsConfirmOpen(false);
  const deleteMutation = useDeleteProjectKey();

  const toast = useToast();
  const copyToClipboard = (key: string, value: string | undefined) => {
    if (value) {
      navigator.clipboard.writeText(value);
      toast({
        render: () => {
          return createElement(ExpandibleToast, {
            message: `${key} copied to clipboard`,
            status: 'success',
          });
        },
        duration: 2000,
        isClosable: true,
      });
    }
  };

  const handleDelete = (key: string) => {
    setSelectedKey(key);
    setIsConfirmOpen(true);
  };

  const handleConfirmDelete = () => {
    if (selectedKey && currentAccount && id) {
      deleteMutation.mutate({
        account: currentAccount.slug,
        id: id,
        key: selectedKey,
      });

      // Delete the key from the environment array.  This if statement is for
      // appeasing ultra-pedantic React.
      if (project && project.tokens && project.tokens.length) {
        project.tokens.splice(project.tokens.indexOf(selectedKey), 1);
      }
    }
  };

  const handleNewKeyRequest = async () => {
    setButtonDisabled(true);

    // This should never happen but prevents pedantic React from being pedantic.
    if (currentAccount === undefined || id === undefined) {
      toast({
        render: () => {
          return createElement(ExpandibleToast, {
            message: 'Session expired',
            extra: 'Your session seems to have expired.  Please re-login.',
            status: 'error',
          });
        },
        isClosable: true,
      });

      return;
    }

    try {
      /*
       * I have wrestled with react all day, and this axios.post isn't returning
       * an axios request even though our "compiler" insists it is.  This weird
       * casting fixes the issue.
       */
      const data = (await axios.post(
        `/api/admin/${currentAccount.slug}/projects/${id}/keys`,
        {}
      )) as unknown as ProjectKeys;

      setNewToken(data.new_token);
    } catch (err) {
      toast({
        render: () => {
          return createElement(ExpandibleToast, {
            message: 'Failed to communicate with the backend to make a new key.',
            status: 'error',
          });
        },
        isClosable: true,
      });
    } finally {
      setButtonDisabled(false);
    }
  };

  return (
    <BasePage header="Project Keys">
      <Box px="10" w="full">
        {(function Render() {
          const { data, isSuccess, isLoading } = useProjectKeys(currentAccount?.slug, id, {
            enabled: currentAccount?.slug !== undefined && id !== undefined,
            onSuccess: async (data: ProjectKeys) => {
              setProject(data);
            },
          });

          return (
            <LoadingWrapper isLoading={isLoading} showElements={data && isSuccess}>
              <Text mt={'5'} mb={'10'} textAlign="center">
                For details on how to use DBT API, check out{' '}
                <Link
                  color={'blue.500'}
                  href="https://docs.datacoves.com/how-tos/dbt/api-getting-started.html"
                  target="_blank"
                >
                  Getting Started with DBT API
                </Link>
              </Text>
              <VStack spacing="10" maxWidth="500px" mx="auto">
                <ProjectKeyBox
                  label="DBT API URL"
                  value={project?.dbt_api_url}
                  onCopy={() => copyToClipboard('DBT API URL', project?.dbt_api_url)}
                />
                {newToken && (
                  <Card>
                    <Text mb={'15'}>
                      You have generated a new API key. Please take note of this key, because it
                      will not be shown to you again.
                    </Text>
                    <ProjectKeyBox
                      label="API Key"
                      value={newToken}
                      onCopy={() => copyToClipboard('New API Key', newToken)}
                    />
                  </Card>
                )}
                {!newToken && (
                  <Button
                    colorScheme="blue"
                    onClick={() => handleNewKeyRequest()}
                    disabled={buttonDisabled === true}
                  >
                    Generate New API Key
                  </Button>
                )}
                {project?.tokens?.length && (
                  <Table borderWidth="1px" fontSize="sm" mt={'5 !important'}>
                    <Tbody>
                      {project.tokens.map((token, index) => (
                        <Tr key={index}>
                          <Td whiteSpace="nowrap" key={index} px={2} textAlign="center">
                            {token}...
                          </Td>
                          <Td textAlign="end">
                            <Button
                              onClick={() => handleDelete(token)}
                              variant="ghost"
                              colorScheme="red"
                            >
                              <DeleteIcon />
                            </Button>
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                )}
                <AlertDialog
                  isOpen={isConfirmOpen}
                  header="Delete key"
                  message={`Are you sure that you want to delete ${selectedKey}? You can't undo this action`}
                  confirmLabel="Delete"
                  onClose={onClose}
                  onConfirm={handleConfirmDelete}
                />
              </VStack>
            </LoadingWrapper>
          );
        })()}
      </Box>
    </BasePage>
  );
};
