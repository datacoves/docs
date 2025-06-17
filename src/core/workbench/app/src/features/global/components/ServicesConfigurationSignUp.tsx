import { VStack, HStack, Text } from '@chakra-ui/layout';
import { Box, Button, Divider, Heading } from '@chakra-ui/react';
import { Form, Formik } from 'formik';
import { InputControl, SelectControl } from 'formik-chakra-ui';
import * as Yup from 'yup';

import { useAccountSetup } from '../api/accountSetup';

export const ServicesConfigurationSignUp = (props: any) => {
  const createAccountMutation = useAccountSetup();

  const initialValues = {
    dbt_home_path: '',
    dbt_profile: '',
    dags_folder: 'orchestrate/dags',
  };

  const handleSubmit = (val: any) => {
    if (val.dbt_home_path) {
      props.payload.environment_configuration.dbt_home_path = val.dbt_home_path;
    }
    if (val.dbt_profile) {
      props.payload.project_settings.dbt_profile = val.dbt_profile;
    }

    if (val.dags_folder) {
      props.payload.environment_configuration.airflow_config = {};
      props.payload.environment_configuration.airflow_config.dags_folder = val.dags_folder;
      props.payload.environment_configuration.airflow_config.yaml_dags_folder = val.dags_folder;
    }
    props.setPayload(props.payload);
    const body = props.payload;
    createAccountMutation.mutate({ body });
  };
  return (
    <Formik
      initialValues={initialValues}
      validationSchema={Yup.object({
        dbt_home_path: Yup.string(),
        dbt_profile: Yup.string().matches(/^[a-zA-Z0-9_]+$/, 'Invalid dbt profile name'),
        dags_folder: Yup.string(),
      })}
      onSubmit={handleSubmit}
    >
      <Form>
        <VStack width="full" spacing="6" alignItems="flex-start">
          <Divider />
          <Box>
            <Heading size="md">General settings</Heading>
            <Text fontSize="sm">Settings that affect multiple services</Text>
          </Box>
          <Box w="full">
            {props.payload.dbt_project_paths && props.payload.dbt_project_paths.length > 0 ? (
              <SelectControl
                label="dbt home path"
                name="dbt_home_path"
                selectProps={{ placeholder: 'Select dbt project home path' }}
              >
                {props.payload.dbt_project_paths?.map((dbt_path: string) => {
                  return (
                    <option key={dbt_path} value={dbt_path}>
                      {dbt_path}
                    </option>
                  );
                })}
              </SelectControl>
            ) : (
              <>
                <InputControl
                  name="dbt_home_path"
                  label="dbt home path"
                  inputProps={{ placeholder: 'path/to/dbt_project/' }}
                />
              </>
            )}
            <Text color="gray.500" mt={1} fontSize="xs">
              Relative path to the folder where the <b>dbt_project.yml</b> file is located. <br />
              If left blank, Datacoves will assume the dbt project is located at your repository{' '}
              <b>root</b>
            </Text>
          </Box>
          <Box w="full">
            <InputControl
              name="dbt_profile"
              label="dbt profile name"
              inputProps={{ placeholder: 'default' }}
            />
            <Text color="gray.500" mt={1} fontSize="xs">
              dbt profile name as defined in dbt_project.yml with the key <b>profile</b>
            </Text>
          </Box>
          {props.payload.services.airflow.enabled && (
            <>
              <Divider />
              <Box>
                <Heading size="md">Airflow</Heading>
                <Text fontSize="sm">Airflow specific settings</Text>
              </Box>

              <Box w="full">
                <InputControl name="dags_folder" label="DAGs path" />
                <Text color="gray.500" mt={1} fontSize="xs">
                  Relative path to the folder where Airflow DAGs are located.
                </Text>
              </Box>
            </>
          )}
        </VStack>
        <HStack mt={6}>
          <Button size="sm" onClick={props.prevStep} variant="ghost">
            Back
          </Button>
          <Button
            type="submit"
            colorScheme="green"
            size="sm"
            isLoading={createAccountMutation.isLoading}
          >
            Finish
          </Button>
        </HStack>
      </Form>
    </Formik>
  );
};
