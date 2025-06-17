import { Box, Stack, StackDivider, Button, HStack, VStack } from '@chakra-ui/react';
import { Formik, Form } from 'formik';
import { InputControl } from 'formik-chakra-ui';
import { useContext, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';

import { BasePage } from '../../../../components/AdminLayout';
import { FieldGroup } from '../../../../components/FieldGroup';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { UserGroups } from '../../../../components/UserGroups';
import {
  addProjectsIntoProjectGroup,
  GroupFormValues,
  ProjectGroupType,
} from '../../../../components/UserGroups/utils';
import { AccountContext } from '../../../../context/AccountContext';
import { useAllGroups } from '../../groups/api/getGroups';
import { Group } from '../../groups/types';
import { useCreateInvitation } from '../api/createInvitation';
import { useInvitation } from '../api/getInvitationById';
import { Invitation } from '../types';

export const InvitationFormPage = () => {
  const { id } = useParams();
  const isCreateMode = id === undefined;
  const { currentAccount } = useContext(AccountContext);

  const initialValues: GroupFormValues = {
    name: '',
    email: '',
    groups: [],
  };

  const {
    data: groups,
    isSuccess: groupsSuccess,
    isLoading: isLoadingGroups,
  } = useAllGroups({
    account: currentAccount?.slug,
  });

  const accountGroup = useMemo(
    () =>
      groups?.filter(
        (group: Group) =>
          group.extended_group.environment === null && group.extended_group.project === null
      ),
    [groups]
  );

  const projectsGroup: ProjectGroupType = useMemo(() => {
    const projectsGroup = addProjectsIntoProjectGroup(groups);
    return projectsGroup;
  }, [groups]);

  const createMutation = useCreateInvitation();
  const handleSubmit = (body: any, { setSubmitting }: any) => {
    body.groups = body.groups.map((gId: string) => parseInt(gId));
    if (isCreateMode && currentAccount?.slug !== undefined) {
      createMutation.mutate({ account: currentAccount?.slug, body });
    }
    setSubmitting(false);
  };
  const navigate = useNavigate();
  return (
    <BasePage header={isCreateMode ? 'Create invitation' : 'Edit invitation'}>
      <Box px={{ base: '4', md: '10' }} py="16" maxWidth="5xl" mx="auto">
        <Stack spacing="4" divider={<StackDivider />}>
          <Formik
            key={id}
            initialValues={initialValues}
            validationSchema={Yup.object({
              name: Yup.string().required('Required'),
              email: Yup.string().required('Required'),
            })}
            onSubmit={handleSubmit}
          >
            {function Render({ setFieldValue, values }) {
              const { data, isSuccess, isLoading } = useInvitation(currentAccount?.slug, id, {
                enabled: currentAccount?.slug !== undefined && id !== undefined,
                onSuccess: (data: Invitation) => {
                  setFieldValue('name', data.name);
                  setFieldValue('email', data.email);
                  setFieldValue(
                    'groups',
                    data.groups.map((group) => group.id.toString())
                  );
                },
              });
              return (
                <LoadingWrapper
                  isLoading={(!isCreateMode && isLoading) || isLoadingGroups}
                  showElements={(isCreateMode || !!(data && isSuccess)) && groupsSuccess}
                >
                  <Form>
                    <FieldGroup title="Basic Info">
                      <VStack width="full" spacing="6">
                        <InputControl name="name" label="Name" isRequired />
                        <InputControl
                          name="email"
                          label="Email"
                          inputProps={{ type: 'email' }}
                          isRequired
                        />
                      </VStack>
                    </FieldGroup>
                    <FieldGroup title="Groups">
                      <UserGroups
                        projectsGroup={projectsGroup}
                        accountGroup={accountGroup}
                        accountName={currentAccount?.name}
                        values={values}
                      />
                    </FieldGroup>
                    <FieldGroup>
                      <HStack width="full" justifyContent="flex-end" spacing="6">
                        <Button onClick={() => navigate('/admin/invitations')}>Cancel</Button>
                        <Button
                          type="submit"
                          colorScheme="blue"
                          isLoading={createMutation.isLoading}
                        >
                          Invite
                        </Button>
                      </HStack>
                    </FieldGroup>
                  </Form>
                </LoadingWrapper>
              );
            }}
          </Formik>
        </Stack>
      </Box>
    </BasePage>
  );
};
