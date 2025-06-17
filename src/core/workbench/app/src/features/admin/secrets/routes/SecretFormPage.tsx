import { InfoIcon, WarningTwoIcon } from '@chakra-ui/icons';
import { Box, Stack, StackDivider, Button, HStack, VStack, Flex, Text } from '@chakra-ui/react';
import { Formik, Form } from 'formik';
import { InputControl, SelectControl, TextareaControl, SwitchControl } from 'formik-chakra-ui';
import { isPlainObject } from 'lodash';
import React, { useContext, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';

import { BasePage } from '../../../../components/AdminLayout';
import { FieldGroup } from '../../../../components/FieldGroup';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { Project, Environment } from '../../../../context/UserContext/types';
import { Secret } from '../../../global/types';
import { useAllEnvironments } from '../../environments/api/getEnvironments';
import { useAllProjects } from '../../projects/api/getProjects';
import { useCreateSecret } from '../api/createSecret';
import { useSecret } from '../api/getSecretById';
import { useUpdateSecret } from '../api/updateSecret';
import { EditSecretValues } from '../components/EditSecretValues';

const isJsonString = (text: string): boolean => {
  try {
    JSON.parse(text);
  } catch (e) {
    return false;
  }
  return true;
};

export const SecretFormPage = () => {
  const { id } = useParams();
  const isCreateMode = id === undefined;
  const { currentAccount } = useContext(AccountContext);
  const [sharingScope, setSharingScope] = useState('project');
  const [valueFormat, setValueFormat] = useState('plain_text');
  const [createdBy, setCreatedBy] = useState('');
  const [usersSharing, setUsersSharing] = useState(false);
  const [servicesSharing, setServicesSharing] = useState(false);

  const initialValues = {
    tags: '',
    slug: '',
    description: '',
    value_format: 'plain_text',
    value: {},
    sharing_scope: 'project',
    project: '',
    environment: '',
    users: false,
    services: false,
  };

  const {
    data: projects,
    isSuccess: projectsSuccess,
    isLoading: isLoadingProjects,
  } = useAllProjects({
    account: currentAccount?.slug,
  });

  const {
    data: environments,
    isSuccess: environmentsSuccess,
    isLoading: isLoadingEnvironments,
  } = useAllEnvironments({
    account: currentAccount?.slug,
  });

  const createMutation = useCreateSecret();
  const updateMutation = useUpdateSecret();
  const handleSubmit = (body: any, { setSubmitting }: any) => {
    const newBody = { ...body };
    newBody.tags = newBody.tags.split(',').filter((x: any) => x);
    if (valueFormat === 'plain_text') {
      newBody.value = { PLAIN_TEXT_VALUE: newBody.plain_text_value };
      delete newBody.plain_text_value;
    }
    if (valueFormat === 'json') {
      newBody.value = JSON.parse(newBody.value as string);
    }
    if (sharingScope === 'environment') {
      newBody.project = environments?.find(
        (environment) => environment.id.toString() === newBody.environment.toString()
      )?.project;
    }
    if (currentAccount?.slug !== undefined) {
      if (isCreateMode) {
        createMutation.mutate({
          account: currentAccount?.slug,
          body: newBody,
        });
      } else {
        updateMutation.mutate({
          account: currentAccount?.slug,
          id,
          body: newBody,
        });
      }
    }
    setSubmitting(false);
  };
  const handleSelectSharingScope = (event: any) => {
    setSharingScope(event.target.value);
  };
  const handleSetUsersSharing = (event: any) => {
    setUsersSharing(event.target.value !== 'true');
  };
  const handleSetServicesSharing = (event: any) => {
    setServicesSharing(event.target.value !== 'true');
  };
  const navigate = useNavigate();

  return (
    <BasePage header={isCreateMode ? 'Create secret' : 'Edit secret'}>
      <Box px={{ base: '4', md: '10' }} py="16" maxWidth="4xl" mx="auto">
        <Stack spacing="4" divider={<StackDivider />}>
          <Formik
            key={id}
            initialValues={initialValues}
            validationSchema={Yup.object({
              slug: Yup.string()
                .required('Required')
                .matches(
                  /^[a-z0-9._-]+$/,
                  'Only lowercase alphanumeric characters, dots (.), dashes (-) and underscores (_) allowed.'
                ),
              description: Yup.string(),
              tags: Yup.string(),
              value_format: Yup.string().required('Required'),
              plain_text_value: Yup.string().when({
                is: () => valueFormat === 'plain_text',
                then: Yup.string().required('Required'),
                otherwise: Yup.string().nullable(),
              }),
              value: Yup.object().when({
                is: () => valueFormat !== 'plain_text',
                then: Yup.object().test('is-json-valid', 'Invalid JSON', (value) =>
                  isPlainObject(value)
                ),
                otherwise: Yup.object().nullable(),
              }),
              sharing_scope: Yup.string().required('Required'),
              project: Yup.string().when({
                is: () => sharingScope === 'project',
                then: Yup.string().required('Required'),
                otherwise: Yup.string().nullable(),
              }),
              environment: Yup.string().when({
                is: () => sharingScope === 'environment',
                then: Yup.string().required('Required'),
                otherwise: Yup.string().nullable(),
              }),
              users: Yup.boolean(),
              services: Yup.boolean(),
            })}
            onSubmit={handleSubmit}
          >
            {function Render({ setFieldValue, values }) {
              const setConvertedValue = (format: string, value: any) => {
                switch (format) {
                  case 'dict':
                    if (isJsonString(value as string)) {
                      setFieldValue('value', JSON.parse(value as string));
                    }
                    break;
                  case 'json':
                    if (isPlainObject(value)) {
                      setFieldValue('value', JSON.stringify(value, null, '\t'));
                    }
                    break;
                }
              };

              const { data, isSuccess, isLoading } = useSecret(currentAccount?.slug, id, {
                enabled: currentAccount?.slug !== undefined && id !== undefined,
                onSuccess: (data: Secret) => {
                  setFieldValue('slug', data.slug);
                  setFieldValue('description', data.description);
                  setFieldValue('tags', data.tags.join());
                  setFieldValue('value_format', data.value_format);
                  setFieldValue('sharing_scope', data.sharing_scope);
                  setSharingScope(data.sharing_scope);
                  setFieldValue('project', data.project);
                  setFieldValue('environment', data.environment);
                  setFieldValue('users', data.users);
                  setUsersSharing(data.users);
                  setFieldValue('services', data.services);
                  setServicesSharing(data.services);
                  setCreatedBy(`${data.created_by_name} (${data.created_by_email})`);
                  setValueFormat(data.value_format);
                  switch (data.value_format) {
                    case 'plain_text':
                      setFieldValue('plain_text_value', data.value['PLAIN_TEXT_VALUE']);
                      break;
                    case 'dict':
                      setFieldValue('value', data.value);
                      break;
                    case 'json':
                      setFieldValue('value', JSON.stringify(data.value, null, '\t'));
                      break;
                  }
                  if ('PLAIN_TEXT_VALUE' in data.value) {
                    delete data.value['PLAIN_TEXT_VALUE'];
                  }
                },
              });

              const handleSelectValueFormat = (event: any) => {
                setValueFormat(event.target.value);
                setConvertedValue(event.target.value, values.value);
              };

              return (
                <LoadingWrapper
                  isLoading={
                    (!isCreateMode && isLoading) || isLoadingProjects || isLoadingEnvironments
                  }
                  showElements={
                    (isCreateMode || (data && isSuccess)) && projectsSuccess && environmentsSuccess
                  }
                >
                  <Form>
                    <FieldGroup title="Basic Info">
                      <VStack width="full" spacing="6">
                        <Box w="full">
                          <InputControl
                            isRequired
                            name="slug"
                            label="Reference Key (slug)"
                          ></InputControl>
                          <Text color="gray.500" mt={1} fontSize="xs">
                            Key used to retrieve the secret value from external services.
                            &quot;datacoves-&quot; will automatically be prefixed to the key if not
                            provided.
                          </Text>
                        </Box>
                        <Box w="full">
                          <TextareaControl name="description" label="Description"></TextareaControl>
                        </Box>
                        <Box w="full">
                          <InputControl name="tags" label="Tags"></InputControl>
                          <Text color="gray.500" mt={1} fontSize="xs">
                            Use comma separated tags to better organize your secrets
                          </Text>
                        </Box>
                        {!isCreateMode && (
                          <Box w="full">
                            <Box fontWeight="medium">Created by</Box>
                            {createdBy}
                          </Box>
                        )}
                      </VStack>
                    </FieldGroup>
                    <FieldGroup title="Value">
                      <VStack width="full" spacing="6">
                        <SelectControl
                          label="Format"
                          name="value_format"
                          selectProps={{ placeholder: 'Select the value type' }}
                          onChange={handleSelectValueFormat}
                          isRequired
                        >
                          <option value="plain_text">Key-Value</option>
                          <option value="dict">Multiple Key-Value pairs</option>
                          <option value="json">Raw JSON</option>
                        </SelectControl>
                        <Box w="full">
                          {valueFormat === 'json' ? (
                            <TextareaControl isRequired name="value" label="Value" />
                          ) : valueFormat === 'plain_text' ? (
                            <InputControl name="plain_text_value" label="Value" isRequired />
                          ) : (
                            <EditSecretValues values={values.value} setFieldValue={setFieldValue} />
                          )}
                          {!isCreateMode && (
                            <Text color="gray.500" mt={1} fontSize="xs">
                              <InfoIcon color="blue.500" /> Secret stored on {data?.backend}
                            </Text>
                          )}
                        </Box>
                      </VStack>
                    </FieldGroup>
                    <FieldGroup title="Sharing">
                      <VStack width="full" spacing="6">
                        <SelectControl
                          label="Scope"
                          name="sharing_scope"
                          selectProps={{ placeholder: 'Select sharing options' }}
                          onChange={handleSelectSharingScope}
                          isRequired
                        >
                          <option value="project">
                            Project (shared within a specific project)
                          </option>
                          <option value="environment">
                            Environment (shared within a specific environment)
                          </option>
                        </SelectControl>
                        {sharingScope === 'project' && (
                          <SelectControl
                            label="Project"
                            name="project"
                            selectProps={{ placeholder: 'Select project' }}
                          >
                            {projects?.map((project: Project) => {
                              return (
                                <option key={`projects.${project.id}`} value={project.id}>
                                  {project.name}
                                </option>
                              );
                            })}
                          </SelectControl>
                        )}
                        {sharingScope === 'environment' && (
                          <SelectControl
                            label="Environment"
                            name="environment"
                            selectProps={{ placeholder: 'Select environment' }}
                          >
                            {environments?.map((environment: Environment) => {
                              return (
                                <option
                                  key={`environments.${environment.id}`}
                                  value={environment.id}
                                >
                                  {environment.name} ({environment.slug})
                                </option>
                              );
                            })}
                          </SelectControl>
                        )}
                        <Flex w="full" flexWrap="wrap">
                          <SwitchControl
                            name="users"
                            label="Share with developers"
                            onChange={handleSetUsersSharing}
                          />
                          <SwitchControl
                            name="services"
                            label="Share with stack services"
                            onChange={handleSetServicesSharing}
                          />
                          <Text color="gray.500" mt={1} fontSize="xs">
                            Share this secret with <b>transform developers</b>, or services (like{' '}
                            <b>Airflow</b> and <b>Airbyte</b>, among others).
                          </Text>
                          <Flex w="full" h="20px">
                            {!usersSharing && !servicesSharing && (
                              <Flex alignItems="center" color="gray.500" mt={1} fontSize="xs">
                                <WarningTwoIcon mr="1" color="orange.500" /> With the current
                                configuration this secret can only be used by the author
                              </Flex>
                            )}
                          </Flex>
                        </Flex>
                      </VStack>
                    </FieldGroup>
                    <FieldGroup>
                      <HStack width="full" justifyContent="flex-end" spacing="6">
                        <Button onClick={() => navigate('/admin/secrets')}>Cancel</Button>
                        <Button
                          type="submit"
                          colorScheme="blue"
                          isLoading={updateMutation.isLoading || createMutation.isLoading}
                        >
                          Save Changes
                        </Button>
                      </HStack>
                    </FieldGroup>
                  </Form>
                </LoadingWrapper>
              );
            }}
          </Formik>
        </Stack>
      </Box>
    </BasePage>
  );
};
