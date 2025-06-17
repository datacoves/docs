import { HStack, VStack, Text } from '@chakra-ui/react';
import { FormikErrors } from 'formik';
import { InputControl, SelectControl } from 'formik-chakra-ui';
import { useEffect } from 'react';

import { Project } from '../../../../context/UserContext/types';

interface Props {
  handleSelectType: (event: any) => void;
  handleProjectChange: (event: any) => void;
  projects: Project[] | undefined;
  validateForm: (values?: any) => Promise<FormikErrors<any>>;
  tabIndex: number;
}

const BasicInfoForm = ({
  handleSelectType,
  handleProjectChange,
  projects,
  validateForm,
  tabIndex,
}: Props) => {
  useEffect(() => {
    tabIndex === 0 && validateForm();
  }, [tabIndex, validateForm]);
  return (
    <VStack width="full" spacing="6">
      <HStack w="full" spacing="6" alignItems="flex-start">
        <InputControl name="name" label="Name" isRequired />
        <SelectControl
          label="Type"
          name="type"
          selectProps={{ placeholder: 'Select type' }}
          onChange={handleSelectType}
          isRequired
        >
          <option value="dev">Development</option>
          <option value="test">Testing</option>
          <option value="prod">Production</option>
        </SelectControl>
      </HStack>
      <HStack w="full" spacing="6" alignItems="flex-start">
        <SelectControl
          label="Project"
          name="project"
          selectProps={{ placeholder: 'Select project' }}
          onChange={handleProjectChange}
          isRequired
          flex="1"
        >
          {projects?.map((project: Project) => {
            return (
              <option key={`projects.${project.id}`} value={project.id}>
                {project.name}
              </option>
            );
          })}
        </SelectControl>
        <VStack flex="1">
          <SelectControl
            label="Profile"
            name="release_profile"
            selectProps={{ placeholder: 'Select profile' }}
            isRequired
          >
            <option value="dbt-snowflake">Snowflake</option>
            <option value="dbt-redshift">Redshift</option>
            <option value="dbt-bigquery">Bigquery</option>
            <option value="dbt-databricks">Databricks</option>
          </SelectControl>
          <Text color="gray.500" mt={1} fontSize="xs">
            Determines the libraries and extensions pre-installed on VSCode and Airflow workers.
          </Text>
        </VStack>
      </HStack>
    </VStack>
  );
};

export default BasicInfoForm;
