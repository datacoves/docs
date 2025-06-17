import { ExternalLinkIcon } from '@chakra-ui/icons';
import { Box, Button, Link, HStack, Text, VStack, Stack, Heading } from '@chakra-ui/react';
import { Form, Formik } from 'formik';
import { SelectControl, InputControl, TextareaControl, SwitchControl } from 'formik-chakra-ui';
import React, { useState } from 'react';
import * as Yup from 'yup';

import { Notification, NotificationButton } from '../../../components/Notification';
import { useTestDbConnection } from '../api/testDbConnection';

import ConnectionMFAWarningAlert from './ConnectionMFAWarningAlert';
import { TestConnectionProgress } from './TestConnectionProgress';

export const ConnectionSignUp = (props: any) => {
  const account = 'ab0001.us-west-1';
  const [valueState, setValueState] = useState('');
  const [showSnowflakeTrial, setShowSnowflakeTrial] = useState(true);
  const [isMfaEnabled, setIsMfaEnabled] = useState(false);
  const initialValues = {
    type: '',
    account: '',
    warehouse: '',
    database: '',
    role: '',
    schema: '',
    user: '',
    password: '',
    http_path: '',
    token: '',
    dataset: '',
    keyfile_json: '',
  };

  const isJsonString = (text: string): boolean => {
    try {
      JSON.parse(text);
    } catch (e) {
      return false;
    }
    return true;
  };

  const handlerSelect = (event: any) => {
    const value = event.target.value;
    setValueState(value);
  };

  const testDbMutation = useTestDbConnection();

  const handleSubmit = (val: any, { setSubmitting }: any) => {
    let body = {};
    if (val.type === 'snowflake') {
      body = {
        type: val.type,
        connection: {
          user: val.user,
          password: val.password,
          warehouse: val.warehouse,
          account: val.account,
          role: val.role,
          database: val.database,
          schema: val.schema,
        },
      };
      props.payload.connection.connection_details.user = val.user;
      props.payload.connection.connection_details.password = val.password;
      props.payload.connection.connection_details.warehouse = val.warehouse;
      props.payload.connection.connection_details.account = val.account;
      props.payload.connection.connection_details.role = val.role;
      props.payload.connection.connection_details.database = val.database;
      props.payload.connection.connection_details.schema = val.schema;
      props.payload.connection.connection_details.mfa_protected = val.mfa_protected || false;
    }
    if (val.type === 'redshift') {
      body = {
        type: val.type,
        connection: {
          user: val.user,
          password: val.password,
          database: val.database,
          schema: val.schema,
          host: val.host,
        },
      };
      props.payload.connection.connection_details.user = val.user;
      props.payload.connection.connection_details.password = val.password;
      props.payload.connection.connection_details.database = val.database;
      props.payload.connection.connection_details.schema = val.schema;
      props.payload.connection.connection_details.host = val.host;
    }
    if (val.type === 'databricks') {
      body = {
        type: val.type,
        connection: {
          schema: val.schema,
          host: val.host,
          http_path: val.http_path,
          token: val.token,
        },
      };
      props.payload.connection.connection_details.schema = val.schema;
      props.payload.connection.connection_details.host = val.host;
      props.payload.connection.connection_details.http_path = val.http_path;
      props.payload.connection.connection_details.token = val.token;
    }
    if (val.type === 'bigquery') {
      body = {
        type: val.type,
        connection: {
          dataset: val.dataset,
          keyfile_json: JSON.parse(val.keyfile_json),
        },
      };
      props.payload.connection.connection_details.dataset = val.dataset;
      props.payload.connection.connection_details.keyfile_json = JSON.parse(val.keyfile_json);
    }

    testDbMutation
      .mutateAsync({ body })
      .then(props.nextStep)
      .catch(() => {
        setSubmitting(false);
      });
    props.payload.connection.type = val.type;
    props.setPayload(props.payload);
  };

  return (
    <Formik
      initialValues={initialValues}
      validationSchema={Yup.object({
        type: Yup.string()
          .oneOf(['snowflake', 'redshift', 'databricks', 'bigquery'], 'Invalid Type')
          .required('Required'),
        account: Yup.string().when('type', {
          is: 'snowflake',
          then: Yup.string()
            .required('Required')
            .test(
              'no-snowflakecomputing',
              'Account should not contain snowflakecomputing.com',
              (value) => !value || !value.includes('snowflakecomputing.com')
            ),
          otherwise: Yup.string(),
        }),
        warehouse: Yup.string().when('type', {
          is: 'snowflake',
          then: Yup.string().required('Required'),
          otherwise: Yup.string(),
        }),
        database: Yup.string().when('type', {
          is: (val: string) => val === 'snowflake' || val === 'redshift',
          then: Yup.string().required('Required'),
          otherwise: Yup.string(),
        }),
        role: Yup.string().when('type', {
          is: 'snowflake',
          then: Yup.string().required('Required'),
          otherwise: Yup.string(),
        }),
        schema: Yup.string().when('type', {
          is: (val: string) => val === 'snowflake' || val === 'redshift' || val === 'databricks',
          then: Yup.string().required('Required'),
          otherwise: Yup.string(),
        }),
        user: Yup.string().when('type', {
          is: (val: string) => val === 'snowflake' || val === 'redshift',
          then: Yup.string().required('Required'),
          otherwise: Yup.string(),
        }),
        password: Yup.string().when('type', {
          is: (val: string) => val === 'snowflake' || val === 'redshift',
          then: Yup.string().required('Required'),
          otherwise: Yup.string(),
        }),
        host: Yup.string().when('type', {
          is: (val: string) => val === 'databricks' || val === 'redshift',
          then: Yup.string().required('Required'),
          otherwise: Yup.string(),
        }),
        token: Yup.string().when('type', {
          is: 'databricks',
          then: Yup.string().required('Required'),
          otherwise: Yup.string(),
        }),
        keyfile_json: Yup.string().when('type', {
          is: 'bigquery',
          then: Yup.string()
            .required('Required')
            .test('is-json-valid', 'Invalid JSON', (value) => value == null || isJsonString(value)),
          otherwise: Yup.string(),
        }),
        dataset: Yup.string().when('type', {
          is: 'bigquery',
          then: Yup.string().required('Required'),
          otherwise: Yup.string(),
        }),
        http_path: Yup.string().when('type', {
          is: 'databricks',
          then: Yup.string().required('Required'),
          otherwise: Yup.string(),
        }),
      })}
      onSubmit={handleSubmit}
    >
      <Form>
        <VStack width="full" spacing="6">
          <Text>
            This is the default database connection for all your services, you can configure each
            service’s connection later in the admin page.
          </Text>
          <SelectControl
            label="Type"
            name="type"
            selectProps={{ placeholder: 'Select type' }}
            onChange={handlerSelect}
            isRequired
          >
            <option value="snowflake">Snowflake</option>
            <option value="redshift">Redshift</option>
            <option value="databricks">Databricks</option>
            <option value="bigquery">Bigquery</option>
          </SelectControl>
          {valueState === 'snowflake' && (
            <>
              {showSnowflakeTrial && (
                <Notification
                  primaryAction={
                    <NotificationButton
                      colorScheme="blue"
                      as={Link}
                      href="https://trial.snowflake.com/?owner=SPN-PID-134352"
                      isExternal
                    >
                      Sign up
                    </NotificationButton>
                  }
                  secondaryAction={
                    <NotificationButton onClick={() => setShowSnowflakeTrial(false)}>
                      Dismiss
                    </NotificationButton>
                  }
                >
                  <Stack spacing="1">
                    <Heading as="h3" fontSize="md">
                      No Snowflake account?
                    </Heading>
                    <Text fontSize="sm">Sign up for a 30-days free trial account.</Text>
                  </Stack>
                </Notification>
              )}
              <Box w="full">
                <InputControl
                  name="account"
                  label="Snowflake Account"
                  inputProps={{ placeholder: account }}
                  isRequired
                />
                <Text color="gray.500" mt={1} fontSize="xs">
                  Subdomain of your login page url, i.e. <b>{account}</b> on https://
                  <b>{account}</b>
                  .snowflakecomputing.com, or <b>toa80739</b> on https://
                  <b>toa80739</b>
                  .snowflakecomputing.com
                </Text>
              </Box>
              <Box w="full">
                <SwitchControl
                  name="mfa_protected"
                  label="Is MFA protected"
                  onChange={(e) => setIsMfaEnabled((e.target as HTMLInputElement).checked)}
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
              <InputControl
                name="warehouse"
                label="Warehouse"
                inputProps={{ placeholder: 'TRANSFORMING_WAREHOUSE' }}
                isRequired
              />
              <InputControl
                name="database"
                label="Database"
                inputProps={{ placeholder: 'DATABASE' }}
                isRequired
              />
              <InputControl
                name="role"
                label="Role"
                inputProps={{ placeholder: 'ANALYST' }}
                isRequired
              />
              <InputControl
                name="schema"
                label="Schema"
                inputProps={{ placeholder: 'john' }}
                isRequired
              />
              <InputControl
                name="user"
                label="User"
                inputProps={{ placeholder: 'john' }}
                isRequired
              />
              <InputControl
                name="password"
                label="Password"
                inputProps={{ placeholder: '*******', type: 'password' }}
                isRequired
              />
            </>
          )}
          {valueState === 'redshift' && (
            <>
              <Box w="full">
                <InputControl
                  name="host"
                  label="Host"
                  inputProps={{
                    placeholder: 'default.xxxxxx.us-west-1.redshift-serverless.amazonaws.com',
                  }}
                  isRequired
                />
              </Box>
              <InputControl
                name="database"
                label="Database"
                inputProps={{ placeholder: 'DATABASE' }}
                isRequired
              />
              <InputControl
                name="user"
                label="User"
                inputProps={{ placeholder: 'john' }}
                isRequired
              />
              <InputControl
                name="schema"
                label="Schema"
                inputProps={{ placeholder: 'john' }}
                isRequired
              />
              <InputControl
                name="password"
                label="Password"
                inputProps={{ placeholder: '*******', type: 'password' }}
                isRequired
              />
            </>
          )}
          {valueState === 'databricks' && (
            <>
              <Box w="full">
                <InputControl
                  name="host"
                  label="Host"
                  inputProps={{
                    placeholder: 'xxx-123.azuredatabricks.net',
                  }}
                  isRequired
                />
              </Box>
              <InputControl
                name="http_path"
                label="HTTP Path"
                inputProps={{ placeholder: '/sql/1.0/warehouses/xxx123' }}
                isRequired
              />
              <InputControl
                name="schema"
                label="Schema"
                inputProps={{ placeholder: 'john' }}
                isRequired
              />
              <InputControl
                name="token"
                label="Token"
                inputProps={{ placeholder: '*******', type: 'password' }}
                isRequired
              />
            </>
          )}
          {valueState === 'bigquery' && (
            <>
              <InputControl
                name="dataset"
                label="Dataset"
                inputProps={{ placeholder: 'DATASET' }}
                isRequired
              />
              <TextareaControl
                name="keyfile_json"
                label="Keyfile content"
                isRequired
              ></TextareaControl>
            </>
          )}
        </VStack>
        {isMfaEnabled && (
          <Box mt={5}>
            <ConnectionMFAWarningAlert />
          </Box>
        )}
        <HStack mt={6}>
          <Button size="sm" onClick={props.prevStep} variant="ghost">
            Back
          </Button>
          <Button type="submit" colorScheme="green" size="sm" isLoading={testDbMutation.isLoading}>
            Next
          </Button>
        </HStack>
        {testDbMutation.isLoading && (
          <TestConnectionProgress infoText="Datacoves will connect from 40.76.152.251. Allow inbound traffic from this IP, and include it in any database grants." />
        )}
      </Form>
    </Formik>
  );
};
