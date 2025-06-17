import { QuestionIcon, ExternalLinkIcon } from '@chakra-ui/icons';
import {
  Box,
  Stack,
  StackDivider,
  Button,
  HStack,
  VStack,
  Text,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverArrow,
  PopoverCloseButton,
  Link,
  PopoverHeader,
  PopoverBody,
  Flex,
  Textarea,
  useToast,
  Tag,
  FormLabel,
} from '@chakra-ui/react';
import { Formik, Form, FormikValues } from 'formik';
import { SelectControl, InputControl, TextareaControl } from 'formik-chakra-ui';
import React, { createElement, useContext, useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';

import { BasePage } from '../../../../components/AdminLayout';
import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { FieldGroup } from '../../../../components/FieldGroup';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { Environment } from '../../../../context/UserContext/types';
import { useAllConnectionTemplates } from '../../../global/api/getAllConnections';
import { useSSLKey } from '../../../global/api/getSslKey';
import { useTestDbConnection } from '../../../global/api/testDbConnection';
import ConnectionMFAWarningAlert from '../../../global/components/ConnectionMFAWarningAlert';
import { RConnectionTemplate, ServiceCredential, SSLKey } from '../../../global/types';
import { useAllEnvironments } from '../../environments/api/getEnvironments';
import { InputWithToggleTwo } from '../../projects';
import { useCreateServiceCredential } from '../api/createServiceCredential';
import { useServiceCredential } from '../api/getServiceCredentialById';
import { useServiceCredentials } from '../api/getServiceCredentials';
import { useUpdateServiceCredential } from '../api/updateServiceCredential';

export const ServiceCredentialFormPage = () => {
  const { id } = useParams();
  const isCreateMode = id === undefined;
  const { currentAccount } = useContext(AccountContext);
  const { data: connectionTemplates, isSuccess: connectionTemplatesSuccess } =
    useAllConnectionTemplates({
      account: currentAccount?.slug,
    });
  const { data: environments, isSuccess: environmentsSuccess } = useAllEnvironments({
    account: currentAccount?.slug,
  });
  const [currentConnectionTemplate, setCurrentConnectionTemplate] = useState<RConnectionTemplate>();
  const [currentSnowflakeAuth, setCurrentSnowflakeAuth] = useState<string>();
  const [currentSSLKey, setCurrentSSLKey] = useState<SSLKey>();
  const [currentEnvironment, setCurrentEnvironment] = useState<Environment>();
  const [currentService, setCurrentService] = useState<string>();
  const [overrideAccount, setOverrideAccount] = useState(false);
  const [overrideWarehouse, setOverrideWarehouse] = useState(false);
  const [overrideDatabase, setOverrideDatabase] = useState(false);
  const [overrideRole, setOverrideRole] = useState(false);
  const [overrideHost, setOverrideHost] = useState(false);
  const [overrideSchema, setOverrideSchema] = useState(false);
  const [overrideHttpPath, setOverrideHttpPath] = useState(false);
  const [overrideDataset, setOverrideDataset] = useState(false);
  const [currentConnectionId, setCurrentConnectionId] = useState<string>();
  const [deliveryMode, setDeliveryMode] = useState<string>();
  const isJsonString = (text: string): boolean => {
    try {
      JSON.parse(text);
    } catch (e) {
      return false;
    }
    return true;
  };

  const initialValues = {
    name: '',
    connection_template: '',
    service: '',
    environment: '',
    account: '',
    accountOverride: '',
    warehouse: '',
    warehouseOverride: '',
    database: '',
    databaseOverride: '',
    role: '',
    roleOverride: '',
    host: '',
    hostOverride: '',
    user: '',
    schema: '',
    token: '',
    schemaOverride: '',
    httpPathOverride: '',
    dataset: '',
    datasetOverride: '',
    keyfile_json: '',
    delivery_mode: 'connection',
  };

  const toast = useToast();

  useSSLKey('snowflake', {
    enabled: currentSSLKey === undefined && currentSnowflakeAuth === 'key-pair',
    onSuccess: (key: SSLKey) => {
      setCurrentSSLKey(key);
    },
  });

  const handleSelectConnectionTemplate = (event: any) => {
    const connectionTemplate = connectionTemplates?.find(
      (conn) => parseInt(conn.id) === parseInt(event.target.value)
    );
    setCurrentConnectionTemplate(connectionTemplate);
  };
  const handleSelectService = (event: any) => {
    setCurrentService(event.target.value);
  };
  const handleSelectEnvironment = (event: any) => {
    const env = environments?.find((env) => parseInt(env.id) === parseInt(event.target.value));
    setCurrentEnvironment(env);
  };
  const handleClose = () => {
    setCurrentConnectionTemplate(undefined);
    navigate('/admin/service-connections');
  };

  const handleSelectAuthenticationSnowflake = (event: any) => {
    setCurrentSnowflakeAuth(event.target.value);
  };

  const handleSelectDeliveryMode = (event: any) => {
    setDeliveryMode(event.target.value);
  };

  const copyToClipboard = (to_copy: string) => {
    navigator.clipboard.writeText(to_copy);
    toast({
      render: () => {
        return createElement(ExpandibleToast, {
          message: 'Public RSA key copied to clipboard',
          status: 'success',
        });
      },
      duration: 3000,
      isClosable: true,
    });
  };

  const testDbMutation = useTestDbConnection();
  const createMutation = useCreateServiceCredential();
  const updateMutation = useUpdateServiceCredential();
  const handleSubmit = (val: any) => {
    const body: any = {
      name: val.name,
      environment: currentEnvironment?.id,
      connection_template: currentConnectionTemplate?.id,
      service: val.service,
      connection_overrides: {},
      ssl_key: null,
      delivery_mode: val.delivery_mode,
    };
    if (currentConnectionTemplate?.type.slug === 'snowflake') {
      body.connection_overrides.user = val.user;
      body.connection_overrides.schema = val.schema;

      if (overrideRole) {
        body.connection_overrides.role = val.roleOverride;
      }
      if (overrideAccount) {
        body.connection_overrides.account = val.accountOverride;
      }
      if (overrideDatabase) {
        body.connection_overrides.database = val.databaseOverride;
      }
      if (overrideWarehouse) {
        body.connection_overrides.warehouse = val.warehouseOverride;
      }
      if (currentSnowflakeAuth === 'password') {
        body.connection_overrides.password = val.password;
      } else {
        if (currentSSLKey) {
          body.ssl_key = parseInt(currentSSLKey.id);
        }
      }
    }
    if (currentConnectionTemplate?.type.slug === 'redshift') {
      body.connection_overrides.user = val.user;
      body.connection_overrides.schema = val.schema;
      if (overrideDatabase) {
        body.connection_overrides.database = val.databaseOverride;
      }
      if (overrideHost) {
        body.connection_overrides.host = val.hostOverride;
      }
      body.connection_overrides.password = val.password;
    }
    if (currentConnectionTemplate?.type.slug === 'databricks') {
      if (overrideSchema) {
        body.connection_overrides.schema = val.schemaOverride;
      }
      if (overrideHost) {
        body.connection_overrides.host = val.hostOverride;
      }
      if (overrideHttpPath) {
        body.connection_overrides.http_path = val.httpPathOverride;
      }
      body.connection_overrides.token = val.token;
    }
    if (currentConnectionTemplate?.type.slug === 'bigquery') {
      if (val.keyfile_json) {
        body.connection_overrides.keyfile_json = JSON.parse(val.keyfile_json);
      }
      if (overrideDataset) {
        body.connection_overrides.dataset = val.datasetOverride;
      }
    }
    if (currentAccount?.slug !== undefined) {
      if (isCreateMode) {
        createMutation
          .mutateAsync({
            account: currentAccount?.slug,
            body,
          })
          .then((record: any) => {
            testDbMutation
              .mutateAsync({ body: { service_credential_id: record.id } })
              .finally(handleClose);
          })
          .finally(handleClose); // returning to avoid re-creating connection
      } else {
        updateMutation
          .mutateAsync({
            account: currentAccount?.slug,
            id,
            body,
          })
          .then((record: any) => {
            testDbMutation
              .mutateAsync({ body: { service_credential_id: record.id } })
              .finally(handleClose);
          });
      }
    }
  };
  const navigate = useNavigate();

  const { data: serviceCredentials } = useServiceCredentials({
    account: currentAccount?.slug,
    environment: currentEnvironment?.id,
    limit: 100,
  });

  const validate = (values: FormikValues) => {
    const errors: { [key: string]: string } = {};
    const duplicatedServiceName = serviceCredentials?.results.filter(
      ({ name }) => name.toLowerCase() === values['name'].toLowerCase()
    );

    const duplicatedService = duplicatedServiceName?.find(
      ({ service }) => service === values.service
    );

    if (
      duplicatedService &&
      serviceCredentials &&
      values.environment &&
      duplicatedService?.id !== currentConnectionId &&
      !errors.name
    ) {
      errors.name =
        'This name was already used for the same service and environment before, please try something new';
    }

    return errors;
  };

  return (
    <BasePage header={isCreateMode ? 'Create service connection' : 'Edit service connection'}>
      <Box px={{ base: '4', md: '10' }} py="16" maxWidth="4xl" mx="auto">
        <Stack spacing="4" divider={<StackDivider />}>
          <Formik
            key={id}
            initialValues={initialValues}
            validate={validate}
            validationSchema={Yup.object({
              name: Yup.string()
                .matches(
                  /^[a-zA-Z0-9_ ]+$/,
                  'Connection name must consist of alphanumeric characters, underscores and spaces'
                )
                .required('Required'),
              service: Yup.string().required('Required'),
              delivery_mode: Yup.string().required('Required'),
              connection_template: Yup.string().required('Required'),
              environment: Yup.string().required('Required'),
              accountOverride: Yup.string().when({
                is: () => overrideAccount,
                then: Yup.string().when({
                  is: () => currentConnectionTemplate?.type.slug === 'snowflake',
                  then: Yup.string()
                    .required('Required')
                    .matches(
                      /^(?!.*\.(?!privatelink$)).*$/,
                      'Accounts must not contain a period. Try a dash instead.'
                    ),
                  otherwise: Yup.string().required('Required'),
                }),
                otherwise: Yup.string(),
              }),
              warehouseOverride: Yup.string().when({
                is: () => overrideWarehouse,
                then: Yup.string().required('Required'),
                otherwise: Yup.string(),
              }),
              databaseOverride: Yup.string().when({
                is: () => overrideDatabase,
                then: Yup.string().required('Required'),
                otherwise: Yup.string(),
              }),
              roleOverride: Yup.string().when({
                is: () => overrideRole,
                then: Yup.string().required('Required'),
                otherwise: Yup.string(),
              }),
              hostOverride: Yup.string().when({
                is: () => overrideHost,
                then: Yup.string().required('Required'),
                otherwise: Yup.string(),
              }),
              schema: Yup.string().when({
                is: () =>
                  currentConnectionTemplate?.type.slug === 'snowflake' ||
                  currentConnectionTemplate?.type.slug === 'redshift',
                then: Yup.string().required('Required'),
                otherwise: Yup.string(),
              }),
              schemaOverride: Yup.string().when({
                is: () => overrideSchema,
                then: Yup.string().required('Required'),
                otherwise: Yup.string(),
              }),
              user: Yup.string().when({
                is: () =>
                  currentConnectionTemplate?.type.slug === 'snowflake' ||
                  currentConnectionTemplate?.type.slug === 'redshift',
                then: Yup.string().required('Required'),
                otherwise: Yup.string(),
              }),
              httpPathOverride: Yup.string().when({
                is: () => overrideHttpPath,
                then: Yup.string().required('Required'),
                otherwise: Yup.string(),
              }),
              keyfile_json: Yup.string().when({
                is: () => currentConnectionTemplate?.type.slug === 'bigquery',
                then: Yup.string()
                  .required('Required')
                  .test(
                    'is-json-valid',
                    'Invalid JSON',
                    (value) => value == null || isJsonString(value)
                  ),
                otherwise: Yup.string(),
              }),
              datasetOverride: Yup.string().when({
                is: () => overrideDataset,
                then: Yup.string().required('Required'),
                otherwise: Yup.string(),
              }),
            })}
            onSubmit={handleSubmit}
          >
            {function Render({ setFieldValue, values, handleChange }) {
              const { data, isSuccess, isLoading } = useServiceCredential(
                currentAccount?.slug,
                id,
                {
                  enabled:
                    connectionTemplatesSuccess &&
                    environmentsSuccess &&
                    currentAccount?.slug !== undefined &&
                    id !== undefined,
                  onSuccess: (data: ServiceCredential) => {
                    const connectionTemplate = connectionTemplates?.find(
                      (conn) => parseInt(conn.id) === parseInt(data.connection_template)
                    );
                    setCurrentConnectionId(data.id);
                    setFieldValue('name', data.name);
                    setFieldValue('service', data.service);
                    setFieldValue('delivery_mode', data.delivery_mode);
                    setCurrentService(data.service);
                    setFieldValue(
                      'accountOverride',
                      data.connection_overrides.account
                        ? data.connection_overrides.account
                        : connectionTemplate?.connection_details.account
                    );
                    setFieldValue(
                      'warehouseOverride',
                      data.connection_overrides.warehouse
                        ? data.connection_overrides.warehouse
                        : connectionTemplate?.connection_details.warehouse
                    );
                    setFieldValue(
                      'databaseOverride',
                      data.connection_overrides.database
                        ? data.connection_overrides.database
                        : connectionTemplate?.connection_details.database
                    );
                    setFieldValue(
                      'roleOverride',
                      data.connection_overrides.role
                        ? data.connection_overrides.role
                        : connectionTemplate?.connection_details.role
                    );
                    setFieldValue(
                      'hostOverride',
                      data.connection_overrides.host
                        ? data.connection_overrides.host
                        : connectionTemplate?.connection_details.host
                    );
                    setFieldValue('schema', data.connection_overrides.schema);
                    setFieldValue('user', data.connection_overrides.user);
                    const env = environments?.find(
                      (env) => parseInt(env.id) === parseInt(data.environment)
                    );
                    setFieldValue('environment', env?.id);
                    setFieldValue(
                      'schemaOverride',
                      data.connection_overrides.schema
                        ? data.connection_overrides.schema
                        : connectionTemplate?.connection_details.schema
                    );
                    setFieldValue(
                      'httpPathOverride',
                      data.connection_overrides.http_path
                        ? data.connection_overrides.http_path
                        : connectionTemplate?.connection_details.http_path
                    );
                    setFieldValue('token', data.connection_overrides.token);
                    setFieldValue('connection_template', connectionTemplate?.id);
                    setFieldValue(
                      'keyfile_json',
                      JSON.stringify(data.connection_overrides.keyfile_json)
                    );
                    setFieldValue(
                      'datasetOverride',
                      data.connection_overrides.dataset
                        ? data.connection_overrides.dataset
                        : connectionTemplate?.connection_details.dataset
                    );
                    setFieldValue('dataset', data.connection_overrides.dataset);
                    setCurrentConnectionTemplate(connectionTemplate);
                    setCurrentEnvironment(env);
                    const auth = data.ssl_key ? 'key-pair' : 'password';
                    setCurrentSnowflakeAuth(auth);
                    setFieldValue('authentication', auth);
                    if (data.ssl_key && data.public_ssl_key) {
                      setCurrentSSLKey({ id: data.ssl_key, ssl_key: data.public_ssl_key });
                    }
                  },
                }
              );

              useEffect(() => {
                if (
                  !!values.environment &&
                  isCreateMode &&
                  !values.name &&
                  serviceCredentials?.results.length === 0
                ) {
                  setFieldValue('name', 'main');
                }
                // eslint-disable-next-line react-hooks/exhaustive-deps
              }, [setFieldValue, values, serviceCredentials?.results]);

              return (
                <LoadingWrapper
                  isLoading={!isCreateMode && isLoading}
                  showElements={isCreateMode || (data && isSuccess)}
                >
                  <Form>
                    <FieldGroup title="Basic Info">
                      <VStack width="full" spacing="6">
                        <Box w="full">
                          <SelectControl
                            label="Environment"
                            name="environment"
                            selectProps={{ placeholder: 'Select environment' }}
                            onChange={(e) => {
                              handleChange(e);
                              handleSelectEnvironment(e);
                            }}
                            isRequired
                          >
                            {environments?.map((env: Environment) => {
                              return (
                                <option key={`environments.${env.id}`} value={env.id}>
                                  {env.name} ({env.slug})
                                </option>
                              );
                            })}
                          </SelectControl>
                        </Box>
                        {(values.environment || !isCreateMode) && (
                          <>
                            <Box w="full">
                              <InputControl name="name" label="Name" isRequired />
                              <Text color="gray.500" mt={1} fontSize="xs">
                                This is used to identify this connection in the target service, i.e.
                                as part of environment variable names
                              </Text>
                            </Box>
                            <Box w="full">
                              <HStack spacing="8" alignItems="flex-start" w="full">
                                <Box w="full">
                                  <SelectControl
                                    label="Service"
                                    name="service"
                                    selectProps={{ placeholder: 'Select target service' }}
                                    onChange={handleSelectService}
                                    isRequired
                                  >
                                    <option value="airflow">Airflow</option>
                                  </SelectControl>
                                  {currentService === 'airflow' && (
                                    <SelectControl
                                      label="Delivery Mode"
                                      name="delivery_mode"
                                      mt="3"
                                      isRequired
                                      onChange={handleSelectDeliveryMode}
                                    >
                                      <option value="connection">Airflow Connection</option>
                                      <option value="env">Environment Variables</option>
                                    </SelectControl>
                                  )}
                                  {currentService === 'airflow' && (
                                    <Flex w="full" justifyContent="center">
                                      <Popover>
                                        <PopoverTrigger>
                                          <Button
                                            mt="3"
                                            leftIcon={<QuestionIcon color="blue.500" />}
                                            variant="link"
                                            colorScheme="blue"
                                          >
                                            How to use this connection?
                                          </Button>
                                        </PopoverTrigger>
                                        <PopoverContent w="xl">
                                          <PopoverArrow />
                                          <PopoverCloseButton />
                                          <PopoverHeader fontWeight="bold">
                                            <Text mx="2">Connection configuration on Airflow</Text>
                                          </PopoverHeader>
                                          <PopoverBody>
                                            <Text m="2">
                                              Service connections can be provided in one of two ways
                                              based on the &quot;Delivery Mode&quot; setting.
                                            </Text>
                                            <Text m="2" fontWeight="bold">
                                              Using Environment Variables
                                            </Text>
                                            <Text m="2">
                                              Service connections on Airflow are injected using
                                              Environment Variables.
                                            </Text>
                                            <Text m="2">
                                              A variable will be created for each connection
                                              attribute, using the pattern{' '}
                                              <Tag color="blue.500" fontWeight="bold">
                                                DATACOVES__[CONNECTION NAME]__[ATTRIBUTE NAME]
                                              </Tag>
                                            </Text>
                                            <Text m="2">
                                              For instance, if the service connection is called
                                              &quot;Main&quot;, the account could be found as a
                                              variable named{' '}
                                              <Tag color="blue.500" fontWeight="bold">
                                                DATACOVES__MAIN__ACCOUNT
                                              </Tag>
                                              , in addition to the rest of the attributes.
                                            </Text>
                                            <Text m="2" fontWeight="bold">
                                              Using Airflow Connections
                                            </Text>
                                            <Text m="2">
                                              If you choose to use the Airflow Connection delivery
                                              mode, then we will automatically push an Airflow
                                              Connection via Airflow&lsquo;s API into your Team
                                              Airflow instance. The connection ID will be the
                                              connection name provided on this screen.
                                            </Text>
                                          </PopoverBody>
                                        </PopoverContent>
                                      </Popover>
                                    </Flex>
                                  )}
                                </Box>
                              </HStack>
                            </Box>
                            <Box w="full">
                              <SelectControl
                                label="Connection Template"
                                name="connection_template"
                                selectProps={{ placeholder: 'Select connection template' }}
                                onChange={handleSelectConnectionTemplate}
                                isRequired
                              >
                                {connectionTemplates?.map((conn: RConnectionTemplate) => {
                                  return (
                                    <option key={`connectionTemplates.${conn.id}`} value={conn.id}>
                                      {conn.name} ({conn.type.name})
                                    </option>
                                  );
                                })}
                              </SelectControl>
                              <Text color="gray.500" mt={1} fontSize="xs">
                                Select a connection template to load default connection values from.
                              </Text>
                            </Box>
                          </>
                        )}
                      </VStack>
                    </FieldGroup>
                    {currentConnectionTemplate &&
                      currentConnectionTemplate.type_slug === 'snowflake' && (
                        <FieldGroup title="Connection details">
                          <VStack>
                            <HStack spacing="8" alignItems="flex-start" w="full">
                              <InputWithToggleTwo
                                label="Account"
                                name="accountOverride"
                                defaultValue={currentConnectionTemplate?.connection_details.account}
                                wasChanged={
                                  data?.connection_overrides.account !== undefined ||
                                  currentConnectionTemplate?.connection_details.account ===
                                    undefined
                                }
                                setOverrideValue={setOverrideAccount}
                              />
                              <InputWithToggleTwo
                                label="Warehouse"
                                name="warehouseOverride"
                                defaultValue={
                                  currentConnectionTemplate?.connection_details.warehouse
                                }
                                wasChanged={
                                  data?.connection_overrides.warehouse !== undefined ||
                                  currentConnectionTemplate?.connection_details.warehouse ===
                                    undefined
                                }
                                setOverrideValue={setOverrideWarehouse}
                              />
                            </HStack>
                            <HStack spacing="8" alignItems="flex-start" w="full">
                              <InputWithToggleTwo
                                label="Database"
                                name="databaseOverride"
                                defaultValue={
                                  currentConnectionTemplate?.connection_details.database
                                }
                                wasChanged={
                                  data?.connection_overrides.database !== undefined ||
                                  currentConnectionTemplate?.connection_details.database ===
                                    undefined
                                }
                                setOverrideValue={setOverrideDatabase}
                              />
                              <InputWithToggleTwo
                                label="Role"
                                name="roleOverride"
                                defaultValue={currentConnectionTemplate?.connection_details.role}
                                wasChanged={
                                  data?.connection_overrides.role !== undefined ||
                                  currentConnectionTemplate?.connection_details.role === undefined
                                }
                                setOverrideValue={setOverrideRole}
                              />
                            </HStack>
                            <HStack w="full">
                              <InputControl name="user" label="User" isRequired />
                              <InputControl name="schema" label="Schema" isRequired />
                            </HStack>
                            <HStack w="full">
                              <Box w="full">
                                <SelectControl
                                  label="Authentication mechanism"
                                  name="authentication"
                                  selectProps={{ placeholder: 'Select authentication mechanism' }}
                                  onChange={handleSelectAuthenticationSnowflake}
                                  isRequired
                                >
                                  <option value="password">Password</option>
                                  {deliveryMode === 'connection' && (
                                    <option value="key-pair">RSA Key-pair</option>
                                  )}
                                </SelectControl>
                                <Text color="gray.500" mt={1} fontSize="xs">
                                  Select one of the authentication mechanisms supported by
                                  Snowflake.
                                </Text>
                              </Box>
                            </HStack>
                            {currentSnowflakeAuth === 'password' && (
                              <InputControl
                                name="password"
                                label="Password"
                                inputProps={{ placeholder: '*******', type: 'password' }}
                                isRequired={data ? false : true}
                              />
                            )}
                            {currentSnowflakeAuth === 'key-pair' && currentSSLKey && (
                              <VStack w="full" alignItems="flex-start">
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
                                    onClick={() => copyToClipboard(currentSSLKey.ssl_key)}
                                  >
                                    COPY
                                  </Button>
                                </Stack>
                                <FormLabel htmlFor="key_value">Public RSA key</FormLabel>
                                <Textarea
                                  name="key_value"
                                  isReadOnly={true}
                                  value={currentSSLKey.ssl_key}
                                  isRequired
                                />
                                <Text color="gray.500" mt={1} fontSize="xs">
                                  This is an auto-generated RSA key. Copy it and configure it your
                                  snowflake account.{' '}
                                  <Link
                                    color="blue.500"
                                    href="https://docs.snowflake.com/en/user-guide/key-pair-auth#assign-the-public-key-to-a-snowflake-user"
                                    target="_blank"
                                    rel="noreferrer"
                                  >
                                    See How <ExternalLinkIcon />
                                  </Link>
                                  .
                                </Text>
                              </VStack>
                            )}
                          </VStack>
                          )
                        </FieldGroup>
                      )}
                    {currentConnectionTemplate &&
                      currentConnectionTemplate.type_slug === 'redshift' && (
                        <FieldGroup title="Connection details">
                          <VStack w="full">
                            <InputWithToggleTwo
                              label="Host"
                              name="hostOverride"
                              defaultValue={currentConnectionTemplate?.connection_details.host}
                              wasChanged={
                                data?.connection_overrides.host !== undefined ||
                                currentConnectionTemplate?.connection_details.host === undefined
                              }
                              setOverrideValue={setOverrideHost}
                            />
                            <InputWithToggleTwo
                              label="Database"
                              name="databaseOverride"
                              defaultValue={currentConnectionTemplate?.connection_details.database}
                              wasChanged={
                                data?.connection_overrides.database !== undefined ||
                                currentConnectionTemplate?.connection_details.database === undefined
                              }
                              setOverrideValue={setOverrideDatabase}
                            />
                            <HStack spacing="8" alignItems="flex-start" w="full">
                              <InputControl name="user" label="User" isRequired />
                              <InputControl name="schema" label="Schema" isRequired />
                            </HStack>
                            <InputControl
                              name="password"
                              label="Password"
                              inputProps={{ placeholder: '*******', type: 'password' }}
                              isRequired={data ? false : true}
                            />
                          </VStack>
                          )
                        </FieldGroup>
                      )}
                    {currentConnectionTemplate &&
                      currentConnectionTemplate.type_slug === 'databricks' && (
                        <FieldGroup title="Connection details">
                          <VStack w="full">
                            <InputWithToggleTwo
                              label="Host"
                              name="hostOverride"
                              defaultValue={currentConnectionTemplate?.connection_details.host}
                              wasChanged={
                                data?.connection_overrides.host !== undefined ||
                                currentConnectionTemplate?.connection_details.host === undefined
                              }
                              setOverrideValue={setOverrideHost}
                            />
                            <InputWithToggleTwo
                              label="Schema"
                              name="schemaOverride"
                              defaultValue={currentConnectionTemplate?.connection_details.schema}
                              wasChanged={
                                data?.connection_overrides.schema !== undefined ||
                                currentConnectionTemplate?.connection_details.schema === undefined
                              }
                              setOverrideValue={setOverrideSchema}
                            />
                            <InputWithToggleTwo
                              label="HTTP Path"
                              name="httpPathOverride"
                              defaultValue={currentConnectionTemplate?.connection_details.http_path}
                              wasChanged={
                                data?.connection_overrides.http_path !== undefined ||
                                currentConnectionTemplate?.connection_details.http_path ===
                                  undefined
                              }
                              setOverrideValue={setOverrideHttpPath}
                            />
                            <InputControl
                              name="token"
                              label="Token"
                              inputProps={{ placeholder: '*******', type: 'password' }}
                              isRequired={data ? false : true}
                            />
                          </VStack>
                          )
                        </FieldGroup>
                      )}
                    {currentConnectionTemplate &&
                      currentConnectionTemplate.type_slug === 'bigquery' && (
                        <FieldGroup title="Default values">
                          <VStack w="full">
                            <InputWithToggleTwo
                              label="Dataset"
                              name="datasetOverride"
                              defaultValue={currentConnectionTemplate?.connection_details.dataset}
                              wasChanged={
                                data?.connection_overrides.dataset !== undefined ||
                                currentConnectionTemplate?.connection_details.dataset === undefined
                              }
                              setOverrideValue={setOverrideDataset}
                            />
                            <TextareaControl
                              name="keyfile_json"
                              label="Keyfile JSON"
                              isRequired
                            ></TextareaControl>
                          </VStack>
                        </FieldGroup>
                      )}
                    <FieldGroup>
                      {currentConnectionTemplate &&
                        currentConnectionTemplate.connection_details.mfa_protected && (
                          <ConnectionMFAWarningAlert />
                        )}
                    </FieldGroup>

                    <FieldGroup>
                      <HStack width="full" justifyContent="flex-end" spacing="6">
                        {(updateMutation.isLoading ||
                          testDbMutation.isLoading ||
                          createMutation.isLoading) && (
                          <Text flex="1" textAlign="right" pr="5">
                            Testing connection...
                          </Text>
                        )}
                        <Button onClick={handleClose}>Cancel</Button>
                        <Button
                          type="submit"
                          colorScheme="blue"
                          isLoading={
                            testDbMutation.isLoading ||
                            updateMutation.isLoading ||
                            createMutation.isLoading
                          }
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
