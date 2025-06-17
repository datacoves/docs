import { ExternalLinkIcon, WarningIcon } from '@chakra-ui/icons';
import { Box, Stack, StackDivider, Button, HStack, VStack, Text, Link } from '@chakra-ui/react';
import { Formik, Form } from 'formik';
import { SelectControl, InputControl, SwitchControl } from 'formik-chakra-ui';
import React, { useContext, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';

import { BasePage } from '../../../../components/AdminLayout';
import { FieldGroup } from '../../../../components/FieldGroup';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { Project, Template } from '../../../../context/UserContext/types';
import { useConnectionTypes } from '../../../global/api/getAccountConnectionTypes';
import { ConnectionTemplate, ConnectionType } from '../../../global/types';
import { useAllProjects } from '../../projects/api/getProjects';
import { useAllTemplates } from '../../templates/api/getTemplates';
import { useCreateConnectionTemplate } from '../api/createConnectionTemplate';
import { useConnectionTemplate } from '../api/getConnectionTemplateById';
import { useUpdateConnectionTemplate } from '../api/updateConnectionTemplate';

export const ConnectionTemplateFormPage = () => {
  const { id } = useParams();
  const isCreateMode = id === undefined;
  const { currentAccount } = useContext(AccountContext);
  const [currentType, setCurrentType] = useState<ConnectionType>();
  const [currentConnectionUser, setCurrentConnectionUser] = useState<string>();
  const [currentForUsers, setCurrentForUsers] = useState<boolean>();
  const {
    data: connectionTypes,
    isSuccess: connectionTypesSuccess,
    isLoading: isLoadingConnectionTypes,
  } = useConnectionTypes({
    account: currentAccount?.slug,
  });

  const initialValues = {
    name: '',
    project: '',
    type: '',
    connection_user: 'provided',
    for_users: false,
  };

  const {
    data: projects,
    isSuccess: projectsSuccess,
    isLoading: isLoadingProjects,
  } = useAllProjects({
    account: currentAccount?.slug,
  });

  const {
    data: templates,
    isSuccess: templatesSuccess,
    isLoading: isLoadingTemplates,
  } = useAllTemplates({
    account: currentAccount?.slug,
    contextType: 'user',
    enabled_for: 'ConnectionTemplate',
  });

  const createMutation = useCreateConnectionTemplate();
  const updateMutation = useUpdateConnectionTemplate();
  const handleSubmit = (body: any, { resetForm }: any) => {
    if (currentAccount?.slug !== undefined) {
      if (body.connection_details) {
        if (currentType?.slug === 'snowflake') {
          body.connection_details = {
            account: body.connection_details.account,
            database: body.connection_details.database,
            warehouse: body.connection_details.warehouse,
            role: body.connection_details.role,
            mfa_protected: body.connection_details.mfa_protected || false,
          };
        }
        if (currentType?.slug === 'redshift') {
          body.connection_details = {
            host: body.connection_details.host,
            database: body.connection_details.database,
          };
        }
        if (currentType?.slug === 'bigquery') {
          body.connection_details = {
            dataset: body.connection_details.dataset,
          };
        }
        if (currentType?.slug === 'databricks') {
          body.connection_details = {
            host: body.connection_details.host,
            schema: body.connection_details.schema,
            http_path: body.connection_details.http_path,
          };
        }
      }

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
    resetForm();
  };
  const handleSelectType = (event: any) => {
    const connection = connectionTypes?.find(
      (type) => parseInt(type.id) === parseInt(event.target.value)
    );
    setCurrentType(connection);
  };
  const handleSelectConnectionUser = (event: any) => {
    setCurrentConnectionUser(event.target.value);
  };
  const handleSelectForUsers = (event: any) => {
    // This is triggered before value is actually changed
    setCurrentForUsers(event.target.value !== 'true');
  };
  const navigate = useNavigate();

  return (
    <BasePage header={isCreateMode ? 'Create connection template' : 'Edit connection template'}>
      <Box px={{ base: '4', md: '10' }} py="16" maxWidth="4xl" mx="auto">
        <Stack spacing="4" divider={<StackDivider />}>
          <Formik
            key={id}
            initialValues={initialValues}
            validationSchema={Yup.object({
              name: Yup.string().required('Required'),
              project: Yup.string().required('Required'),
              type: Yup.string().required('Required'),
              connection_user: Yup.string().when({
                is: () => currentForUsers,
                then: Yup.string().required('Required'),
                otherwise: Yup.string(),
              }),
              connection_user_template: Yup.string().when({
                is: () => currentForUsers && currentConnectionUser === 'template',
                then: Yup.string().required('Required'),
                otherwise: Yup.string().nullable(),
              }),
              connection_details: Yup.object().when({
                is: () => currentType?.slug === 'snowflake',
                then: Yup.object().shape({
                  account: Yup.string().matches(
                    /^(?!.*\.(?!privatelink$)).*$/,
                    'Accounts must not contain a period. Try a dash instead.'
                  ),
                }),
                otherwise: Yup.object().shape({}),
              }),
            })}
            onSubmit={handleSubmit}
          >
            {function Render({ setFieldValue }) {
              const { data, isSuccess, isLoading } = useConnectionTemplate(
                currentAccount?.slug,
                id,
                {
                  enabled:
                    currentAccount?.slug !== undefined &&
                    id !== undefined &&
                    connectionTypesSuccess,
                  onSuccess: (data: ConnectionTemplate) => {
                    setFieldValue('name', data.name);
                    setFieldValue('project', data.project);
                    setFieldValue('type', data.type);
                    const type = connectionTypes?.find(
                      (type) => parseInt(type.id) === parseInt(data.type)
                    );
                    setCurrentType(type);
                    setFieldValue('for_users', data.for_users);
                    setCurrentForUsers(data.for_users);
                    setFieldValue('connection_user', data.connection_user);
                    setCurrentConnectionUser(data.connection_user);
                    setFieldValue('connection_user_template', data.connection_user_template);
                    setFieldValue('connection_details.account', data.connection_details.account);
                    setFieldValue(
                      'connection_details.warehouse',
                      data.connection_details.warehouse
                    );
                    setFieldValue('connection_details.database', data.connection_details.database);
                    setFieldValue('connection_details.host', data.connection_details.host);
                    setFieldValue('connection_details.role', data.connection_details.role);
                    setFieldValue(
                      'connection_details.http_path',
                      data.connection_details.http_path
                    );
                    setFieldValue('connection_details.schema', data.connection_details.schema);
                    setFieldValue('connection_details.dataset', data.connection_details.dataset);
                    setFieldValue(
                      'connection_details.mfa_protected',
                      data.connection_details.mfa_protected
                    );
                  },
                }
              );
              return (
                <LoadingWrapper
                  isLoading={
                    (!isCreateMode && isLoading) ||
                    isLoadingConnectionTypes ||
                    isLoadingProjects ||
                    isLoadingTemplates
                  }
                  showElements={
                    (isCreateMode || (data && isSuccess)) &&
                    connectionTypesSuccess &&
                    projectsSuccess &&
                    templatesSuccess
                  }
                >
                  <Form>
                    <FieldGroup title="Basic Info">
                      <VStack width="full" spacing="6">
                        <Box w="full">
                          <InputControl name="name" label="Name" isRequired />
                          <Text color="gray.500" mt={1} fontSize="xs">
                            This is the identifier displayed when you use it in your services and
                            user settings.
                          </Text>
                        </Box>
                        <SelectControl
                          label="Project"
                          name="project"
                          selectProps={{ placeholder: 'Select project' }}
                          isRequired
                        >
                          {projects?.map((project: Project) => {
                            return (
                              <option key={`projects.${project.id}`} value={project.id}>
                                {project.name}
                              </option>
                            );
                          })}
                        </SelectControl>
                        <SelectControl
                          label="Type"
                          name="type"
                          selectProps={{ placeholder: 'Select type' }}
                          onChange={handleSelectType}
                          isRequired
                        >
                          {connectionTypes?.map((type: ConnectionType) => {
                            return (
                              <option key={`connectiontypes.${type.id}`} value={type.id}>
                                {type.name}
                              </option>
                            );
                          })}
                        </SelectControl>
                      </VStack>
                    </FieldGroup>
                    <FieldGroup title="Template Usage">
                      <VStack width="full" spacing="6">
                        <Box w="full">
                          <HStack>
                            <SwitchControl
                              name="for_users"
                              label="Enabled for users"
                              onChange={handleSelectForUsers}
                            />
                            {!currentForUsers &&
                              !isCreateMode &&
                              data?.for_users &&
                              data?.user_credentials_count !== 0 && (
                                <HStack>
                                  <WarningIcon color="red.500" />
                                  <Text fontSize="xs">{`This action will delete ${
                                    data?.user_credentials_count
                                  } user ${
                                    data?.user_credentials_count === 1
                                      ? 'connection'
                                      : 'connections'
                                  }`}</Text>
                                </HStack>
                              )}
                          </HStack>
                          <Text color="gray.500" mt={1} fontSize="xs">
                            When enabled, the connection template can be selected by users when they
                            configure DB connections.
                          </Text>
                        </Box>
                        {currentForUsers && currentType && currentType.slug === 'snowflake' && (
                          <>
                            <Box w="full">
                              <SwitchControl
                                name="connection_details.mfa_protected"
                                label="Is MFA protected"
                              />
                              <Text color="gray.500" mt={1} fontSize="xs">
                                Make sure to{' '}
                                <Link
                                  target="_blank"
                                  color="blue.500"
                                  href="https://docs.snowflake.com/en/user-guide/security-mfa#using-mfa-token-caching-to-minimize-the-number-of-prompts-during-authentication-optional"
                                >
                                  enable Snowflake MFA caching <ExternalLinkIcon />
                                </Link>{' '}
                                for a smoother experience
                              </Text>
                            </Box>
                            <SelectControl
                              label="User field configuration"
                              name="connection_user"
                              onChange={handleSelectConnectionUser}
                              isRequired
                            >
                              <option value="template">Custom template</option>
                              <option value="email">Email</option>
                              <option value="email_uppercase">Email (uppercase)</option>
                              <option value="provided">Provided by user</option>
                              <option value="email_username">Username from email</option>
                            </SelectControl>
                          </>
                        )}
                        {currentForUsers &&
                          currentConnectionUser === 'template' &&
                          currentType &&
                          currentType.slug === 'snowflake' && (
                            <SelectControl
                              label="Template"
                              name="connection_user_template"
                              selectProps={{ placeholder: 'Select template' }}
                              isRequired
                            >
                              {templates?.map((template: Template) => {
                                return (
                                  <option key={`templates.${template.id}`} value={template.id}>
                                    {template.name}
                                  </option>
                                );
                              })}
                            </SelectControl>
                          )}
                      </VStack>
                    </FieldGroup>
                    {currentType && currentType.slug === 'snowflake' && (
                      <FieldGroup title="Default values">
                        <VStack w="full">
                          <HStack spacing="8" alignItems="flex-start" w="full">
                            <InputControl name="connection_details.account" label="Account" />
                            <InputControl name="connection_details.warehouse" label="Warehouse" />
                          </HStack>
                          <HStack spacing="8" alignItems="flex-start" w="full">
                            <InputControl name="connection_details.database" label="Database" />
                            <InputControl name="connection_details.role" label="Role" />
                          </HStack>
                        </VStack>
                      </FieldGroup>
                    )}
                    {currentType && currentType.slug === 'redshift' && (
                      <FieldGroup title="Default values">
                        <VStack w="full">
                          <InputControl name="connection_details.host" label="Host" />
                          <InputControl name="connection_details.database" label="Database" />
                        </VStack>
                      </FieldGroup>
                    )}
                    {currentType && currentType.slug === 'databricks' && (
                      <FieldGroup title="Default values">
                        <VStack w="full">
                          <HStack spacing="8" alignItems="flex-start" w="full">
                            <InputControl name="connection_details.host" label="Host" />
                            <InputControl name="connection_details.schema" label="Schema" />
                          </HStack>
                          <HStack spacing="8" alignItems="flex-start" w="full">
                            <InputControl name="connection_details.http_path" label="HTTP Path" />
                          </HStack>
                        </VStack>
                      </FieldGroup>
                    )}
                    {currentType && currentType.slug === 'bigquery' && (
                      <FieldGroup title="Default values">
                        <VStack w="full">
                          <InputControl name="connection_details.dataset" label="Dataset" />
                        </VStack>
                      </FieldGroup>
                    )}
                    <FieldGroup>
                      <HStack width="full" justifyContent="flex-end" spacing="6">
                        <Button onClick={() => navigate('/admin/connection-templates')}>
                          Cancel
                        </Button>
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
