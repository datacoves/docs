import { Button, Flex, Stack, StackDivider } from '@chakra-ui/react';
import { Form, Formik } from 'formik';
import { InputControl } from 'formik-chakra-ui';
import React, { useState, useEffect } from 'react';
import * as Yup from 'yup';

import { HeadingGroup } from '../../../components/ProfileForm/HeadingGroup';
import { useUpdateUserName } from '../api/updateUserName';

export const ProfileSettings = ({ userName }: { userName: string | undefined }) => {
  const [value, setValue] = useState<string>('');
  useEffect(() => {
    if (userName) {
      setValue(userName);
    }
  }, [userName]);
  const initialValues = {
    name: value,
  };

  const updateMutation = useUpdateUserName();

  const handleSubmit = (val: any, { setSubmitting }: any) => {
    const body = { name: val.name };
    updateMutation.mutate({ body });
    setSubmitting(false);
  };

  return (
    <Stack as="section" spacing="6">
      <HeadingGroup title="Profile Settings" description="Change your profile." />
      <Stack divider={<StackDivider />} spacing="6" pt="8">
        <Formik
          initialValues={initialValues}
          enableReinitialize={true}
          validationSchema={Yup.object({
            name: Yup.string().required('Required'),
          })}
          onSubmit={handleSubmit}
        >
          <Form>
            <Flex direction="column">
              <InputControl name="name" label="Name" />
              <Flex w="full" justifyContent="flex-end">
                <Button
                  mt="5"
                  type="submit"
                  colorScheme="blue"
                  isLoading={updateMutation.isLoading}
                >
                  Save
                </Button>
              </Flex>
            </Flex>
          </Form>
        </Formik>
      </Stack>
    </Stack>
  );
};
