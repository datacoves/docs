import { VStack, Box, Heading, Text } from '@chakra-ui/layout';
import { FormikErrors } from 'formik';
import { InputControl } from 'formik-chakra-ui';
import { useEffect } from 'react';

interface Props {
  validateForm: (values?: any) => Promise<FormikErrors<any>>;
  tabIndex: number;
}

const DocsForm = ({ validateForm, tabIndex }: Props) => {
  useEffect(() => {
    (tabIndex === 5 || tabIndex === 3) && validateForm();
  }, [tabIndex, validateForm]);

  return (
    <VStack width="full" spacing="6" alignItems="flex-start">
      <Box>
        <Heading size="md">Docs</Heading>
        <Text fontSize="sm">dbt docs specific settings</Text>
      </Box>
      <Box w="full">
        <InputControl name="dbt_docs_config.git_branch" label="Git branch name" isRequired />
        <Text color="gray.500" mt={1} fontSize="xs">
          Git branch where dbt docs were generated
        </Text>
      </Box>
    </VStack>
  );
};

export default DocsForm;
