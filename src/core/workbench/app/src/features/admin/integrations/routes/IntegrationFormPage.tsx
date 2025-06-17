import { Box, Stack, StackDivider, Button, HStack, VStack, Text, Flex } from '@chakra-ui/react';
import { Formik, Form } from 'formik';
import { SelectControl, InputControl, SwitchControl } from 'formik-chakra-ui';
import React, { useContext, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';

import { BasePage } from '../../../../components/AdminLayout';
import { FieldGroup } from '../../../../components/FieldGroup';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { Integration } from '../../../global/types';
import { useCreateIntegration } from '../api/createIntegration';
import { useIntegration } from '../api/getIntegrationById';
import { useUpdateIntegration } from '../api/updateIntegration';

export const IntegrationFormPage = () => {
  const { id } = useParams();
  const isCreateMode = id === undefined;
  const { currentAccount } = useContext(AccountContext);
  const [currentType, setCurrentType] = useState<string>();
  const [currentServer, setCurrentServer] = useState<string>();

  const initialValues = {
    name: '',
    type: '',
    settings: {
      server: '',
      host: '',
      mail_from: '',
      port: 587,
      user: '',
      password: '',
      ssl: false,
      start_tls: true,
      webhook_url: '',
    },
    is_default: false,
  };

  const createMutation = useCreateIntegration();
  const updateMutation = useUpdateIntegration();
  const handleSubmit = (body: any, { setSubmitting }: any) => {
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
      setSubmitting(false);
    }
  };
  const handleSelectType = (event: any) => {
    setCurrentType(event.target.value);
  };
  const handleSelectServer = (event: any) => {
    setCurrentServer(event.target.value);
  };
  const navigate = useNavigate();

  return (
    <BasePage header={isCreateMode ? 'Create integration' : 'Edit integration'}>
      <Box px={{ base: '4', md: '10' }} py="16" maxWidth="4xl" mx="auto">
        <Stack spacing="4" divider={<StackDivider />}>
          <Formik
            key={id}
            initialValues={initialValues}
            validationSchema={Yup.object({
              name: Yup.string().required('Required'),
              type: Yup.string().required('Required'),
              is_default: Yup.boolean(),
              settings: Yup.object({
                server: Yup.string().when({
                  is: () => currentType === 'smtp',
                  then: Yup.string().required('Required'),
                  otherwise: Yup.string().nullable(),
                }),
                host: Yup.string().when({
                  is: () => currentType === 'smtp' && currentServer === 'custom',
                  then: Yup.string().required('Required'),
                  otherwise: Yup.string().nullable(),
                }),
                mail_from: Yup.string().when({
                  is: () => currentType === 'smtp' && currentServer === 'custom',
                  then: Yup.string().required('Required'),
                  otherwise: Yup.string().nullable(),
                }),
                port: Yup.string().when({
                  is: () => currentType === 'smtp' && currentServer === 'custom',
                  then: Yup.string().required('Required'),
                  otherwise: Yup.string().nullable(),
                }),
                user: Yup.string(),
                password: Yup.string(),
                ssl: Yup.boolean(),
                start_tls: Yup.boolean(),
                webhook_url: Yup.string().when({
                  is: () => currentType === 'msteams' || currentType === 'slack',
                  then: Yup.string().required('Required'),
                  otherwise: Yup.string().nullable(),
                }),
                api_key: Yup.string().when({
                  is: () => currentType === 'slack',
                  then: Yup.string().required('Required'),
                  otherwise: Yup.string().nullable(),
                }),
              }),
            })}
            onSubmit={handleSubmit}
          >
            {function Render({ setFieldValue }) {
              const { data, isSuccess, isLoading } = useIntegration(currentAccount?.slug, id, {
                enabled: currentAccount?.slug !== undefined && id !== undefined,
                onSuccess: (data: Integration) => {
                  setFieldValue('name', data.name);
                  setFieldValue('type', data.type);
                  setFieldValue('is_default', data.is_default);
                  setCurrentType(data.type);
                  if (data.type === 'smtp') {
                    setFieldValue('settings.server', data.settings.server);
                    setCurrentServer(data.settings.server);
                    if (data.settings.server === 'custom') {
                      setFieldValue('settings.host', data.settings.host);
                      setFieldValue('settings.mail_from', data.settings.mail_from);
                      setFieldValue('settings.port', data.settings.port);
                      if (data.settings.ssl !== undefined) {
                        setFieldValue('settings.ssl', data.settings.ssl);
                      }
                      if (data.settings.start_tls !== undefined) {
                        setFieldValue('settings.start_tls', data.settings.start_tls);
                      }
                    }
                  } else if (data.type === 'msteams') {
                    setFieldValue('settings.webhook_url', data.settings.webhook_url);
                  } else if (data.type === 'slack') {
                    setFieldValue('settings.webhook_url', data.settings.webhook_url);
                    setFieldValue('settings.api_key', data.settings.api_key);
                  }

                  if (data.settings.user !== undefined) {
                    setFieldValue('settings.user', data.settings.user);
                  }
                },
              });
              return (
                <LoadingWrapper
                  isLoading={!isCreateMode && isLoading}
                  showElements={isCreateMode || (data && isSuccess)}
                >
                  <Form>
                    <FieldGroup title="Basic Info">
                      <VStack width="full" spacing="6">
                        <Box w="full">
                          <InputControl name="name" label="Name" isRequired />
                          <Text color="gray.500" mt={1} fontSize="xs">
                            This is the identifier displayed when you configure it in your
                            environments.
                          </Text>
                        </Box>
                        <SelectControl
                          label="Type"
                          name="type"
                          selectProps={{ placeholder: 'Select type' }}
                          onChange={handleSelectType}
                          isRequired
                        >
                          <option value="smtp">SMTP</option>
                          <option value="msteams">MS Teams</option>
                          <option value="slack">Slack</option>
                        </SelectControl>
                        <Box w="full">
                          <SwitchControl name="is_default" label="Default" />
                          <Text color="gray.500" mt={1} fontSize="xs">
                            Default integrations will be set to all new Environments.
                          </Text>
                        </Box>
                      </VStack>
                    </FieldGroup>
                    {currentType && currentType === 'smtp' && (
                      <FieldGroup title="Configuration">
                        <VStack w="full">
                          <HStack spacing="8" alignItems="flex-start" w="full">
                            <SelectControl
                              label="SMTP Server"
                              name="settings.server"
                              selectProps={{ placeholder: 'Select SMTP Server' }}
                              onChange={handleSelectServer}
                              isRequired
                            >
                              <option value="datacoves">Datacoves</option>
                              <option value="custom">Custom</option>
                            </SelectControl>
                          </HStack>
                          {currentServer && currentServer === 'custom' && (
                            <>
                              <HStack spacing="8" alignItems="flex-start" w="full">
                                <InputControl name="settings.host" label="Host" isRequired />
                                <InputControl name="settings.port" label="Port" isRequired />
                              </HStack>
                              <HStack spacing="8" alignItems="flex-start" w="full">
                                <InputControl
                                  name="settings.mail_from"
                                  label="From Address"
                                  isRequired
                                />
                              </HStack>
                              <HStack spacing="8" alignItems="flex-start" w="full">
                                <InputControl name="settings.user" label="User" />
                                <InputControl
                                  name="settings.password"
                                  label="Password"
                                  inputProps={{ placeholder: '*******', type: 'password' }}
                                />
                              </HStack>
                              <HStack spacing="8" alignItems="flex-start" w="full">
                                <Flex w="full">
                                  <SwitchControl name="settings.ssl" label="SSL" />
                                </Flex>
                                <Flex w="full">
                                  <SwitchControl name="settings.start_tls" label="Start TLS" />
                                </Flex>
                              </HStack>
                            </>
                          )}
                        </VStack>
                      </FieldGroup>
                    )}
                    {currentType && currentType === 'msteams' && (
                      <FieldGroup title="Configuration">
                        <VStack w="full">
                          <HStack spacing="8" alignItems="flex-start" w="full">
                            <InputControl
                              name="settings.webhook_url"
                              label="Webhook URL"
                              isRequired
                            />
                          </HStack>
                          <HStack spacing="8" alignItems="flex-start" w="full">
                            <InputControl name="settings.user" label="User" />
                            <InputControl
                              name="settings.password"
                              label="Password"
                              inputProps={{ placeholder: '*******', type: 'password' }}
                            />
                          </HStack>
                        </VStack>
                      </FieldGroup>
                    )}

                    {currentType && currentType === 'slack' && (
                      <FieldGroup title="Configuration">
                        <VStack w="full">
                          <HStack spacing="8" alignItems="flex-start" w="full">
                            <InputControl
                              name="settings.webhook_url"
                              label="Webhook URL"
                              isRequired
                            />
                          </HStack>
                          <HStack spacing="8" alignItems="flex-start" w="full">
                            <InputControl
                              name="settings.api_key"
                              label="API Key"
                              inputProps={{ placeholder: '*******', type: 'password' }}
                            />
                          </HStack>
                        </VStack>
                      </FieldGroup>
                    )}

                    <FieldGroup>
                      <HStack width="full" justifyContent="flex-end" spacing="6">
                        <Button onClick={() => navigate('/admin/integrations')}>Cancel</Button>
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
