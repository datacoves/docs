import { WarningIcon, WarningTwoIcon } from '@chakra-ui/icons';
import {
  Box,
  Stack,
  Text,
  StackDivider,
  Button,
  HStack,
  Tabs,
  TabPanels,
  TabPanel,
  VStack,
} from '@chakra-ui/react';
import { Formik, Form, FormikErrors } from 'formik';
import { isEmpty } from 'lodash';
import { useContext, useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';

import { BasePage } from '../../../../components/AdminLayout';
import { FormTabs } from '../../../../components/FormTabs';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { UserContext } from '../../../../context/UserContext';
import {
  Environment,
  EnvironmentIntegration,
  EnvironmentVariablesDeletable,
  Project,
} from '../../../../context/UserContext/types';
import { objectMap } from '../../../../utils/inlineListEditable';
import { useAllIntegrations } from '../../integrations/api/getIntegrations';
import { useDependantProject } from '../../projects/api/getProjectById';
import { useAllProjects } from '../../projects/api/getProjects';
import { useCreateEnvironment } from '../api/createEnvironment';
import { useAdaptersDefaultValues } from '../api/getAirflowDefault';
import { useEnvironment } from '../api/getEnvironmentById';
import { useUpdateEnvironment } from '../api/updateEnvironment';
import { findErrorTab, getFormSections, getLabels, getTabs } from '../components/utils';

export const EnvironmentFormPage = () => {
  const { id } = useParams();
  const isCreateMode = id === undefined;
  const { currentAccount } = useContext(AccountContext);
  const { currentUser } = useContext(UserContext);

  const { data: adaptersDefaultValues } = useAdaptersDefaultValues();
  const airflowDefaultConfig = adaptersDefaultValues?.airflow;

  const [tabIndex, setTabIndex] = useState(0);
  const [currentType, setCurrentType] = useState<string>();
  const [currentError, setCurrentError] = useState<string>();
  const [orchestrateSelected, setOrchestrateSelected] = useState<boolean>();
  const [docsSelected, setDocsSelected] = useState<boolean>();
  const [integrationsSelected, setIntegrationsSelected] = useState<EnvironmentIntegration[]>([]);
  const [environmentVariables, setEnvironmentVariables] = useState<EnvironmentVariablesDeletable>(
    {}
  );
  const [dagsSource, setDagsSource] = useState<string>();
  const [dagSyncAuth, setDagSyncAuth] = useState<string>();
  const [airflowLogsBackend, setAirflowLogsBackend] = useState<string>();
  const [airflowLogsExternal, setAirflowLogsExternal] = useState<boolean>();

  const initialValues = {
    name: '',
    project: '',
    type: '',
    release_profile: '',
    dbt_home_path: '',
    dbt_profiles_dir: 'automate/dbt',
    airflow_config: {
      git_branch: airflowDefaultConfig?.git_branch,
      dags_folder: airflowDefaultConfig?.dags_folder,
      yaml_dags_folder: airflowDefaultConfig?.yaml_dags_folder,
      dags_source: '',
      s3_sync: { wait: 60 },
      logs: {
        backend: airflowDefaultConfig?.logs?.backend,
        access_key: '',
        secret_key: '',
        s3_log_bucket: airflowDefaultConfig?.logs?.s3_log_bucket,
        external: airflowDefaultConfig?.logs?.external,
      },
      ...(!!currentUser?.features.admin_env_airflow_mem_and_cpu_resources && {
        resources: airflowDefaultConfig?.resources,
      }),
    },
    dbt_docs_config: {
      git_branch: 'dbt-docs',
    },
    variables: {},
    dbt_profile: '',
    project_dbt_profile: '',
    override_dbt_profile: '',
    code_server_config: {
      resources: adaptersDefaultValues?.['code-server'].resources,
    },
    services: {
      'code-server': { enabled: false },
      'dbt-docs': { enabled: false },
      airbyte: { enabled: false },
      airflow: { enabled: false },
      superset: { enabled: false },
    },
  };

  const {
    data: projects,
    isSuccess: projectsSuccess,
    isLoading: isLoadingProjects,
  } = useAllProjects({
    account: currentAccount?.slug,
  });

  const {
    data: integrations,
    isSuccess: integrationsSuccess,
    isLoading: isLoadingIntegrations,
  } = useAllIntegrations({
    account: currentAccount?.slug,
  });

  useEffect(() => {
    if (integrations) {
      const defaultIntegrations = integrations.filter((integration) => integration.is_default);
      if (defaultIntegrations.length > 0 && isCreateMode) {
        setIntegrationsSelected(
          defaultIntegrations.map((integration) => ({
            service: 'airflow',
            integration: integration.id,
            type: integration.type,
            is_notification: integration.is_notification ?? false,
          }))
        );
      }
    }
  }, [integrations, isCreateMode]);

  const handleSelectType = (event: any) => {
    setCurrentType(event.target.value);
  };

  const handleChangeOrchestrate = (event: any) => {
    setOrchestrateSelected(event.target.checked);
  };

  const handleChangeDocs = (event: any) => {
    setDocsSelected(event.target.checked);
  };

  const handleSelectDagsSource = (event: any) => {
    setDagsSource(event.target.value);
  };

  const handleSelectDagSyncAuth = (event: any) => {
    setDagSyncAuth(event.target.value);
  };

  const handleSelectLogsBackend = (event: any) => {
    setAirflowLogsBackend(event.target.value || 'minio');
    setAirflowLogsExternal(!!event.target.value);
  };

  const createMutation = useCreateEnvironment();
  const updateMutation = useUpdateEnvironment();

  const handleSubmit = (body: any, { setSubmitting }: any) => {
    delete body.project_dbt_profile;
    delete body.override_dbt_profile;
    if (currentType !== 'dev') {
      if ('services' in body && 'code-server' in body.services) {
        body.services['code-server'].enabled = false;
      }
    }
    const enabledService = Object.keys(body.services ?? {}).find(
      (serviceKey) => body.services[serviceKey].enabled
    );
    if (enabledService) {
      setCurrentError(undefined);
    } else {
      setSubmitting(false);
      setTabIndex(1);
      setCurrentError('Please select at least one Stack Service');
      return;
    }
    if (!orchestrateSelected) {
      body.airflow_config = {};
    } else {
      if (dagsSource === 's3') {
        if (dagSyncAuth === 'iam-user') {
          body.airflow_config.s3_sync.iam_role = '';
        } else if (dagSyncAuth === 'iam-role') {
          body.airflow_config.s3_sync.access_key = '';
          body.airflow_config.s3_sync.secret_key = '';
        }
      }
      if (airflowLogsBackend) {
        body.airflow_config.logs.backend = airflowLogsBackend;
        body.airflow_config.logs.external = airflowLogsExternal;
      }
    }
    if (!docsSelected) {
      body.dbt_docs_config = {};
    }
    if (!body.services['code-server'].enabled) {
      body.code_server_config = {};
    }
    body.integrations = integrationsSelected;
    body.variables = objectMap(environmentVariables, (v) => (v.delete ? undefined : v.value));

    body.settings = body.dbt_profile
      ? {
          dbt_profile: body.dbt_profile,
        }
      : { dbt_profile: 'default' };

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
  };

  const navigate = useNavigate();

  const goToNextSection = () => {
    setTabIndex((prev) => prev + 1);
  };

  const handleTabsChange = (index: number) => {
    setTabIndex(index);
  };

  return (
    <BasePage header={isCreateMode ? 'Create environment' : 'Edit environment'}>
      {integrationsSuccess && projectsSuccess && (
        <Box p="10" w="full">
          <Stack spacing="4" divider={<StackDivider />}>
            <Formik
              key={id}
              initialValues={initialValues}
              validationSchema={Yup.object({
                name: Yup.string().required('Required'),
                project: Yup.string().required('Required'),
                type: Yup.string().required('Required'),
                release_profile: Yup.string().required('Required'),
                dbt_profiles_dir: Yup.string().when({
                  is: () => orchestrateSelected,
                  then: Yup.string().required('Required'),
                  otherwise: Yup.string(),
                }),
                airflow_config: Yup.object().when({
                  is: () => orchestrateSelected,
                  then: Yup.object({
                    git_branch: Yup.string().when({
                      is: () => dagsSource === 'git',
                      then: Yup.string().required('Required'),
                      otherwise: Yup.string(),
                    }),
                    dags_folder: Yup.string().required('Required'),
                    yaml_dags_folder: Yup.string().required('Required'),
                    dags_source: Yup.string().required('Required').nullable(),
                    s3_sync: Yup.object().when({
                      is: () => dagsSource === 's3',
                      then: Yup.object({
                        path: Yup.string().required('Required'),
                        access_key: Yup.string().when({
                          is: () => dagSyncAuth === 'iam-user',
                          then: Yup.string().required('Required'),
                          otherwise: Yup.string(),
                        }),
                        secret_key: Yup.string().when({
                          is: () => dagSyncAuth === 'iam-user',
                          then: Yup.string().required('Required'),
                          otherwise: Yup.string(),
                        }),
                        iam_role: Yup.string().when({
                          is: () => dagSyncAuth === 'iam-role',
                          then: Yup.string().required('Required'),
                          otherwise: Yup.string(),
                        }),
                      }),
                      otherwise: Yup.object(),
                    }),
                    logs: Yup.object().when({
                      is: () => airflowLogsExternal,
                      then: Yup.object({
                        s3_log_bucket: Yup.string().when({
                          is: () => airflowLogsBackend === 's3',
                          then: Yup.string().required('Required'),
                          otherwise: Yup.string(),
                        }),
                        access_key: Yup.string().when({
                          is: () => airflowLogsBackend === 's3',
                          then: Yup.string().required('Required'),
                          otherwise: Yup.string(),
                        }),
                        secret_key: Yup.string().when({
                          is: () => airflowLogsBackend === 's3',
                          then: Yup.string().required('Required'),
                          otherwise: Yup.string(),
                        }),
                        volume_handle: Yup.string().when({
                          is: () => airflowLogsBackend === 'efs',
                          then: Yup.string().required('Required'),
                          otherwise: Yup.string(),
                        }),
                      }),
                    }),
                  }),
                  otherwise: Yup.object(),
                }),
                dbt_docs_config: Yup.object().when({
                  is: () => docsSelected,
                  then: Yup.object({
                    git_branch: Yup.string().required('Required'),
                  }),
                  otherwise: Yup.object(),
                }),
                dbt_profile: Yup.string().matches(/^[a-zA-Z0-9_]*$/, 'Invalid dbt profile name'),
                dag_s3_auth: Yup.string().when({
                  is: () =>
                    dagsSource === 's3' && !currentUser?.has_dynamic_blob_storage_provisioning,
                  then: Yup.string().required('Required'),
                }),
                integrations: Yup.array()
                  .test('is-notification', 'Only one notification integration is allowed', () => {
                    const hasTeams = integrationsSelected.some((it) => it.type === 'msteams');
                    const hasSlack = integrationsSelected.some((it) => it.type === 'slack');
                    if (hasTeams && hasSlack) {
                      setCurrentError(
                        'Slack and MS Teams integrations cannot be used at the same time'
                      );
                      return false;
                    }
                    return true;
                  })
                  .test('no-duplicate', 'Cannot add the same integration multiple times', () => {
                    const integrationIds = integrationsSelected.map((item) =>
                      String(item.integration)
                    );
                    const uniqueIds = new Set(integrationIds);
                    const isValid = uniqueIds.size == integrationIds.length;
                    if (!isValid) {
                      setCurrentError('Cannot add the same integration multiple times');
                    }
                    return isValid;
                  }),
              })}
              onSubmit={handleSubmit}
            >
              {function Render({
                setFieldValue,
                validateForm,
                submitForm,
                handleChange,
                isValidating,
                isValid,
                errors,
                values,
                touched,
                setFieldTouched,
              }) {
                const { data, isSuccess, isLoading } = useEnvironment(currentAccount?.slug, id, {
                  enabled: currentAccount?.slug !== undefined && id !== undefined && !isCreateMode,
                  onSuccess: async (data: Environment) => {
                    setFieldValue('name', data.name);
                    setFieldValue('project', data.project);
                    setFieldValue('type', data.type);
                    setFieldValue('release_profile', data.release_profile);
                    setFieldValue(
                      'services.code-server.enabled',
                      data.services['code-server']?.enabled
                    );
                    setFieldValue('services.dbt-docs.enabled', data.services['dbt-docs']?.enabled);
                    setFieldValue('services.airbyte.enabled', data.services.airbyte?.enabled);
                    setFieldValue('services.airflow.enabled', data.services.airflow?.enabled);
                    setOrchestrateSelected(data.services.airflow?.enabled);
                    setFieldValue('services.superset.enabled', data.services.superset?.enabled);
                    setCurrentType(data.type);
                    setFieldValue('dbt_home_path', data.dbt_home_path);
                    setFieldValue('dbt_profiles_dir', data.dbt_profiles_dir);
                    if (data.airflow_config.git_branch) {
                      setFieldValue('airflow_config.git_branch', data.airflow_config.git_branch);
                    }
                    if (data.airflow_config.dags_folder) {
                      setFieldValue('airflow_config.dags_folder', data.airflow_config.dags_folder);
                    }
                    if (data.airflow_config.yaml_dags_folder) {
                      setFieldValue(
                        'airflow_config.yaml_dags_folder',
                        data.airflow_config.yaml_dags_folder
                      );
                    }
                    if (data.airflow_config.dags_source) {
                      setDagsSource(data.airflow_config.dags_source);
                      setFieldValue('airflow_config.dags_source', data.airflow_config.dags_source);
                    }
                    if (data.dbt_docs_config.git_branch) {
                      setFieldValue('dbt_docs_config.git_branch', data.dbt_docs_config.git_branch);
                    }
                    setDocsSelected(data.services['dbt-docs']?.enabled);
                    // Set integrations to a join of the default integrations and the environment integrations
                    const envIntegrationsNotInDefaults = data.integrations.filter(
                      (envIntegration) =>
                        !integrationsSelected.some(
                          (it) => it.integration === envIntegration.integration
                        )
                    );
                    setIntegrationsSelected(
                      integrationsSelected.concat(envIntegrationsNotInDefaults)
                    );
                    setEnvironmentVariables(
                      objectMap(data.variables, (v: string) => {
                        return { value: v, delete: false };
                      })
                    );
                    if (data.settings.dbt_profile) {
                      setFieldValue('dbt_profile', data.settings.dbt_profile);
                      setFieldValue('override_dbt_profile', true);
                    } else {
                      setFieldValue('override_dbt_profile', false);
                    }
                    setDagsSource(data.airflow_config.dags_source);
                    setFieldValue('airflow_config.dags_source', data.airflow_config.dags_source);
                    !isEmpty(data.airflow_config.resources) &&
                      setFieldValue('airflow_config.resources', data.airflow_config.resources);
                    !isEmpty(data.code_server_config.resources) &&
                      setFieldValue(
                        'code_server_config.resources',
                        data.code_server_config.resources
                      );
                    if (data.airflow_config.s3_sync) {
                      setFieldValue(
                        'airflow_config.s3_sync.path',
                        data.airflow_config.s3_sync.path
                      );
                      if (
                        data.airflow_config.s3_sync.access_key &&
                        data.airflow_config.s3_sync.secret_key
                      ) {
                        setDagSyncAuth('iam-user');
                        setFieldValue('dag_s3_auth', 'iam-user');
                        setFieldValue(
                          'airflow_config.s3_sync.access_key',
                          data.airflow_config.s3_sync.access_key
                        );
                        setFieldValue(
                          'airflow_config.s3_sync.secret_key',
                          data.airflow_config.s3_sync.secret_key
                        );
                      }
                      if (data.airflow_config.s3_sync.iam_role) {
                        setDagSyncAuth('iam-role');
                        setFieldValue('dag_s3_auth', 'iam-user');
                        setFieldValue(
                          'airflow_config.s3_sync.iam_role',
                          data.airflow_config.s3_sync.iam_role
                        );
                      }
                    }
                    if (data.airflow_config.logs) {
                      if (data.airflow_config.logs.external) {
                        setAirflowLogsExternal(data.airflow_config.logs.external);
                        if (data.airflow_config.logs.backend) {
                          setAirflowLogsBackend(data.airflow_config.logs.backend);
                          setFieldValue(
                            'airflow_config.logs.backend',
                            data.airflow_config.logs.backend
                          );
                          if (data.airflow_config.logs.s3_log_bucket) {
                            setFieldValue(
                              'airflow_config.logs.s3_log_bucket',
                              data.airflow_config.logs.s3_log_bucket
                            );
                          }
                          if (data.airflow_config.logs.access_key) {
                            setFieldValue(
                              'airflow_config.logs.access_key',
                              data.airflow_config.logs.access_key
                            );
                          }
                          if (data.airflow_config.logs.secret_key) {
                            setFieldValue(
                              'airflow_config.logs.secret_key',
                              data.airflow_config.logs.secret_key
                            );
                          }
                          if (data.airflow_config.logs.volume_handle) {
                            setFieldValue(
                              'airflow_config.logs.volume_handle',
                              data.airflow_config.logs.volume_handle
                            );
                          }
                        }
                      }
                    }
                  },
                });

                useDependantProject(currentAccount?.slug, values.project, {
                  enabled: !!values.project,
                  onSuccess: async (projectData: Project) => {
                    setFieldValue('project_dbt_profile', projectData.settings.dbt_profile);
                    if (
                      data?.settings.dbt_profile &&
                      data?.settings.dbt_profile === projectData.settings.dbt_profile
                    ) {
                      setFieldValue('override_dbt_profile', false);
                    }
                    if (
                      projectData.settings.dbt_profile &&
                      !data?.settings.dbt_profile &&
                      !touched.override_dbt_profile &&
                      (!touched.dbt_profile || !values.dbt_profile)
                    ) {
                      setFieldValue('dbt_profile', projectData.settings.dbt_profile);
                      setFieldTouched('dbt_profile', false);
                      setFieldValue('override_dbt_profile', false);
                    }
                    if (
                      !projectData.settings.dbt_profile &&
                      !touched.override_dbt_profile &&
                      !data?.settings.dbt_profile
                    ) {
                      setFieldValue('dbt_profile', '');
                      setFieldTouched('dbt_profile', false);
                      setFieldValue('override_dbt_profile', true);
                    }
                  },
                });

                const handleProjectChange = (e: React.ChangeEvent<any>) => {
                  if (!e.target.value) {
                    setFieldValue('project_dbt_profile', '');
                    if (!values.override_dbt_profile || !touched.dbt_profile) {
                      setFieldValue('dbt_profile', '');
                      setFieldValue('override_dbt_profile', true);
                      setFieldTouched('dbt_profile', false);
                    }
                  }
                  handleChange(e);
                };

                const formSections = getFormSections({
                  handleSelectType,
                  handleProjectChange,
                  projects,
                  validateForm,
                  handleChangeDocs,
                  handleChangeOrchestrate,
                  currentType,
                  orchestrateSelected,
                  docsSelected,
                  currentUser,
                  dagsSource,
                  handleSelectDagsSource,
                  dagSyncAuth,
                  handleSelectDagSyncAuth,
                  airflowLogsBackend,
                  handleSelectLogsBackend,
                  airflowLogsExternal,
                  tabIndex,
                  integrationsSelected,
                  integrations,
                  setIntegrationsSelected,
                  setEnvironmentVariables,
                  environmentVariables,
                  handleChange,
                  values,
                  setFieldValue,
                  setCurrentError,
                });

                const labels = useMemo(() => getLabels(formSections), [formSections]);
                const tabs = useMemo(() => getTabs(formSections), [formSections]);

                const numberOfSteps = useMemo(
                  () =>
                    labels.reduce(function (acc, curr) {
                      if (typeof curr === 'string') {
                        acc++;
                      } else {
                        acc += (curr as { [key: string]: string[] })[Object.keys(curr)[0]].length;
                      }
                      return acc;
                    }, 0),
                  [labels]
                );

                const onNextClick = () => {
                  goToNextSection();
                };

                const goToInvalidTab = (errors: FormikErrors<any>) => {
                  const errorTab = findErrorTab(errors, labels);
                  errorTab >= 0 && setTabIndex(errorTab);
                };

                return (
                  <LoadingWrapper
                    isLoading={
                      (!isCreateMode && isLoading) || isLoadingIntegrations || isLoadingProjects
                    }
                    showElements={
                      (isCreateMode || (data && isSuccess)) &&
                      integrationsSuccess &&
                      projectsSuccess
                    }
                  >
                    <Form>
                      <Tabs index={tabIndex} onChange={handleTabsChange} orientation="vertical">
                        <FormTabs labels={labels} />
                        <Box w="full">
                          <TabPanels>
                            {tabs.map((tab, index) => (
                              <TabPanel pl="16" pr="0" key={index}>
                                {tab}
                              </TabPanel>
                            ))}
                          </TabPanels>
                          <HStack
                            width="full"
                            justifyContent="flex-end"
                            spacing="6"
                            pt="10"
                            pl="16"
                          >
                            <VStack gap={2} w="100%">
                              <HStack spacing="1" w="100%" justifyContent="flex-end" gap="2">
                                <Button
                                  onClick={() => navigate('/admin/environments')}
                                  mr={isCreateMode ? 12 : ''}
                                >
                                  Cancel
                                </Button>
                                <Button
                                  onClick={() => setTabIndex((prev) => prev - 1)}
                                  disabled={tabIndex === 0}
                                  hidden={!isCreateMode}
                                >
                                  Previous
                                </Button>
                                <Button
                                  colorScheme="blue"
                                  isLoading={isValidating}
                                  onClick={onNextClick}
                                  disabled={tabIndex === numberOfSteps - 1}
                                  hidden={
                                    !isCreateMode || !(isCreateMode && tabIndex < numberOfSteps - 1)
                                  }
                                >
                                  Next
                                </Button>
                                <Button
                                  colorScheme="blue"
                                  isLoading={updateMutation.isLoading || createMutation.isLoading}
                                  onClick={() => {
                                    !isValid && goToInvalidTab(errors);
                                    submitForm();
                                  }}
                                  hidden={isCreateMode && tabIndex < numberOfSteps - 1}
                                >
                                  Save Changes
                                </Button>
                              </HStack>
                              {!currentError && !isCreateMode && (
                                <HStack spacing="1" justifyContent="flex-end" w="full">
                                  <WarningTwoIcon color="orange.400" />
                                  <Text m="0">
                                    Saving changes could result in users&apos; environments being
                                    restarted.
                                  </Text>
                                </HStack>
                              )}
                              {currentError && (
                                <HStack spacing="1" justifyContent="flex-end" w="full">
                                  <WarningIcon color="red.400" />
                                  <Text fontWeight="bold" m="0" color="red.400">
                                    {currentError}
                                  </Text>
                                </HStack>
                              )}
                            </VStack>
                          </HStack>
                        </Box>
                      </Tabs>
                    </Form>
                  </LoadingWrapper>
                );
              }}
            </Formik>
          </Stack>
        </Box>
      )}
    </BasePage>
  );
};
