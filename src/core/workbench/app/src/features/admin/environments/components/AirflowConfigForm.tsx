import { Box, Text, HStack, VStack, Heading, Divider } from '@chakra-ui/react';
import { FormikErrors } from 'formik';
import { SelectControl, InputControl } from 'formik-chakra-ui';
import React, { useEffect } from 'react';

import { User } from '../../../../context/UserContext/types';

interface Props {
  currentUser: User | undefined;
  dagsSource: string | undefined;
  dagSyncAuth: string | undefined;
  handleSelectDagsSource: (event: any) => void;
  handleSelectDagSyncAuth: (event: any) => void;
  airflowLogsBackend: string | undefined;
  handleSelectLogsBackend: (event: any) => void;
  airflowLogsExternal: boolean | undefined;
  tabIndex: number;
  validateForm: (values?: any) => Promise<FormikErrors<any>>;
  handleChange: {
    (e: React.ChangeEvent<any>): void;
    <T = string | React.ChangeEvent<any>>(field: T): T extends React.ChangeEvent<any>
      ? void
      : (e: string | React.ChangeEvent<any>) => void;
  };
}

function AirflowConfigForm(props: Props) {
  const {
    currentUser,
    dagsSource,
    handleSelectDagsSource,
    dagSyncAuth,
    handleSelectDagSyncAuth,
    airflowLogsBackend,
    handleSelectLogsBackend,
    airflowLogsExternal,
    validateForm,
    tabIndex,
    handleChange,
  } = props;

  useEffect(() => {
    tabIndex === 3 && validateForm();
  }, [tabIndex, validateForm, airflowLogsBackend, airflowLogsExternal, dagSyncAuth, dagsSource]);

  const isLocal = window.location.hostname === 'datacoveslocal.com';

  return (
    <>
      <Divider />
      <Box w="full">
        <VStack w="full" spacing="4">
          <Box w="full">
            <Heading size="md">Airflow</Heading>
            <Text fontSize="sm">Airflow specific settings</Text>
          </Box>
          <HStack w="full">
            <Box w="full">
              <InputControl name="airflow_config.dags_folder" label="Python DAGs path" isRequired />
              <Text color="gray.500" mt={1} fontSize="xs">
                Relative path to the folder where Python DAGs are located.
              </Text>
            </Box>
            <Box w="full">
              <InputControl
                name="airflow_config.yaml_dags_folder"
                label="YAML DAGs path"
                isRequired
              />
              <Text color="gray.500" mt={1} fontSize="xs">
                Relative path to the folder where YAML DAGs are located.
              </Text>
            </Box>
          </HStack>
        </VStack>
        <Box w="full">
          <InputControl name="dbt_profiles_dir" label="dbt profiles path" isRequired />
          <Text color="gray.500" mt={1} fontSize="xs">
            Relative path to a folder where the <b>profiles.yml</b> file is located.
          </Text>
        </Box>
      </Box>
      <VStack w="full" spacing="4">
        <Box w="full">
          <Heading size="sm">DAGs sync configuration</Heading>
          <Text fontSize="xs">Where Airflow DAGs will be stored</Text>
        </Box>
        <Box w="full">
          <SelectControl
            label="Provider"
            name="airflow_config.dags_source"
            selectProps={{ placeholder: 'Select DAG storage' }}
            onChange={(e) => {
              handleSelectDagsSource(e);
              handleChange(e);
              validateForm();
            }}
            isRequired
          >
            <option value="git">Git</option>
            <option value="s3">S3</option>
          </SelectControl>
        </Box>
        {dagsSource === 's3' && (
          <VStack w="full">
            <Box w="full">
              <InputControl name="airflow_config.s3_sync.path" label="Bucket path" isRequired />
            </Box>
            <Box w="full">
              <SelectControl
                label="Auth mechanism"
                name="dag_s3_auth"
                selectProps={{
                  placeholder: 'Select provider',
                  value: dagSyncAuth,
                }}
                onChange={(e) => {
                  handleSelectDagSyncAuth(e);
                  handleChange(e);
                  validateForm();
                }}
                isRequired
              >
                <option value="iam-user">IAM User</option>
                <option value="iam-role">IAM Role</option>
              </SelectControl>
            </Box>
            {dagSyncAuth === 'iam-user' && (
              <HStack w="full">
                <Box w="full">
                  <InputControl
                    name="airflow_config.s3_sync.access_key"
                    label="Access key"
                    inputProps={{
                      placeholder: '*******',
                      type: 'password',
                    }}
                    isRequired
                  />
                </Box>
                <Box w="full">
                  <InputControl
                    name="airflow_config.s3_sync.secret_key"
                    label="Secret key"
                    inputProps={{
                      placeholder: '*******',
                      type: 'password',
                    }}
                    isRequired
                  />
                </Box>
              </HStack>
            )}
            {dagSyncAuth === 'iam-role' && (
              <Box w="full">
                <InputControl
                  name="airflow_config.s3_sync.iam_role"
                  label="Role ARN"
                  inputProps={{
                    placeholder: '*******',
                    type: 'password',
                  }}
                  isRequired
                />
              </Box>
            )}
          </VStack>
        )}
        {dagsSource === 'git' && (
          <Box w="full">
            <InputControl name="airflow_config.git_branch" label="Git branch name" isRequired />
            <Text color="gray.500" mt={1} fontSize="xs">
              Git branch to monitor for changes
            </Text>
          </Box>
        )}
        {(currentUser?.has_dynamic_blob_storage_provisioning ||
          currentUser?.has_dynamic_network_filesystem_provisioning ||
          isLocal) && (
          <>
            <Box w="full">
              <Heading size="sm">Logs configuration</Heading>
              <Text fontSize="xs">Where Airflow logs will be stored</Text>
            </Box>
            <Box w="full">
              <SelectControl
                label="Provider"
                name="airflow_config.logs.backend"
                selectProps={{ placeholder: 'Select logs provider' }}
                onChange={(e) => {
                  handleSelectLogsBackend(e);
                  handleChange(e);
                  validateForm();
                }}
              >
                <option value="s3">S3</option>
                {!isLocal &&
                  (currentUser?.has_dynamic_network_filesystem_provisioning ? (
                    <option value="efs">EFS</option>
                  ) : (
                    <option value="afs">AFS</option>
                  ))}
                {!!currentUser?.features.select_minio_logs && isLocal && (
                  <option value="minio">Minio</option>
                )}
                {isLocal && <option value="nfs">NFS</option>}
              </SelectControl>
            </Box>

            {airflowLogsExternal && (
              <>
                {airflowLogsBackend === 's3' ? (
                  <>
                    <VStack w="full">
                      <Box w="full">
                        <InputControl
                          name="airflow_config.logs.s3_log_bucket"
                          label="Bucket path"
                          isRequired
                        />
                      </Box>
                      <Box w="full">
                        <HStack w="full">
                          <Box w="full">
                            <InputControl
                              name="airflow_config.logs.access_key"
                              label="Access key"
                              inputProps={{
                                placeholder: '*******',
                                type: 'password',
                              }}
                              isRequired
                            />
                          </Box>
                          <Box w="full">
                            <InputControl
                              name="airflow_config.logs.secret_key"
                              label="Secret key"
                              inputProps={{
                                placeholder: '*******',
                                type: 'password',
                              }}
                              isRequired
                            />
                          </Box>
                        </HStack>
                      </Box>
                    </VStack>
                  </>
                ) : (
                  airflowLogsBackend === 'efs' && (
                    <>
                      <Box w="full">
                        <InputControl
                          name="airflow_config.logs.volume_handle"
                          label="Volume handle ID"
                          isRequired={!currentUser?.has_dynamic_network_filesystem_provisioning}
                        />
                      </Box>
                    </>
                  )
                )}
              </>
            )}
          </>
        )}
      </VStack>
    </>
  );
}

export default AirflowConfigForm;
