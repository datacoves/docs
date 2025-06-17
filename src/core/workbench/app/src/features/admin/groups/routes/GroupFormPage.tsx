import { InfoOutlineIcon } from '@chakra-ui/icons';
import {
  Box,
  Stack,
  StackDivider,
  Button,
  HStack,
  VStack,
  Accordion,
  Switch,
  Tabs,
  TabPanels,
  TabPanel,
  FormLabel,
  Flex,
  Tooltip,
  Alert,
  AlertIcon,
  Text,
} from '@chakra-ui/react';
import { Formik, Form } from 'formik';
import { CheckboxContainer, InputControl, SelectControl, TextareaControl } from 'formik-chakra-ui';
import { isEmpty } from 'lodash';
import { useCallback, useContext, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';

import { BasePage } from '../../../../components/AdminLayout';
import NotAuthorized from '../../../../components/Error/NotAuthorized';
import { FieldGroup } from '../../../../components/FieldGroup';
import { FormTabs } from '../../../../components/FormTabs';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { UserContext } from '../../../../context/UserContext';
import { Environment, Project } from '../../../../context/UserContext/types';
import { useAllEnvironments } from '../../environments/api/getEnvironments';
import { useAllProjects } from '../../projects/api/getProjects';
import { useCreateGroup } from '../api/createGroup';
import { useGroup } from '../api/getGroupById';
import { useAllPermissions } from '../api/getPermissions';
import { useUpdateGroup } from '../api/updateGroup';
import PermissionsAccordion from '../components/PermissionsAccordion';
import { Group, Permission } from '../types';

interface FormValues {
  id: string;
  name: string;
  permissions: string[];
  users_count: number;
  extended_group: {
    description: string;
    name: string;
    identity_groups: string[] | string;
    project_id: string | undefined;
    environment_id: string | undefined;
    environment?: Environment;
    project?: Project;
  };
}

export const GroupFormPage = () => {
  const { currentUser } = useContext(UserContext);
  const { id } = useParams();
  const isCreateMode = id === undefined;
  const { currentAccount } = useContext(AccountContext);
  const [currentPermissionsFilter, setCurrentPermissionsFilter] = useState<string>('');
  const [showGroupPermissionsOnly, setShowGroupPermissionsOnly] = useState(false);

  const initialValues: FormValues = {
    name: '',
    extended_group: {
      description: '',
      name: '',
      identity_groups: [],
      project_id: undefined,
      environment_id: undefined,
    },
    permissions: [],
    id: '',
    users_count: 0,
  };
  const {
    data: permissions,
    isSuccess: permissionsSuccess,
    isLoading: isLoadingPermissions,
  } = useAllPermissions({
    account: currentAccount?.slug,
  });

  const {
    data: projects,
    isSuccess: projectsSuccess,
    isLoading: isLoadingProjects,
  } = useAllProjects({
    account: currentAccount?.slug,
  });

  const {
    data: environments,
    isSuccess: environmentsSuccess,
    isLoading: isLoadingEnvs,
  } = useAllEnvironments({
    account: currentAccount?.slug,
  });

  const createMutation = useCreateGroup();
  const updateMutation = useUpdateGroup();

  const handlePermissionsFilterChange = (event: any) => {
    setCurrentPermissionsFilter(event.target.value.toLowerCase());
  };

  const handleSubmit = (body: FormValues, { setSubmitting }: any) => {
    const formattedBody = {
      name: body.name || body.extended_group.name,
      permissions: body.permissions.map((pId) => ({ id: Number(pId) })),
      extended_group: {
        ...body.extended_group,
        identity_groups: body.extended_group.identity_groups
          ? typeof body.extended_group.identity_groups === 'string'
            ? body.extended_group.identity_groups.split(',')
            : body.extended_group.identity_groups
          : [],
      },
    };
    if (currentAccount?.slug !== undefined) {
      if (isCreateMode) {
        createMutation.mutate({ account: currentAccount?.slug, body: formattedBody });
      } else {
        updateMutation.mutate({
          account: currentAccount?.slug,
          id,
          body: formattedBody,
        });
      }
      setSubmitting(false);
    }
  };
  const navigate = useNavigate();

  const filteredPermissions = useCallback(
    (data?: Group | undefined) => {
      const userSelectedPermissions = data
        ? permissions?.filter(({ id }) => data?.permissions.map(({ id }) => id).includes(id))
        : [];
      const filtered = (showGroupPermissionsOnly ? userSelectedPermissions : permissions)?.filter(
        (perm: Permission) =>
          perm.resource.toLowerCase().includes(currentPermissionsFilter) ||
          perm.environment?.toLowerCase().includes(currentPermissionsFilter) ||
          perm.project?.toLowerCase().includes(currentPermissionsFilter)
      );
      return filtered;
    },
    [currentPermissionsFilter, permissions, showGroupPermissionsOnly]
  );

  if (isCreateMode && !currentUser?.features.admin_create_groups) {
    return <NotAuthorized />;
  }

  return (
    <BasePage header={isCreateMode ? 'Create group' : 'Edit group'}>
      <Box px={{ base: '4', md: '10' }} py="16" maxWidth="5xl" mx="auto">
        <Stack spacing="4" divider={<StackDivider />}>
          <Formik
            key={id}
            initialValues={initialValues}
            validationSchema={Yup.object({
              extended_group: Yup.object({
                name: Yup.string().required('Required'),
              }),
            })}
            onSubmit={handleSubmit}
            validateOnChange={false}
          >
            {function Render({ setValues, values, setFieldValue, handleChange }) {
              const { data, isSuccess, isLoading } = useGroup(currentAccount?.slug, id, {
                enabled: currentAccount?.slug !== undefined && id !== undefined && !isCreateMode,
                onSuccess: (data: Group) => {
                  const formFormattedData: FormValues = {
                    ...data,
                    permissions: data.permissions.map((perm) => perm.id.toString()),
                    extended_group: {
                      ...data.extended_group,
                      identity_groups: data.extended_group.identity_groups.toString(),
                      project_id: data.extended_group.project?.id,
                      environment_id: data.extended_group.environment?.id,
                    },
                  };
                  setValues(formFormattedData);
                },
              });

              const { project_id, environment_id, environment, project } = values.extended_group;

              const permissionsInScope = filteredPermissions(data)?.filter(
                (permission) =>
                  Number(permission.project_id) === Number(project_id) &&
                  (environment_id
                    ? Number(permission.environment_id) === Number(environment_id)
                    : !permission.environment_id)
              );

              const accountPermissions = !project_id
                ? filteredPermissions(data)?.filter((perm) => !perm.environment && !perm.project)
                : [];

              const handleProjectChange = (e: React.ChangeEvent<any>) => {
                setFieldValue('extended_group.environment_id', undefined);
                setFieldValue('extended_group.environment', undefined);
                setFieldValue(
                  'extended_group.project',
                  projects?.find(({ id }) => Number(id) === Number(e.target.value))
                );
                handleChange(e);
              };

              const handleEnvChange = (e: React.ChangeEvent<any>) => {
                setFieldValue(
                  'extended_group.environment',
                  environments?.find(({ id }) => Number(id) === Number(e.target.value))
                );
                handleChange(e);
              };

              const formTabLabels = ['Basic Information'];

              if (isCreateMode) {
                formTabLabels.push('Scope');
                formTabLabels.push('Permissions');
              }

              return (
                <LoadingWrapper
                  isLoading={
                    (!isCreateMode && isLoading) ||
                    isLoadingPermissions ||
                    isLoadingProjects ||
                    isLoadingEnvs
                  }
                  showElements={
                    (isCreateMode || (data && isSuccess)) &&
                    permissionsSuccess &&
                    projectsSuccess &&
                    environmentsSuccess
                  }
                >
                  <Form>
                    <Tabs orientation="vertical">
                      <FormTabs labels={formTabLabels} />
                      <TabPanels>
                        <TabPanel pl="16" pr="0">
                          <VStack width="full" spacing="6">
                            <InputControl name="extended_group.name" label="Name" isRequired />
                            <TextareaControl
                              name="extended_group.description"
                              label="Description"
                              textareaProps={{ isDisabled: true }}
                              isReadOnly={true}
                            />
                            <InputControl
                              name="extended_group.identity_groups"
                              label="Mapped AD groups"
                            />
                          </VStack>
                        </TabPanel>

                        {isCreateMode && (
                          <TabPanel pl="16" pr="0">
                            <VStack width="full" spacing="6">
                              <Text w="full" fontWeight="bold">
                                Account: {currentAccount?.name}
                              </Text>
                              <SelectControl
                                name="extended_group.project_id"
                                selectProps={{ placeholder: 'Select project' }}
                                onChange={handleProjectChange}
                                label="Project"
                              >
                                {projects?.map((project: Project) => {
                                  return (
                                    <option key={project.id} value={project.id}>
                                      {project.name}
                                    </option>
                                  );
                                })}
                              </SelectControl>
                              <SelectControl
                                name="extended_group.environment_id"
                                selectProps={{ placeholder: 'Select environment' }}
                                onChange={handleEnvChange}
                                label="Environment"
                              >
                                {environments
                                  ?.filter(({ project }) => Number(project) === Number(project_id))
                                  .map((env: Environment) => {
                                    return (
                                      <option key={env.id} value={env.id}>
                                        {env.name}
                                      </option>
                                    );
                                  })}
                              </SelectControl>
                              {!isCreateMode && (
                                <Alert status="warning">
                                  <AlertIcon />
                                  By changing the scope of your group, the permissions that do not
                                  match the scope will be removed
                                </Alert>
                              )}
                            </VStack>
                          </TabPanel>
                        )}
                        {isCreateMode && (
                          <TabPanel pl="16" pr="0">
                            <VStack width="full" spacing="6">
                              <HStack w="full" spacing={8} alignItems="end">
                                <InputControl
                                  name="permissions_filter"
                                  label="Filter permissions"
                                  inputProps={{
                                    placeholder: 'Type resource name, project, or environment...',
                                  }}
                                  onChange={handlePermissionsFilterChange}
                                />
                                {!isCreateMode && (
                                  <Flex gap={2} pb={2}>
                                    <FormLabel
                                      htmlFor="showGroupPermissionsOnly"
                                      textAlign="center"
                                      whiteSpace="nowrap"
                                      mb={0}
                                      mt={1}
                                    >
                                      Current permissions
                                      <Tooltip label="Filter to see only currently added permissions for this group">
                                        <InfoOutlineIcon ml={2} />
                                      </Tooltip>
                                    </FormLabel>
                                    <Switch
                                      size="lg"
                                      id="showGroupPermissionsOnly"
                                      onChange={() => setShowGroupPermissionsOnly((prev) => !prev)}
                                    />
                                  </Flex>
                                )}
                              </HStack>
                              <CheckboxContainer name="permissions" stackProps={{ pl: 0 }}>
                                <Accordion allowMultiple>
                                  {accountPermissions && accountPermissions?.length > 0 && (
                                    <PermissionsAccordion
                                      title="Account level permissions"
                                      permissions={accountPermissions}
                                    />
                                  )}
                                  {permissionsInScope && !isEmpty(permissionsInScope) && (
                                    <PermissionsAccordion
                                      title={`${environment?.name || project?.name} ${
                                        values.extended_group.environment_id
                                          ? 'Environment'
                                          : 'Project'
                                      } level permissions`}
                                      permissions={permissionsInScope}
                                    />
                                  )}
                                </Accordion>
                              </CheckboxContainer>
                            </VStack>
                          </TabPanel>
                        )}
                      </TabPanels>
                    </Tabs>
                    <FieldGroup>
                      <HStack width="full" justifyContent="flex-end" spacing="6">
                        <Button onClick={() => navigate('/admin/groups')}>Cancel</Button>
                        <Button
                          type="submit"
                          colorScheme="blue"
                          isLoading={updateMutation.isLoading || createMutation.isLoading}
                        >
                          Save Changes
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
