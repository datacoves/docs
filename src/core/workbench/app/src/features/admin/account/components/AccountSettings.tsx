import { Box, Button, Stack, StackDivider, Text, StackProps, VStack } from '@chakra-ui/react';
import { Formik, Form } from 'formik';
import { InputControl } from 'formik-chakra-ui';
import React, { useContext } from 'react';
import * as Yup from 'yup';

import { Card } from '../../../../components/Card';
import { HeadingGroup } from '../../../../components/ProfileForm/HeadingGroup';
import { AccountContext } from '../../../../context/AccountContext';
import { useUpdateAccountDetail } from '../api/updateAccountDetail';

export const AccountSettings = (props: StackProps) => {
  const { currentAccount } = useContext(AccountContext);

  const initialValues = {
    name: currentAccount ? currentAccount.name : '',
    owned_by: currentAccount ? currentAccount.owned_by : '',
  };
  const updateMutation = useUpdateAccountDetail();

  const handleSubmit = (val: any, { setSubmitting }: any) => {
    const body = {
      name: val.name,
    };
    if (currentAccount?.slug !== undefined) {
      updateMutation.mutate({ account: currentAccount.slug, body });
    }
    setSubmitting(false);
  };

  return (
    <Stack as="section" spacing="6" {...props}>
      <HeadingGroup title="Account Settings" description="Change account details." />
      <Card>
        <Stack divider={<StackDivider />} spacing="6">
          <Formik
            initialValues={initialValues}
            validationSchema={Yup.object({
              name: Yup.string().required('Required'),
            })}
            onSubmit={handleSubmit}
          >
            <Form>
              <VStack width="full" spacing="6" alignItems="flex-start">
                <Box w="full">
                  <InputControl
                    label="Account owner"
                    name="owned_by"
                    inputProps={{ isDisabled: true }}
                  />
                  <Text color="gray.500" fontSize="xs" mt={1}>
                    Account related notifications are sent to owner&apos;s email address.
                  </Text>
                </Box>
                <Box w="full">
                  <InputControl label="Name" name="name" />
                  <Button
                    type="submit"
                    mt="5"
                    size="sm"
                    maxW="max-content"
                    fontWeight="normal"
                    isLoading={updateMutation.isLoading}
                  >
                    Save
                  </Button>
                </Box>
              </VStack>
            </Form>
          </Formik>
        </Stack>
      </Card>
    </Stack>
  );
};
