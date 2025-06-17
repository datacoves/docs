import { Box, Text, HStack, VStack, Heading, Divider } from '@chakra-ui/react';
import { FormikErrors } from 'formik';
import { capitalize } from 'lodash-es';
import React, { Fragment, useEffect } from 'react';

import { MemoryInput } from './MemoryInput';
import { SERVICES } from './utils';

interface Props {
  tabIndex: number;
  validateForm: (values?: any) => Promise<FormikErrors<any>>;
  values: any;
  setFieldValue: (field: string, value: any, shouldValidate?: boolean | undefined) => void;
}

function AirflowResourcesForm(props: Props) {
  const { validateForm, tabIndex, values, setFieldValue } = props;

  useEffect(() => {
    tabIndex === 4 && validateForm();
  }, [tabIndex, validateForm]);

  return (
    <VStack width="full" spacing="6" alignItems="flex-start">
      <Box w="full">
        <VStack w="full" spacing="4">
          <Box w="full">
            <Heading size="md">Airflow resources</Heading>
            <Text fontSize="sm">
              Specify a memory request and a memory limit for different services
            </Text>
          </Box>
        </VStack>
      </Box>
      {SERVICES.map((service) => (
        <Fragment key={service}>
          <VStack w="full" spacing="4">
            <Box w="full">
              <Heading size="sm">{capitalize(service)} configuration</Heading>
            </Box>
            <Box w="full">
              <HStack w="full" gap={5}>
                <MemoryInput
                  name={`airflow_config.resources.${service}.requests.cpu`}
                  label="CPU Request"
                  value={values.airflow_config.resources[service]?.requests.cpu}
                  setFieldValue={setFieldValue}
                  type="CPU"
                />
                <MemoryInput
                  name={`airflow_config.resources.${service}.limits.cpu`}
                  label="CPU Limit"
                  value={values.airflow_config.resources[service]?.limits.cpu}
                  setFieldValue={setFieldValue}
                  type="CPU"
                />
                <MemoryInput
                  name={`airflow_config.resources.${service}.requests.memory`}
                  label="Memory Request"
                  value={values.airflow_config.resources[service]?.requests.memory}
                  setFieldValue={setFieldValue}
                  type="memory"
                />
                <MemoryInput
                  name={`airflow_config.resources.${service}.limits.memory`}
                  label="Memory Limit"
                  value={values.airflow_config.resources[service]?.limits.memory}
                  setFieldValue={setFieldValue}
                  type="memory"
                />
              </HStack>
            </Box>
          </VStack>
          <Divider />
        </Fragment>
      ))}
    </VStack>
  );
}

export default AirflowResourcesForm;
