import { VStack, Box, Heading, Text, Tooltip, Flex } from '@chakra-ui/react';
import { FormikErrors } from 'formik';
import { InputControl, SwitchControl } from 'formik-chakra-ui';
import { ChangeEvent, useEffect } from 'react';

interface Props {
  validateForm: (values?: any) => Promise<FormikErrors<any>>;
  tabIndex: number;
  values: any;
  setFieldValue: (field: string, value: any, shouldValidate?: boolean | undefined) => void;
  handleChange: {
    (e: React.ChangeEvent<any>): void;
    <T = string | React.ChangeEvent<any>>(field: T): T extends React.ChangeEvent<any>
      ? void
      : (e: string | React.ChangeEvent<any>) => void;
  };
}

const GeneralSettingsForm = ({
  tabIndex,
  validateForm,
  values,
  setFieldValue,
  handleChange,
}: Props) => {
  const onSwitchChange = async (e: ChangeEvent<any>) => {
    if (values.override_dbt_profile) {
      setFieldValue('dbt_profile', values.project_dbt_profile);
      await validateForm({ ...values, dbt_profile: values.project_dbt_profile });
    } else {
      setFieldValue('dbt_profile', '');
      await validateForm({ ...values, dbt_profile: '' });
    }
    handleChange(e);
  };

  useEffect(() => {
    tabIndex === 2 && validateForm();
  }, [tabIndex, validateForm]);

  return (
    <VStack width="full" spacing="6" alignItems="flex-start">
      <Box>
        <Heading size="md">General settings</Heading>
        <Text fontSize="sm">Settings that affect multiple services</Text>
      </Box>
      <VStack width="full" spacing="3" alignItems="flex-start">
        <Box w="full">
          <InputControl name="dbt_home_path" label="dbt project path" />
          <Text color="gray.500" mt={1} fontSize="xs">
            Relative path to the folder where the <b>dbt_project.yml</b> file is located. <br />
            If left blank, Datacoves will assume the dbt project is located at your repository{' '}
            <b>root</b>.
          </Text>
        </Box>
        <Flex gap={5} alignItems="flex-start" display="flex" w="full">
          <Box w="full">
            <InputControl
              name="dbt_profile"
              label="dbt profile name"
              inputProps={{
                isDisabled: !values.override_dbt_profile && !!values.project_dbt_profile,
                placeholder: 'default',
              }}
            />
            <Text color="gray.500" mt={1} fontSize="xs">
              dbt profile name as defined in dbt_project.yml with the key <b>profile</b>
            </Text>
            <Text color="gray.500" fontSize="xs">
              If left blank, <b>&rsquo;default&rsquo;</b> will be used
            </Text>
          </Box>
          {!!values.project_dbt_profile && (
            <Tooltip label="Override project value" hasArrow bg="gray.300" color="black">
              <Box
                alignItems="center"
                display="flex"
                justifyContent="center"
                verticalAlign="baseline"
                mt="10"
              >
                <SwitchControl
                  id={`switch`}
                  mr={1}
                  display="flex"
                  onChange={onSwitchChange}
                  name="override_dbt_profile"
                />
              </Box>
            </Tooltip>
          )}
        </Flex>
      </VStack>
    </VStack>
  );
};

export default GeneralSettingsForm;
