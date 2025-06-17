import {
  Box,
  Divider,
  FormLabel,
  Heading,
  HStack,
  Switch,
  Tooltip,
  VStack,
  Text,
} from '@chakra-ui/react';
import { FormikErrors } from 'formik';
import { SwitchControl } from 'formik-chakra-ui';
import { useEffect } from 'react';

interface Props {
  handleChangeDocs: (event: any) => void;
  handleChangeOrchestrate: (event: any) => void;
  currentType: string | undefined;
  validateForm: (values?: any) => Promise<FormikErrors<any>>;
  tabIndex: number;
  setCurrentError?: (error: string | undefined) => void;
}

const StackServicesForm = ({
  handleChangeDocs,
  handleChangeOrchestrate,
  currentType,
  validateForm,
  tabIndex,
  setCurrentError,
}: Props) => {
  useEffect(() => {
    tabIndex === 1 && validateForm();
  }, [tabIndex, validateForm]);

  const handleServiceChange = (e: any, originalHandler?: (event: any) => void) => {
    if (e.target.checked) {
      setCurrentError?.(undefined);
    }
    originalHandler?.(e);
  };

  return (
    <VStack spacing="6" alignItems="flex-start">
      <Divider />
      <Box>
        <Heading size="md">User services</Heading>
        <Text fontSize="sm">One instance per user</Text>
      </Box>
      <Box flex="1">
        {currentType === 'dev' ? (
          <SwitchControl
            name="services.code-server.enabled"
            label="TRANSFORM + OBSERVE > Local Docs"
            onChange={(e) => handleServiceChange(e)}
          />
        ) : (
          <Tooltip label="Requires a Development type of environment">
            <HStack spacing="0">
              <FormLabel htmlFor="services.code-server.enabled" mb="0" textColor="gray">
                TRANSFORM + OBSERVE &gt; Local Docs
              </FormLabel>
              <Switch name="services.code-server.enabled" isDisabled isChecked={false} />
            </HStack>
          </Tooltip>
        )}
        <Text fontSize="sm">Powered by VS Code and dbt</Text>
      </Box>
      <Divider />
      <Box>
        <Heading size="md">Environment services</Heading>
        <Text fontSize="sm">One instance each</Text>
      </Box>
      <HStack w="full">
        <Box flex="1">
          <SwitchControl
            name="services.airbyte.enabled"
            label="LOAD"
            onChange={(e) => handleServiceChange(e)}
          />
          <Text fontSize="sm">Powered by Airbyte</Text>
        </Box>
        <Box flex="1">
          <SwitchControl
            name="services.dbt-docs.enabled"
            label="OBSERVE > Docs"
            onChange={(e) => {
              handleServiceChange(e, handleChangeDocs);
              validateForm();
            }}
          />
          <Text fontSize="sm">Powered by dbt docs</Text>
        </Box>
      </HStack>
      <HStack w="full">
        <Box flex="1">
          <SwitchControl
            name="services.airflow.enabled"
            label="ORCHESTRATE"
            onChange={(e) => {
              handleServiceChange(e, handleChangeOrchestrate);
              validateForm(e);
            }}
          />
          <Text fontSize="sm">Powered by Airflow</Text>
        </Box>
        <Box flex="1">
          <SwitchControl
            name="services.superset.enabled"
            label="ANALYZE"
            onChange={(e) => handleServiceChange(e)}
          />
          <Text fontSize="sm">Powered by Superset</Text>
        </Box>
      </HStack>
    </VStack>
  );
};

export default StackServicesForm;
