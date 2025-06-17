import { Box, HStack, VStack, Text } from '@chakra-ui/layout';
import { Button, Link, Checkbox } from '@chakra-ui/react';
import { Form, Formik } from 'formik';
import { CheckboxSingleControl, InputControl } from 'formik-chakra-ui';
import React, { useContext } from 'react';
import * as Yup from 'yup';

import { AccountContext } from '../../../context/AccountContext';
import { useAccountSetup } from '../api/accountSetup';

export const ProjectInfoSignUp = (props: any) => {
  const createAccountMutation = useAccountSetup();

  const { currentAccount } = useContext(AccountContext);
  const initialValues = {
    firstProject: '',
    services: {
      airbyte: { enabled: true },
      'code-server': { enabled: true },
      airflow: { enabled: true },
      superset: { enabled: true },
    },
  };

  const handleSubmit = (val: any) => {
    props.payload.project_name = val.firstProject;
    props.payload.services = val.services;
    props.payload.account_slug = currentAccount?.slug;
    props.setPayload(props.payload);
    props.nextStep();
  };

  const handleSkip = () => {
    const body = {
      account_name: props.payload.account_name,
      plan: props.payload.plan,
      billing_period: props.payload.billing_period,
      account_slug: currentAccount?.slug,
    };

    createAccountMutation.mutate({ body });
  };

  return (
    <Formik
      initialValues={initialValues}
      validationSchema={Yup.object({
        firstProject: Yup.string().required('Required').max(50),
      })}
      onSubmit={handleSubmit}
    >
      <Form>
        <VStack width="full" spacing="6">
          <Box w="full">
            <InputControl
              name="firstProject"
              label="First Project"
              inputProps={{ placeholder: 'Commercial Analytics' }}
              isRequired
            />
            <Text color="gray.500" mt={1} fontSize="xs">
              This will be associated to your git repository.
            </Text>
          </Box>
        </VStack>
        <VStack width="full" spacing="3" mt={3} alignItems="flex-start">
          <VStack alignItems="flex-start">
            <CheckboxSingleControl name="services.airbyte.enabled">
              Extract and Load data
            </CheckboxSingleControl>
            <Text color="gray.500" fontSize="xs" pl={6}>
              Extract and load data from a variety of sources using{' '}
              <Link
                href="https://airbyte.com/"
                isExternal
                color="blue.500"
                textDecoration="underline"
              >
                Airbyte
              </Link>
            </Text>
          </VStack>
          <VStack alignItems="flex-start">
            <Checkbox isDisabled isChecked>
              Transform data
            </Checkbox>
            <Text color="gray.500" fontSize="xs" pl={6}>
              Use a web version of{' '}
              <Link
                href="https://code.visualstudio.com/"
                isExternal
                color="blue.500"
                textDecoration="underline"
              >
                Visual Studio Code
              </Link>{' '}
              and{' '}
              <Link
                href="https://www.getdbt.com/"
                isExternal
                color="blue.500"
                textDecoration="underline"
              >
                dbt
              </Link>{' '}
              to transform data, add testing, docs and build the lineage users need to trust your
              insights.
            </Text>
          </VStack>
          <VStack alignItems="flex-start">
            <CheckboxSingleControl name="services.airflow.enabled">
              Orchestrate
            </CheckboxSingleControl>
            <Text color="gray.500" fontSize="xs" pl={6}>
              Schedule, monitor and scale your workflows using{' '}
              <Link
                href="https://airflow.apache.org/"
                isExternal
                color="blue.500"
                textDecoration="underline"
              >
                Airflow
              </Link>
            </Text>
          </VStack>
          <VStack alignItems="flex-start">
            <CheckboxSingleControl name="services.superset.enabled">Analyze</CheckboxSingleControl>
            <Text color="gray.500" fontSize="xs" pl={6}>
              Build reports and dashboards for decision makers using{' '}
              <Link
                href="https://superset.apache.org/"
                isExternal
                color="blue.500"
                textDecoration="underline"
              >
                Superset
              </Link>
            </Text>
          </VStack>
        </VStack>
        <HStack mt={6}>
          <Button size="sm" onClick={props.prevStep} variant="ghost">
            Back
          </Button>
          <Button type="submit" colorScheme="green" size="sm">
            Next
          </Button>
          <Button
            size="sm"
            colorScheme="blue"
            onClick={handleSkip}
            isLoading={createAccountMutation.isLoading}
          >
            Skip
          </Button>
        </HStack>
      </Form>
    </Formik>
  );
};
