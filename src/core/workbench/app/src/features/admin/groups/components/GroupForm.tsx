import { VStack, Box, HStack, Button } from '@chakra-ui/react';
import { Formik, Form } from 'formik';
// import React, { useState } from 'react';
import React from 'react';
import * as Yup from 'yup';

import { FieldGroup } from '../../../../components/FieldGroup';
import { FormikInput } from '../../../../components/Forms/FormikInput';
import { TagInput } from '../../../../components/TagInput';
import { Group } from '../types';

import {
  PermissionsGroupTableActions,
  PermissionsGroupTable,
  PermissionsGroupTablePagination,
} from '.';

interface IGroupFormProps {
  isFetched?: boolean;
  isSuccess?: boolean;
  group: Group | undefined;
  handleSubmit: any;
}

export const GroupForm = ({ isSuccess, group, handleSubmit }: IGroupFormProps) => {
  // const [data, setData] = useState([]);
  const initialValues = {
    name: group?.name ?? '',
    permissions: group?.permissions ?? [],
    extended_group: {
      identity_groups: null,
    },
  };

  return (
    <>
      {isSuccess && (
        <Formik
          initialValues={initialValues}
          validationSchema={Yup.object({
            name: Yup.string().max(15, 'Must be 15 characters or less').required('Required'),
          })}
          // onSubmit={(val) => alert(JSON.stringify(val, null, 2))}
          onSubmit={handleSubmit}
        >
          <Form>
            <FieldGroup title="Basic Info">
              <VStack width="full" spacing="6">
                <FormikInput name="name" label="Name" placeholder={group?.name} />
              </VStack>
            </FieldGroup>
            <FieldGroup title="LDAP groups">
              <TagInput placeholder="Enter a group" />
            </FieldGroup>
            <FieldGroup title="Permissions" isTable>
              <Box overflowX="auto" p={1}>
                {/* <PermissionsGroupTableActions data={data} setData={setdata} /> */}
                <PermissionsGroupTableActions />
                {/* <PermissionsGroupTable data={group?.permissions} setData={setData} /> */}
                <PermissionsGroupTable data={group?.permissions} />
                <PermissionsGroupTablePagination data={group?.permissions} />
              </Box>
            </FieldGroup>
            <FieldGroup>
              <HStack width="full" justifyContent="flex-end" spacing="6">
                <Button type="submit" colorScheme="blue" onClick={handleSubmit}>
                  Save Changes
                </Button>
              </HStack>
            </FieldGroup>
          </Form>
        </Formik>
      )}
    </>
  );
};
