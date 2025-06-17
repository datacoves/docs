import { DeleteIcon } from '@chakra-ui/icons';
import {
  Box,
  Stack,
  Text,
  StackDivider,
  Button,
  HStack,
  VStack,
  Tabs,
  TabPanels,
  TabPanel,
  Heading,
  Divider,
  Input,
  Select,
  Switch,
  Thead,
  Table,
  Tr,
  Th,
  Tbody,
  Td,
} from '@chakra-ui/react';
import { Formik, Form } from 'formik';
import { InputControl, SwitchControl } from 'formik-chakra-ui';
import React, { useContext, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';

import { BasePage } from '../../../../components/AdminLayout';
import { FormTabs } from '../../../../components/FormTabs';
import { AccountContext } from '../../../../context/AccountContext';
import { Profile, ProfileFile, Template } from '../../../../context/UserContext/types';
import { useAllTemplates } from '../../templates/api/getTemplates';
import { useCreateProfile } from '../api/createProfile';
import { useProfile } from '../api/getProfileById';
import { useUpdateProfile } from '../api/updateProfile';

export const ProfileFormPage = () => {
  const { id } = useParams();
  const isCreateMode = id === undefined;
  const { currentAccount } = useContext(AccountContext);
  const [profileFilesSelected, setProfileFilesSelected] = useState<ProfileFile[]>([]);

  const initialValues = {
    name: '',
    account: null,
    dbt_sync: false,
    dbt_local_docs: false,
    mount_ssl_keys: false,
    mount_ssh_keys: false,
    mount_api_token: false,
    clone_repository: false,
    files_from: null,
    files: [],
  };

  const { data: templates, isSuccess: templatesSuccess } = useAllTemplates({
    account: currentAccount?.slug,
    enabled_for: 'ProfileFile',
  });

  const createMutation = useCreateProfile();
  const updateMutation = useUpdateProfile();

  const handleSubmit = (body: any, { setSubmitting }: any) => {
    body.files = profileFilesSelected;

    if (currentAccount?.slug !== undefined) {
      if (isCreateMode) {
        createMutation.mutate({
          account: currentAccount?.slug,
          body,
        });
      } else {
        updateMutation.mutate({
          account: currentAccount?.slug,
          id,
          body,
        });
      }
    }
    setSubmitting(false);
  };

  const updateProfileFile = (itIndex: number, item: ProfileFile) => {
    setProfileFilesSelected((prevState) => {
      const newState = prevState.map((obj, index) => {
        if (index === itIndex) {
          return item;
        }
        return obj;
      });

      return newState;
    });
  };
  const deleteProfileFile = (itIndex: number) => {
    setProfileFilesSelected((prevState) => {
      return prevState.filter((item, index) => index !== itIndex);
    });
  };

  const navigate = useNavigate();

  return (
    <BasePage header={isCreateMode ? 'Create profile' : 'Edit profile'}>
      <Box p="10" w="full">
        <Stack spacing="4" divider={<StackDivider />}>
          <Formik
            key={id}
            initialValues={initialValues}
            validationSchema={Yup.object({
              name: Yup.string().required('Required'),
              dbt_sync: Yup.boolean().required('Required'),
              dbt_local_docs: Yup.boolean().required('Required'),
              mount_ssl_keys: Yup.boolean().required('Required'),
              mount_ssh_keys: Yup.boolean().required('Required'),
              mount_api_token: Yup.boolean().required('Required'),
              clone_repository: Yup.boolean().required('Required'),
            })}
            onSubmit={handleSubmit}
          >
            {function Render({ setFieldValue }) {
              const { data, isSuccess } = useProfile(currentAccount?.slug, id, {
                enabled: currentAccount?.slug !== undefined && id !== undefined,
                onSuccess: (data: Profile) => {
                  setFieldValue('name', data.name);
                  setFieldValue('dbt_sync', data.dbt_sync);
                  setFieldValue('dbt_local_docs', data.dbt_local_docs);
                  setFieldValue('mount_ssl_keys', data.mount_ssl_keys);
                  setFieldValue('mount_ssh_keys', data.mount_ssh_keys);
                  setFieldValue('mount_api_token', data.mount_api_token);
                  setFieldValue('clone_repository', data.clone_repository);
                  setProfileFilesSelected(data.files);
                },
              });
              return (
                (isCreateMode || (data && isSuccess)) &&
                templatesSuccess && (
                  <Form>
                    <Tabs orientation="vertical">
                      <FormTabs labels={['Basic Information', 'Code Files']} />

                      <TabPanels>
                        <TabPanel pl="16" pr="0">
                          <VStack width="full" spacing="6">
                            <InputControl name="name" label="Name" />
                          </VStack>
                          <VStack spacing="6" alignItems="flex-start">
                            <Divider />
                            <Box>
                              <Heading size="md">dbt</Heading>
                              <Text fontSize="sm">dbt-related profile configurations</Text>
                            </Box>
                            <HStack w="full">
                              <Box flex="1">
                                <SwitchControl name="dbt_sync" label="dbt sync" />
                                <Text fontSize="sm">
                                  Install dbt-core-interface required by datacoves-power-user
                                </Text>
                              </Box>
                              <Box flex="1">
                                <SwitchControl name="dbt_local_docs" label="dbt local docs" />
                                <Text fontSize="sm">Launch local dbt docs web server</Text>
                              </Box>
                            </HStack>
                            <Divider />
                            <Box>
                              <Heading size="md">Mounts</Heading>
                              <Text fontSize="sm">mountable profile configurations</Text>
                            </Box>
                            <HStack w="full">
                              <Box flex="1">
                                <SwitchControl name="mount_ssl_keys" label="SSL" />
                                <Text fontSize="sm">Mount SSL Keys under /config/.ssl/</Text>
                              </Box>
                              <Box flex="1">
                                <SwitchControl name="mount_ssh_keys" label="SSH" />
                                <Text fontSize="sm">Mount SSH Keys under /config/.ssh/</Text>
                              </Box>
                              <Box flex="1">
                                <SwitchControl name="mount_api_token" label="API" />
                                <Text fontSize="sm">Mount API token as environment variable</Text>
                              </Box>
                            </HStack>
                            <Divider />
                            <Box>
                              <Heading size="md">Repository</Heading>
                              <Text fontSize="sm">repository-related configurations</Text>
                            </Box>
                            <HStack w="full">
                              <Box flex="1">
                                <SwitchControl name="clone_repository" label="Clone Repository" />
                                <Text fontSize="sm">
                                  The project git repository gets cloned automatically
                                </Text>
                              </Box>
                            </HStack>
                          </VStack>
                        </TabPanel>
                        {templates && templates.length > 0 && (
                          <TabPanel pl="16" pr="0">
                            <VStack width="full" spacing="6" alignItems="flex-start">
                              {/* <HStack>
                                <Box flex="1">
                                  <Heading size="md">Files From</Heading>
                                  <Text fontSize="sm">
                                    Other Profile from which to extend Code Files.
                                  </Text>
                                  <Select
                                    name="files-from"
                                    value="test"
                                    onChange={(event: any) => {
                                      event;
                                    }}
                                  >
                                    <option value="TODO">TODO</option>
                                  </Select>
                                </Box>
                              </HStack>
                              <Divider /> */}
                              <HStack w="full">
                                <Box flex="1">
                                  <Heading size="md">Code Files</Heading>
                                  <Text fontSize="sm">
                                    Generate files in users code environments using pre-created
                                    Jinja templates
                                  </Text>
                                </Box>
                                <Button
                                  onClick={() =>
                                    setProfileFilesSelected((prevSelected) => [
                                      ...prevSelected,
                                      {
                                        template: templates[0],
                                        mount_path: '',
                                        override_existent: false,
                                        execute: false,
                                      },
                                    ])
                                  }
                                >
                                  + Add New File
                                </Button>
                              </HStack>
                              <Divider />

                              {profileFilesSelected.length === 0 && (
                                <Text>No files configured yet.</Text>
                              )}

                              {profileFilesSelected.length > 0 && (
                                <Table my="8" borderWidth="1px" fontSize="sm">
                                  <Thead>
                                    <Tr>
                                      <Th>Template</Th>
                                      <Th>Mount Path</Th>
                                      <Th>Override Existent</Th>
                                      <Th>Execute</Th>
                                      <Th />
                                    </Tr>
                                  </Thead>
                                  <Tbody>
                                    {profileFilesSelected.map((profileFile: ProfileFile, index) => {
                                      return (
                                        <Tr key={`profileFile.${index}`} w="full">
                                          <Td>
                                            <Select
                                              name={`template-${index}`}
                                              value={profileFile.template.toString()}
                                              onChange={(event: any) => {
                                                profileFile.template = event.target.value;
                                                updateProfileFile(index, profileFile);
                                              }}
                                            >
                                              {templates?.map((template: Template) => {
                                                return (
                                                  <option
                                                    key={`profileFile.${index}.${template}`}
                                                    value={template.id}
                                                  >
                                                    {template.name}
                                                  </option>
                                                );
                                              })}
                                            </Select>
                                          </Td>
                                          <Td>
                                            <Input
                                              name={`mount_path-${index}`}
                                              placeholder="Mount Path"
                                              value={profileFile.mount_path}
                                              onChange={(event: any) => {
                                                profileFile.mount_path = event.target.value;
                                                updateProfileFile(index, profileFile);
                                              }}
                                            />
                                          </Td>

                                          <Td>
                                            <Switch
                                              name={`override_existent-${index}`}
                                              isChecked={profileFile.override_existent}
                                              onChange={(event: any) => {
                                                profileFile.override_existent =
                                                  event.target.checked;
                                                updateProfileFile(index, profileFile);
                                              }}
                                            />
                                          </Td>
                                          <Td>
                                            <Switch
                                              name={`execute-${index}`}
                                              isChecked={profileFile.execute}
                                              onChange={(event: any) => {
                                                profileFile.execute = event.target.checked;
                                                updateProfileFile(index, profileFile);
                                              }}
                                            />
                                          </Td>
                                          <Td>
                                            <Button
                                              variant="ghost"
                                              colorScheme="red"
                                              onClick={() => deleteProfileFile(index)}
                                            >
                                              <DeleteIcon />
                                            </Button>
                                          </Td>
                                        </Tr>
                                      );
                                    })}
                                  </Tbody>
                                </Table>
                              )}
                            </VStack>
                          </TabPanel>
                        )}
                      </TabPanels>
                    </Tabs>
                    <HStack width="full" justifyContent="flex-end" spacing="6" pt="10">
                      <Button onClick={() => navigate('/admin/profiles')}>Cancel</Button>
                      <Button
                        type="submit"
                        colorScheme="blue"
                        isLoading={updateMutation.isLoading || createMutation.isLoading}
                      >
                        Save Changes
                      </Button>
                    </HStack>
                  </Form>
                )
              );
            }}
          </Formik>
        </Stack>
      </Box>
    </BasePage>
  );
};
