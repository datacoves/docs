import { DeleteIcon, EditIcon } from '@chakra-ui/icons';
import {
  Button,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  useDisclosure,
  VStack,
  ButtonProps,
  HStack,
  Box,
  Text,
  Tooltip,
  FormLabel,
  Input,
} from '@chakra-ui/react';
import { Form, Formik } from 'formik';
import { SelectControl, InputControl, TextareaControl } from 'formik-chakra-ui';
import React, { useContext, useEffect, useState } from 'react';
import * as Yup from 'yup';

import { InputWithToggleTwo } from '..';
import { AlertDialog } from '../../../../components/AlertDialog';
import { TestButton } from '../../../../components/TestButton';
import { UserContext } from '../../../../context/UserContext';
import { useCreateProfileCredential } from '../../../global/api/createProfileCredential';
import { useDeleteProfileCredential } from '../../../global/api/deleteProfileCredential';
import { useProfileCredentialDetail } from '../../../global/api/getProfileCredentialDetail';
import { useProfileCredentialsList } from '../../../global/api/getProfileCredentialsList';
import { useProfileSSLKeysList } from '../../../global/api/getProfileSSLKeysList';
import { useTestDbConnection } from '../../../global/api/testDbConnection';
import { useUpdateProfileCredential } from '../../../global/api/updateProfileCredential';
import ConnectionMFAWarningAlert from '../../../global/components/ConnectionMFAWarningAlert';
import { RConnectionTemplate, UserCredential, UserSSLKey } from '../../../global/types';
interface ModalCredentialsProps extends ButtonProps {
  title: string;
  connectionTemplates?: RConnectionTemplate[];
  userCredential?: UserCredential;
  environmentId: string;
}

const isJsonString = (text: string): boolean => {
  try {
    JSON.parse(text);
  } catch (e) {
    return false;
  }
  return true;
};

export const ModalCredentials = (props: ModalCredentialsProps) => {
  const { title, connectionTemplates, userCredential, environmentId } = props;
  const { currentUser } = useContext(UserContext);
  const [defaultUser, setDefaultUser] = useState(currentUser?.email_username);
  const [currentConnectionTemplate, setCurrentConnectionTemplate] = useState<RConnectionTemplate>();
  const [overrideAccount, setOverrideAccount] = useState(false);
  const [overrideWarehouse, setOverrideWarehouse] = useState(false);
  const [overrideDatabase, setOverrideDatabase] = useState(false);
  const [overrideRole, setOverrideRole] = useState(false);
  const [overrideHost, setOverrideHost] = useState(false);
  const [overrideSchema, setOverrideSchema] = useState(false);
  const [overrideHttpPath, setOverrideHttpPath] = useState(false);
  const [authType, setAuthType] = useState<string>('password');
  const [isConfirmDeleteOpen, setIsConfirmDeleteOpen] = useState(false);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const isCreateMode = userCredential === undefined;
  const { data: userSSLKeys } = useProfileSSLKeysList();
  const [overrideDataset, setOverrideDataset] = useState(false);
  const [showMFAWarning, setShowMFAWarning] = useState(false);

  useEffect(() => {
    if (connectionTemplates && userCredential) {
      const conn = connectionTemplates.find(
        (conn) => conn.id === userCredential.connection_template
      );
      if (conn) {
        setCurrentConnectionTemplate(conn);
        setShowMFAWarning(conn.connection_details.mfa_protected);
      }
    }
  }, [connectionTemplates, userCredential]);

  const initialValues = {
    name: '',
    connection_template: '',
    account: '',
    accountOverride: '',
    warehouse: '',
    warehouseOverride: '',
    database: '',
    databaseOverride: '',
    role: '',
    roleOverride: '',
    schema: '',
    schemaOverride: '',
    host: '',
    hostOverride: '',
    user: '',
    http_path: '',
    httpPathOverride: '',
    token: '',
    keyfile_json: '',
  };
  const handleSelectConnectionTemplate = (event: any) => {
    const connectionTemplate = connectionTemplates?.find(
      (conn) => parseInt(conn.id) === parseInt(event.target.value)
    );
    setCurrentConnectionTemplate(connectionTemplate);
    if (connectionTemplate?.connection_user === 'provided') {
      setAuthType('password');
    }
    setShowMFAWarning(connectionTemplate?.connection_details.mfa_protected ?? false);
  };
  const handleSelectAuthType = (event: any) => {
    setAuthType(event.target.value);
  };
  const handlerClose = () => {
    setCurrentConnectionTemplate(undefined);
    setAuthType('password');
    onClose();
  };
  const testDbMutation = useTestDbConnection();
  const createMutation = useCreateProfileCredential();
  const updateMutation = useUpdateProfileCredential();
  const deleteMutation = useDeleteProfileCredential();

  const handleSubmit = (val: any) => {
    const body: any = {
      name: val.name,
      environment: environmentId,
      connection_template: currentConnectionTemplate?.id,
      connection_overrides: {},
      ssl_key: null,
    };
    if (currentConnectionTemplate?.type.slug === 'snowflake') {
      if (currentConnectionTemplate?.connection_user === 'provided') {
        body.connection_overrides.user = defaultUser;
      } else {
        body.connection_overrides.user = currentConnectionTemplate.default_username;
      }
      body.connection_overrides.schema = overrideSchema ? val.schemaOverride : defaultUser;
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
    }
    if (currentConnectionTemplate?.type.slug === 'redshift') {
      body.connection_overrides.user = defaultUser;
      body.connection_overrides.schema = overrideSchema ? val.schemaOverride : defaultUser;
      if (overrideDatabase) {
        body.connection_overrides.database = val.databaseOverride;
      }
      if (overrideHost) {
        body.connection_overrides.host = val.hostOverride;
      }
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

    if (authType === 'password') {
      body.connection_overrides.password = val.password;
      body.ssl_key = null;
    } else {
      body.ssl_key = parseInt(val.ssl_key);
      delete body.connection_overrides.password;
    }
    if (isCreateMode) {
      createMutation
        .mutateAsync({ environmentId, body: body })
        .then((record: any) => {
          // Closing modal despite connection fails
          testDbMutation
            .mutateAsync({ body: { user_credential_id: record.id } })
            .finally(handlerClose);
        })
        .catch(handlerClose);
    } else {
      updateMutation.mutateAsync({ id: userCredential?.id, body }).then((record: any) => {
        testDbMutation
          .mutateAsync({ body: { user_credential_id: record.id } })
          .finally(handlerClose);
      });
    }
  };

  const handleTest = () => {
    testDbMutation.mutate({ body: { user_credential_id: userCredential?.id } });
  };

  const handleDelete = () => {
    setIsConfirmDeleteOpen(true);
  };

  const handleConfirmDelete = () => {
    if (!isCreateMode) {
      deleteMutation.mutate({ id: userCredential?.id });
    }
  };

  return (
    <>
      {isCreateMode ? (
        <Button colorScheme="blue" onClick={onOpen} size="sm">
          Add
        </Button>
      ) : (
        <HStack justifyContent="space-around" w="full">
          <TestButton
            testType="connection"
            validatedAt={userCredential.validated_at}
            onClick={handleTest}
            isLoading={testDbMutation.isLoading}
          />
          <HStack>
            <Tooltip label="Edit connection">
              <Button variant="ghost" colorScheme="blue" onClick={onOpen}>
                <EditIcon />
              </Button>
            </Tooltip>
            <Tooltip label="Delete connection">
              <Button variant="ghost" colorScheme="red" onClick={handleDelete}>
                <DeleteIcon />
              </Button>
            </Tooltip>
            <AlertDialog
              isOpen={isConfirmDeleteOpen}
              header={`Delete '${userCredential.name}' connection`}
              message="Are you sure? You can't undo this action."
              confirmLabel="Delete"
              onClose={() => setIsConfirmDeleteOpen(false)}
              onConfirm={handleConfirmDelete}
            />
          </HStack>
        </HStack>
      )}
      <Modal size="3xl" isOpen={isOpen} onClose={handlerClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>{title}</ModalHeader>
          <Formik
            initialValues={initialValues}
            validationSchema={Yup.object({
              name: Yup.string().required('Required'),
              connection_template: Yup.string().required('Required'),
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
              schemaOverride: Yup.string().when({
                is: () => overrideSchema,
                then: Yup.string().required('Required'),
                otherwise: Yup.string(),
              }),
              user: Yup.string().when({
                is: () =>
                  (currentConnectionTemplate?.connection_user === 'provided' &&
                    currentConnectionTemplate?.type.slug === 'snowflake') ||
                  currentConnectionTemplate?.type.slug === 'redshift',
                then: Yup.string().required('Required'),
                otherwise: Yup.string(),
              }),
              ssl_key: Yup.string().when({
                is: () => authType === 'key',
                then: Yup.string().nullable().required('Required'),
                otherwise: Yup.string().nullable(),
              }),
              token: Yup.string().when({
                is: () => currentConnectionTemplate?.type.slug === 'databricks',
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
            {function Render({ setFieldValue, values }) {
              const { data, isSuccess } = useProfileCredentialDetail(userCredential?.id ?? '', {
                enabled: userCredential !== undefined && connectionTemplates !== undefined,
                onSuccess: (data: UserCredential) => {
                  const connectionTemplate = connectionTemplates?.find(
                    (conn) => parseInt(conn.id) === parseInt(data.connection_template)
                  );
                  setFieldValue('name', data.name);
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
                  setFieldValue(
                    'schemaOverride',
                    data.connection_overrides.schema
                      ? data.connection_overrides.schema
                      : data.connection_overrides.user
                  );
                  setFieldValue('ssl_key', data.ssl_key ?? '');
                  setFieldValue('connection_template', connectionTemplate?.id);
                  setCurrentConnectionTemplate(connectionTemplate);

                  if (connectionTemplate?.connection_user === 'provided') {
                    setDefaultUser(data.connection_overrides.user);
                    setFieldValue('user', data.connection_overrides.user);
                  }

                  const authType = data.ssl_key ? 'key' : 'password';
                  setFieldValue('authType', authType);
                  setAuthType(authType);
                  setFieldValue(
                    'httpPathOverride',
                    data.connection_overrides.http_path
                      ? data.connection_overrides.http_path
                      : connectionTemplate?.connection_details.http_path
                  );
                  setFieldValue('token', data.connection_overrides.token);
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
                },
              });

              const { data: credentialsList, isSuccess: isSuccessList } = useProfileCredentialsList(
                { environment: Number(environmentId) }
              );

              const [showDefaultName, setShowDefaultName] = useState(false);

              useEffect(() => {
                if (
                  isCreateMode &&
                  isSuccessList &&
                  credentialsList?.length === 0 &&
                  !values.name
                ) {
                  setFieldValue('name', 'dev');
                  setShowDefaultName(true);
                }
              }, [credentialsList?.length, isSuccessList, setFieldValue, values.name]);

              const handleuserChange = (e: any) => {
                const { value } = e.target;
                if (!overrideSchema) {
                  setFieldValue('schemaOverride', value);
                }
                setDefaultUser(value);
              };

              return (
                ((isCreateMode && isSuccessList) || (data && isSuccess)) && (
                  <Form>
                    <ModalBody>
                      <VStack width="full" spacing="6">
                        <Box w="full">
                          <InputControl name="name" label="Name" isRequired />
                          <Text color="gray.500" mt={1} fontSize="xs">
                            This is used to identify this connection in tools like dbt, i.e. as the
                            target name. {showDefaultName && 'dbt’s default is dev.'}
                          </Text>
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
                                <option key={`connection_templates.${conn.id}`} value={conn.id}>
                                  {conn.name} ({conn.type.name})
                                </option>
                              );
                            })}
                          </SelectControl>
                          <Text color="gray.500" mt={1} fontSize="xs">
                            Select a connection template to load default connection values from.
                          </Text>
                        </Box>
                        {currentConnectionTemplate &&
                          currentConnectionTemplate.type_slug === 'snowflake' && (
                            <>
                              <HStack spacing="8" alignItems="flex-start" w="full">
                                <InputWithToggleTwo
                                  label="Account"
                                  name="accountOverride"
                                  defaultValue={
                                    currentConnectionTemplate?.connection_details.account
                                  }
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
                              <HStack spacing="8" alignItems="flex-start" w="full">
                                {currentConnectionTemplate.connection_user === 'provided' && (
                                  <InputControl
                                    name="user"
                                    label="User"
                                    onChange={handleuserChange}
                                    isRequired
                                  />
                                )}
                                {currentConnectionTemplate.connection_user !== 'provided' && (
                                  <VStack w="full" alignItems="flex-start">
                                    <FormLabel mb="0">User</FormLabel>
                                    <Input
                                      value={currentConnectionTemplate.default_username}
                                      isReadOnly
                                      textColor="GrayText"
                                      isRequired
                                    />
                                  </VStack>
                                )}
                                <InputWithToggleTwo
                                  label="Schema"
                                  name="schemaOverride"
                                  defaultValue={defaultUser}
                                  wasChanged={
                                    data?.connection_overrides.schema !== undefined &&
                                    data?.connection_overrides.schema !== defaultUser
                                  }
                                  setOverrideValue={setOverrideSchema}
                                />
                              </HStack>

                              {currentConnectionTemplate.connection_user === 'provided' && (
                                <SelectControl
                                  label="Auth type"
                                  name="authType"
                                  isDisabled={true}
                                  selectProps={{ isDisabled: true }}
                                  isRequired
                                >
                                  <option value="password">Password</option>
                                </SelectControl>
                              )}
                              {currentConnectionTemplate.connection_user !== 'provided' && (
                                <SelectControl
                                  label="Auth type"
                                  name="authType"
                                  onChange={handleSelectAuthType}
                                  isRequired
                                >
                                  <option value="password">Password</option>
                                  <option value="key">Key pair</option>
                                </SelectControl>
                              )}

                              {authType === 'password' && (
                                <InputControl
                                  name="password"
                                  label="Password"
                                  inputProps={{ placeholder: '*******', type: 'password' }}
                                  isRequired={data ? false : true}
                                />
                              )}
                              {authType === 'key' && (
                                <SelectControl
                                  label="Public key"
                                  name="ssl_key"
                                  selectProps={{ placeholder: 'Select public key' }}
                                  isRequired
                                >
                                  {userSSLKeys?.map((ssl_key: UserSSLKey) => {
                                    return (
                                      <option key={`ssl_key.${ssl_key.id}`} value={ssl_key.id}>
                                        {ssl_key.public.substr(0, 80)}...
                                      </option>
                                    );
                                  })}
                                </SelectControl>
                              )}
                            </>
                          )}
                        {currentConnectionTemplate &&
                          currentConnectionTemplate.type_slug === 'redshift' && (
                            <>
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
                              <HStack spacing="8" alignItems="flex-start" w="full">
                                <InputControl
                                  name="user"
                                  label="User"
                                  onChange={handleuserChange}
                                  isRequired
                                />
                                <InputWithToggleTwo
                                  label="Schema"
                                  name="schemaOverride"
                                  defaultValue={defaultUser}
                                  wasChanged={
                                    data?.connection_overrides.schema !== undefined &&
                                    data?.connection_overrides.schema !==
                                      data?.connection_overrides.user
                                  }
                                  setOverrideValue={setOverrideSchema}
                                />
                              </HStack>
                              <InputControl
                                name="password"
                                label="Password"
                                inputProps={{ placeholder: '*******', type: 'password' }}
                                isRequired
                              />
                            </>
                          )}

                        {currentConnectionTemplate &&
                          currentConnectionTemplate.type_slug === 'databricks' && (
                            <>
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
                                defaultValue={
                                  currentConnectionTemplate?.connection_details.http_path
                                }
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
                            </>
                          )}
                        {currentConnectionTemplate &&
                          currentConnectionTemplate.type_slug === 'bigquery' && (
                            <>
                              <InputWithToggleTwo
                                label="Dataset"
                                name="datasetOverride"
                                defaultValue={currentConnectionTemplate?.connection_details.dataset}
                                wasChanged={
                                  data?.connection_overrides.dataset !== undefined ||
                                  currentConnectionTemplate?.connection_details.dataset ===
                                    undefined
                                }
                                setOverrideValue={setOverrideDataset}
                              />
                              <TextareaControl
                                name="keyfile_json"
                                label="Keyfile JSON"
                                isRequired
                              ></TextareaControl>
                            </>
                          )}
                        {showMFAWarning && <ConnectionMFAWarningAlert />}
                      </VStack>
                    </ModalBody>

                    <ModalFooter>
                      {(updateMutation.isLoading ||
                        testDbMutation.isLoading ||
                        createMutation.isLoading) && (
                        <Text flex="1" textAlign="right" pr="5">
                          Testing connection...
                        </Text>
                      )}
                      <Button
                        colorScheme="blue"
                        mr={3}
                        type="submit"
                        isLoading={
                          updateMutation.isLoading ||
                          testDbMutation.isLoading ||
                          createMutation.isLoading
                        }
                      >
                        Save
                      </Button>
                      <Button
                        variant="ghost"
                        onClick={handlerClose}
                        disabled={
                          updateMutation.isLoading ||
                          testDbMutation.isLoading ||
                          createMutation.isLoading
                        }
                      >
                        Cancel
                      </Button>
                    </ModalFooter>
                  </Form>
                )
              );
            }}
          </Formik>
        </ModalContent>
      </Modal>
    </>
  );
};
