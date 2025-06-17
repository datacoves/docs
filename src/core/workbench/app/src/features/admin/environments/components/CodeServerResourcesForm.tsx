import { Box, Text, HStack, VStack, Heading } from '@chakra-ui/react';

import { MemoryInput } from './MemoryInput';

interface Props {
  values: any;
  setFieldValue: (field: string, value: any, shouldValidate?: boolean | undefined) => void;
}

function CodeServerResourcesForm(props: Props) {
  const { values, setFieldValue } = props;

  return (
    <VStack width="full" spacing="6" alignItems="flex-start">
      <Box w="full">
        <VStack w="full" spacing="4">
          <Box w="full">
            <Heading size="md">Code Server resources</Heading>
            <Text fontSize="sm">Specify a memory request and a memory limit for code-server</Text>
          </Box>
        </VStack>
      </Box>
      <VStack w="full" spacing="4">
        <Box w="full">
          <HStack w="full" gap={5}>
            <MemoryInput
              name={`code_server_config.resources.requests.cpu`}
              label="CPU Request"
              value={values.code_server_config.resources?.requests.cpu}
              setFieldValue={setFieldValue}
              type="CPU"
            />
            <MemoryInput
              name={`code_server_config.resources.limits.cpu`}
              label="CPU Limit"
              value={values.code_server_config.resources?.limits.cpu}
              setFieldValue={setFieldValue}
              type="CPU"
            />
            <MemoryInput
              name={`code_server_config.resources.requests.memory`}
              label="Memory Request"
              value={values.code_server_config.resources?.requests.memory}
              setFieldValue={setFieldValue}
              type="memory"
            />
            <MemoryInput
              name={`code_server_config.resources.limits.memory`}
              label="Memory Limit"
              value={values.code_server_config.resources?.limits.memory}
              setFieldValue={setFieldValue}
              type="memory"
            />
          </HStack>
        </Box>
      </VStack>
    </VStack>
  );
}

export default CodeServerResourcesForm;
