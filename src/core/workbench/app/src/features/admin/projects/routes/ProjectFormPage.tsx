import { WarningTwoIcon } from '@chakra-ui/icons';
import {
  Box,
  Button,
  FormLabel,
  HStack,
  Stack,
  StackDivider,
  Textarea,
  useToast,
  Text,
  VStack,
  Tooltip,
} from '@chakra-ui/react';
import { Formik, Form } from 'formik';
import { FormControl, InputControl, SelectControl, SwitchControl } from 'formik-chakra-ui';
import React, { createElement, useContext, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';

import { BasePage } from '../../../../components/AdminLayout';
import ExpandibleToast from '../../../../components/ExpandibleToast/ExpandibleToast';
import { FieldGroup } from '../../../../components/FieldGroup';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { UserContext } from '../../../../context/UserContext';
import { EnvironmentVariablesDeletable, Project } from '../../../../context/UserContext/types';
import { objectMap } from '../../../../utils/inlineListEditable';
import { useSSHKey } from '../../../global/api/getSshKey';
import { useSSLKey } from '../../../global/api/getSslKey';
import { useTestGitConnection } from '../../../global/api/testGitConnection';
import { SSHKey, SSLKey } from '../../../global/types';
import { EnvironmentVariableModal } from '../../environments/components/EnvironmentVariableModal';
import { EnvironmentVariablesTable } from '../../environments/components/EnvironmentVariablesTable';
import { useCreateProject } from '../api/createProject';
import { useProject } from '../api/getProjectById';
import { useUpdateProject } from '../api/updateProject';

export const ProjectFormPage = () => {
  const { id } = useParams();
  const isCreateMode = id === undefined;
  const { currentAccount } = useContext(AccountContext);
  const { currentUser } = useContext(UserContext);
  const [secretBackendConfigErrorState, setSecretBackendConfigErrorState] =
    useState<boolean>(false);
  const [currentCIProvider, setCurrentCIProvider] = useState<string>();
  const [currentSecretsSecondaryBackend, setCurrentSecretsSecondaryBackend] = useState<string>();
  const [originalSecretsSecondaryBackend, setOriginalSecretsSecondaryBackend] = useState<string>();
  const [currentCloneStrategy, setCurrentCloneStrategy] = useState<string>();
  const [currentSSHKey, setCurrentSSHKey] = useState<SSHKey>();
  const [currentPEM, setCurrentPEM] = useState<SSLKey>();
  const [environmentVariables, setEnvironmentVariables] = useState<EnvironmentVariablesDeletable>(
    {}
  );
  const toast = useToast();

  // Default 'help text' for our secondary secrets config
  const defaultSecondarySecretsConfig = `{
  "connections_prefix": "airflow/connections",
  "connections_lookup_pattern": null,
  "variables_prefix": "airflow/variables",
  "variables_lookup_pattern": null,
  "aws_access_key_id": "xxx",
  "aws_secret_access_key": "xxx",
  "region_name": "xxx"
}`;

  const [currentSecretsSecondaryBackendConfig, setCurrentSecretsSecondaryBackendConfig] =
    useState<string>(defaultSecondarySecretsConfig);

  useSSHKey('project', {
    enabled: currentCloneStrategy === 'ssh_clone' && currentSSHKey === undefined,
    onSuccess: (key: SSHKey) => {
      setCurrentSSHKey(key);
    },
  });

  useSSLKey('azure', {
    enabled: currentCloneStrategy === 'azure_certificate_clone' && currentPEM === undefined,
    onSuccess: (key: SSLKey) => {
      setCurrentPEM(key);
    },
  });

  const copyToClipboard = (to_copy: string) => {
    navigator.clipboard.writeText(to_copy);
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

  const initialValues = {
    name: '',
    clone_strategy: '',
    git_url: '',
    url: '',
    release_branch: '',
    release_branch_protected: false,
    git_username: '',
    ci_provider: '',
    ci_home_url: '',
    variables: {},
    dbt_profile: '',
    secrets_secondary_backend: '',
    secrets_secondary_backend_config: '',
    azure_tenant: '',
  };
  const createMutation = useCreateProject();
  const updateMutation = useUpdateProject();
  const testGitMutation = useTestGitConnection(true);
  const navigate = useNavigate();

  const handleSubmit = (body: any) => {
    body.repository = {
      git_url: body.git_url,
      url: body.url,
    };

    if (currentCloneStrategy === 'http_clone') {
      if (body.git_password) {
        body.deploy_credentials = {
          git_username: body.git_username,
          git_password: body.git_password,
        };
      }

      body.deploy_key = null;
    } else if (currentCloneStrategy === 'ssh_clone') {
      body.deploy_credentials = {};
      if (currentSSHKey) {
        body.deploy_key = currentSSHKey.id;
      }
    } else if (currentCloneStrategy === 'azure_secret_clone') {
      if (body.git_password) {
        body.deploy_credentials = {
          git_username: body.git_username,
          git_password: body.git_password,
          azure_tenant: body.azure_tenant,
        };
      }
    } else {
      body.deploy_credentials = {
        azure_tenant: body.azure_tenant,
        git_username: body.git_username,
      };

      if (currentPEM) {
        body.azure_deploy_key = currentPEM.id;
      }
    }

    // I don't care, sorry.
    // prettier-ignore
    if ((isCreateMode && currentSecretsSecondaryBackendConfig) ||
        (!isCreateMode && (originalSecretsSecondaryBackend != currentSecretsSecondaryBackend))) {
        body.secrets_secondary_backend_config = currentSecretsSecondaryBackendConfig;
    }

    body.variables = objectMap(environmentVariables, (v) => (v.delete ? undefined : v.value));
    body.settings = body.dbt_profile
      ? {
          dbt_profile: body.dbt_profile,
        }
      : {};
    if (currentAccount?.slug !== undefined) {
      if (isCreateMode) {
        createMutation.mutateAsync({ account: currentAccount?.slug, body }).then((record: any) => {
          testGitMutation.mutateAsync({ project_id: parseInt(record.id) }).finally(() => {
            navigate('/admin/projects');
          });
        });
      } else {
        updateMutation
          .mutateAsync({
            account: currentAccount?.slug,
            id,
            body,
          })
          .then((record: any) => {
            testGitMutation.mutateAsync({ project_id: parseInt(record.id) }).finally(() => {
              navigate('/admin/projects');
            });
          });
      }
    }
  };
  return (
    <BasePage header={id ? 'Edit project' : 'Create project'}>
      <Box p="10" w="full">
        <Stack spacing="4" divider={<StackDivider />}>
          <Formik
            key={id}
            initialValues={initialValues}
            validationSchema={Yup.object({
              name: Yup.string().required('Required'),
              git_url: Yup.string()
                .matches(/^.*:(.*)\/(.*)/, 'Enter a valid ssh git repository url')
                .required('Required'),
              release_branch: Yup.string().required('Required'),
              release_branch_protected: Yup.boolean(),
              clone_strategy: Yup.string().required('Required'),
              url: Yup.string().when({
                is: () => currentCloneStrategy === 'http_clone',
                then: Yup.string()
                  .matches(
                    /https(:(\/\/)?)([\w.@:/\-~]+)(\.git)(\/)?/,
                    'Enter a valid https git repository url'
                  )
                  .required('Required'),
                otherwise: Yup.string().nullable(),
              }),
              git_username: Yup.string().when({
                is: () =>
                  currentCloneStrategy === 'http_clone' ||
                  (currentCloneStrategy && currentCloneStrategy.startsWith('azure_')),
                then: Yup.string().required('Required'),
                otherwise: Yup.string(),
              }),
              git_password: Yup.string().when({
                is: () =>
                  isCreateMode &&
                  (currentCloneStrategy === 'http_clone' ||
                    currentCloneStrategy === 'azure_secret_clone'),
                then: Yup.string().required('Required'),
                otherwise: Yup.string(),
              }),
              dbt_profile: Yup.string().matches(/^[a-zA-Z0-9_]*$/, 'Invalid dbt profile name'),
              azure_tenant: Yup.string().when({
                is: () => currentCloneStrategy && currentCloneStrategy.startsWith('azure_'),
                then: Yup.string().required('Required'),
                otherwise: Yup.string().nullable(),
              }),
              // Prettier is arguing back and forth about the same line,
              // I have no idea what it wants.
              // prettier-ignore
              secrets_secondary_backend_config: Yup.string().when({
                is: () => (isCreateMode && currentSecretsSecondaryBackend) ||
                  (!isCreateMode && currentSecretsSecondaryBackend != originalSecretsSecondaryBackend),
                then: Yup.string()
                  .test(
                    "json",
                    "Invalid JSON format",
                    () => {
                      if (!currentSecretsSecondaryBackendConfig) {
                        return false;
                      }

                      try {
                        JSON.parse(currentSecretsSecondaryBackendConfig ?? '');
                        setSecretBackendConfigErrorState(false);
                        return true;
                      } catch (error) {
                        setSecretBackendConfigErrorState(true);
                        return false;
                      }
                    }
                  ),
                otherwise: Yup.string().nullable(),
              }),
            })}
            onSubmit={handleSubmit}
          >
            {function Render({ setFieldValue }) {
              const { data, isSuccess, isLoading } = useProject(currentAccount?.slug, id, {
                enabled: currentAccount?.slug !== undefined && id !== undefined,
                onSuccess: (data: Project) => {
                  setFieldValue('name', data.name);
                  setFieldValue('git_url', data.repository.git_url);
                  setFieldValue('url', data.repository.url);
                  setFieldValue('release_branch', data.release_branch);
                  setFieldValue('release_branch_protected', data.release_branch_protected);
                  setFieldValue('ci_provider', data.ci_provider ?? '');
                  setCurrentCIProvider(data.ci_provider ?? '');
                  setFieldValue('ci_home_url', data.ci_home_url ?? '');
                  setFieldValue('git_username', data.deploy_credentials.git_username);
                  if (data.public_ssh_key) {
                    setCurrentSSHKey({ id: data.deploy_key, ssh_key: data.public_ssh_key });
                  }

                  if (data.public_azure_key) {
                    setCurrentPEM({ id: data.azure_deploy_key, ssl_key: data.public_azure_key });
                  }

                  setFieldValue('clone_strategy', data.clone_strategy);
                  setCurrentCloneStrategy(data.clone_strategy);
                  setEnvironmentVariables(
                    objectMap(data.variables, (v: string) => {
                      return { value: v, delete: false };
                    })
                  );
                  setFieldValue('dbt_profile', data.settings.dbt_profile);
                  setFieldValue('secrets_secondary_backend', data.secrets_secondary_backend ?? '');
                  setCurrentSecretsSecondaryBackend(data.secrets_secondary_backend);
                  setOriginalSecretsSecondaryBackend(data.secrets_secondary_backend);

                  if (!data.secrets_secondary_backend) {
                    setCurrentSecretsSecondaryBackendConfig(defaultSecondarySecretsConfig);
                  }

                  setFieldValue('azure_tenant', data.deploy_credentials.azure_tenant);
                },
              });

              // Prettier can't handle the long lines on the options select
              // boxes.
              // prettier-ignore
              return (
                <LoadingWrapper
                  isLoading={!isCreateMode && isLoading}
                  showElements={isCreateMode || (data && isSuccess)}
                >
                  <Form>
                    <FieldGroup title="Basic Info">
                      <VStack width="full" spacing="6" alignItems="flex-start">
                        <InputControl name="name" label="Name" isRequired />
                      </VStack>
                    </FieldGroup>
                    <FieldGroup title="Git Repo">
                      <VStack width="full" spacing="6">
                        <HStack w="full" alignItems="flex-start">
                          <SelectControl
                            label="Clone strategy"
                            name="clone_strategy"
                            selectProps={{ placeholder: 'Select clone strategy' }}
                            onChange={(event: any) => setCurrentCloneStrategy(event.target.value)}
                            w="sm"
                            isRequired
                          >
                            <option value="ssh_clone">SSH</option>
                            <option value="http_clone">HTTPS</option>
                            <option value="azure_secret_clone">Azure DevOps Secret</option>
                            <option value="azure_certificate_clone">
                              Azure DevOps Certificate
                            </option>
                          </SelectControl>
                          <Box w="full">
                            <InputControl
                              name="git_url"
                              label="Git SSH url"
                              isRequired
                              isReadOnly={!isCreateMode}
                              inputProps={{ isDisabled: !isCreateMode }}
                            />
                            {!isCreateMode && (
                              <Text color="gray.500" mt={1} fontSize="xs">
                                It is not possible to change the repository, if needed, create a new
                                project with the new repo information
                              </Text>
                            )}
                          </Box>
                        </HStack>
                        {currentCloneStrategy === 'http_clone' && (
                          <>
                            <Box w="full">
                              <InputControl
                                name="url"
                                label="Git HTTPS url"
                                isRequired
                                isReadOnly={!isCreateMode}
                                inputProps={{ isDisabled: !isCreateMode }}
                              />
                              {!isCreateMode && (
                                <Text color="gray.500" mt={1} fontSize="xs">
                                  It is not possible to change the repository, if needed, create a
                                  new project with the new repo information
                                </Text>
                              )}
                            </Box>
                            <HStack w="full">
                              <InputControl name="git_username" label="Username" isRequired />
                              <InputControl
                                name="git_password"
                                label="Password"
                                inputProps={{ placeholder: '*******', type: 'password' }}
                              />
                            </HStack>
                          </>
                        )}
                        {currentCloneStrategy === 'ssh_clone' && currentSSHKey && (
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
                                onClick={() => copyToClipboard(currentSSHKey.ssh_key)}
                              >
                                COPY
                              </Button>
                            </Stack>
                            <FormLabel htmlFor="key_value">Public SSH key</FormLabel>
                            <Textarea
                              name="key_value"
                              isReadOnly={true}
                              value={currentSSHKey.ssh_key}
                              isRequired
                            />
                            <Text color="gray.500" mt={1} fontSize="xs">
                              This is an auto-generated public SSH key. Copy it and configure it in
                              your git provider.
                            </Text>
                          </VStack>
                        )}
                        {currentCloneStrategy === 'azure_secret_clone' && (
                          <>
                            <Box w="full">
                              <InputControl
                                name="url"
                                label="Azure HTTPS Clone URL"
                                isRequired
                                isReadOnly={!isCreateMode}
                                inputProps={{ isDisabled: !isCreateMode }}
                              />
                              {!isCreateMode && (
                                <Text color="gray.500" mt={1} fontSize="xs">
                                  It is not possible to change the repository, if needed, create a
                                  new project with the new repo information
                                </Text>
                              )}
                            </Box>
                            <VStack w="full">
                              <InputControl name="azure_tenant" label="Tenant ID" isRequired />
                              <InputControl
                                name="git_username"
                                label="App ID or Username"
                                isRequired
                              />
                              <InputControl
                                name="git_password"
                                label="Client Secret or Password"
                                inputProps={{ placeholder: '*******', type: 'password' }}
                              />
                            </VStack>
                          </>
                        )}
                        {currentCloneStrategy === 'azure_certificate_clone' && currentPEM && (
                          <>
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
                                  onClick={() => copyToClipboard(currentPEM.ssl_key)}
                                >
                                  COPY
                                </Button>
                              </Stack>
                              <FormLabel htmlFor="key_value">Certificate PEM File</FormLabel>
                              <Textarea
                                name="key_value"
                                isReadOnly={true}
                                value={currentPEM.ssl_key}
                                isRequired
                              />
                              <Text color="gray.500" mt={1} fontSize="xs">
                                This is an auto-generated certificate. Copy it and configure it in
                                Azure Entra ID.
                              </Text>
                              <InputControl
                                name="url"
                                label="Azure HTTPS Clone URL"
                                isRequired
                                isReadOnly={!isCreateMode}
                                inputProps={{ isDisabled: !isCreateMode }}
                              />
                              {!isCreateMode && (
                                <Text color="gray.500" mt={1} fontSize="xs">
                                  It is not possible to change the repository, if needed, create a
                                  new project with the new repo information
                                </Text>
                              )}
                              <InputControl name="azure_tenant" label="Tenant ID" isRequired />
                              <InputControl
                                name="git_username"
                                label="App ID or Username"
                                isRequired
                              />
                            </VStack>
                          </>
                        )}
                        <FormControl id="release_branch" name="release_branch" isRequired>
                          <FormLabel>Release Branch</FormLabel>
                          <HStack w="50">
                            <InputControl name="release_branch" isRequired />
                            <Tooltip label="Prevent commits to this branch">
                              <SwitchControl
                                name="release_branch_protected"
                                label="Prevent commits"
                                whiteSpace="nowrap"
                              />
                            </Tooltip>
                          </HStack>
                        </FormControl>
                      </VStack>
                    </FieldGroup>
                    <FieldGroup title="CI / CD">
                      <VStack width="full" spacing="6">
                        <HStack w="full" alignItems="flex-start">
                          <SelectControl
                            label="Provider"
                            name="ci_provider"
                            selectProps={{ placeholder: 'Select provider' }}
                            onChange={(event: any) => setCurrentCIProvider(event.target.value)}
                            w="sm"
                          >
                            <option value="github">GitHub</option>
                            <option value="gitlab">GitLab</option>
                            <option value="bitbucket">Bitbucket</option>
                            <option value="azure_devops">Azure DevOps</option>
                            <option value="circleci">CircleCI</option>
                            <option value="bamboo">Bamboo</option>
                            <option value="other">Other</option>
                          </SelectControl>
                          <Box w="full">
                            {currentCIProvider && (
                              <InputControl name="ci_home_url" label="Jobs home url" />
                            )}
                          </Box>
                        </HStack>
                      </VStack>
                    </FieldGroup>
                    <FieldGroup title="dbt">
                      <Box w="full">
                        <InputControl
                          name="dbt_profile"
                          label="Profile name"
                          inputProps={{ placeholder: 'default' }}
                        />
                        <Text color="gray.500" mt={1} fontSize="xs">
                          dbt profile name as defined in dbt_project.yml with the key <b>profile</b>
                        </Text>
                      </Box>
                    </FieldGroup>
                    {currentUser?.features.admin_secrets && (
                      <FieldGroup title="Secrets">
                        <VStack width="full" spacing="6" alignItems="flex-start">
                          <VStack w="full" alignItems="flex-start">
                            <SelectControl
                              label="Additional Secrets Backend"
                              name="secrets_secondary_backend"
                              selectProps={{ placeholder: 'None' }}
                              onChange={(event: any) =>
                                setCurrentSecretsSecondaryBackend(event.target.value)
                              }
                              w="sm"
                            >
                              <option
                                value="airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend"
                              >
                                AWS Secrets Manager
                              </option>
                            </SelectControl>
                            <Text color="gray.500" mt={1} fontSize="xs">
                              Secrets backend used to store confidential data, including Airflow
                              variables/connections and other secrets.
                            </Text>
                          </VStack>
                          {currentSecretsSecondaryBackend  && currentSecretsSecondaryBackend.length && (
                            <>
                              {isCreateMode || originalSecretsSecondaryBackend != currentSecretsSecondaryBackend ? (
                                <VStack w="full" alignItems="flex-start">
                                  <HStack w="full" alignItems="flex-start">
                                    <Textarea
                                      name="secrets_secondary_backend_config"
                                      value={currentSecretsSecondaryBackendConfig}
                                      rows={10}
                                      onChange={(ev) => setCurrentSecretsSecondaryBackendConfig(ev.target.value)}
                                    />
                                  </HStack>
                                  <Text color="gray.500" mt={1} fontSize="xs">
                                    This is some JSON configuration that can be found
                                    in the Airflow documentation
                                    <a
                                      href="https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/secrets-backends/index.html"
                                      target="_blank"
                                      rel="noreferrer"
                                    >
                                      here
                                    </a>.
                                  </Text>
                                  {secretBackendConfigErrorState && (
                                    <Text mt={1} fontSize="md" color="red">
                                      This must be valid JSON.
                                    </Text>
                                  )}
                                </VStack>
                              ) : (
                                <VStack w="full" alignItems="flex-start">
                                  <Text mt={1} fontSize="xs">
                                    Because your secret manager settings probably
                                    contain credentials, you cannot edit them. If
                                    you wish to change them, then please change
                                    the secrets backend type to &quot;None&quot;,
                                    save, and then come back and start over. If
                                    you need help, contact
                                    <a
                                      href="mailto:support@datacoves.com"
                                    >
                                      support@datacoves.com
                                    </a>
                                    or contact us via slack.
                                  </Text>
                                </VStack>
                              )}
                            </>
                          )}
                        </VStack>
                      </FieldGroup>
                    )}
                    {currentUser?.features.admin_code_server_environment_variables && (
                      <FieldGroup title="VS Code Environment Variables">
                        <VStack width="full" spacing="6">
                          <HStack w="full" justifyContent="flex-end">
                            <EnvironmentVariableModal
                              setVariables={setEnvironmentVariables}
                              variables={environmentVariables}
                            />
                          </HStack>
                          <HStack w="full">
                            <EnvironmentVariablesTable
                              setVariables={setEnvironmentVariables}
                              variables={environmentVariables}
                            />
                          </HStack>
                        </VStack>
                      </FieldGroup>
                    )}
                    <HStack width="full" justifyContent="flex-end" spacing="6" pt="10">
                      {(updateMutation.isLoading ||
                        testGitMutation.isLoading ||
                        createMutation.isLoading) && (
                        <Text flex="1" textAlign="right" pr="5">
                          Testing git connection...
                        </Text>
                      )}
                      {!updateMutation.isLoading &&
                        !testGitMutation.isLoading &&
                        !createMutation.isLoading &&
                        !isCreateMode && (
                          <HStack spacing="1">
                            <WarningTwoIcon color="orange.400" />
                            <Text m="0">
                              Saving changes could result in users&apos; environments being
                              restarted.
                            </Text>
                          </HStack>
                        )}
                      <Button onClick={() => navigate('/admin/projects')}>Cancel</Button>
                      <Button
                        type="submit"
                        colorScheme="blue"
                        isLoading={
                          updateMutation.isLoading ||
                          createMutation.isLoading ||
                          testGitMutation.isLoading
                        }
                      >
                        Save Changes
                      </Button>
                    </HStack>
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
