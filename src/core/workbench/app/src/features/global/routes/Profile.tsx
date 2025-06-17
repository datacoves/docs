import { Box, Stack, Text, Tabs, TabPanel, TabPanels } from '@chakra-ui/react';
import { useContext } from 'react';

import { BasePage } from '../../../components/AdminLayout';
import { FormTabs } from '../../../components/FormTabs';
import { HeadingGroup } from '../../../components/ProfileForm/HeadingGroup';
import { Project } from '../../../context/UserContext/types';
import { UserContext } from '../../../context/UserContext/UserContext';
import { DeleteProfile } from '../components/DeleteProfile';
import { ProfileSettings } from '../components/ProfileSettings';
import { ProfileSSHKeys } from '../components/ProfileSSHKeys';
import { ProfileSSLKeys } from '../components/ProfileSSLKeys';
import { ProjectSettings } from '../components/ProjectSettings';
import { UserEnvironmentSettings } from '../components/UserEnvironmentSettings';

export const Profile = () => {
  const { currentUser } = useContext(UserContext);

  return (
    <BasePage header="User Settings">
      <Box p="10" w="full">
        <Tabs orientation="vertical">
          <FormTabs
            labels={[
              currentUser?.features.user_profile_change_name && 'Basic Settings',
              currentUser?.features.user_profile_change_ssh_keys && 'Git SSH Keys',
              currentUser?.features.user_profile_change_ssl_keys && 'Database Auth Keys',
              currentUser?.features.user_profile_change_credentials && 'Database Connections',
              currentUser?.features.admin_code_server_environment_variables &&
                'VS Code Environment Variables',
              currentUser?.features.user_profile_delete_account && 'Delete User Account',
            ].flatMap((f) => (f ? [f] : []))}
          />
          <TabPanels>
            {currentUser?.features.user_profile_change_name && (
              <TabPanel pl="16" pr="0">
                <ProfileSettings userName={currentUser?.name} />
              </TabPanel>
            )}
            {currentUser?.features.user_profile_change_ssh_keys && (
              <TabPanel pl="16" pr="0">
                <ProfileSSHKeys />
              </TabPanel>
            )}
            {currentUser?.features.user_profile_change_ssl_keys && (
              <TabPanel pl="16" pr="0">
                <ProfileSSLKeys />
              </TabPanel>
            )}
            {currentUser?.features.user_profile_change_credentials && (
              <TabPanel pl="16" pr="0">
                <Stack as="section" spacing="6">
                  <HeadingGroup
                    title="Database Connections"
                    description="Configure database connections for each project environment."
                  />
                  {currentUser.projects.length === 0 && (
                    <Text pt="8">No environments granted yet.</Text>
                  )}
                  {currentUser.projects?.map((project: Project) => (
                    <ProjectSettings key={project.id} project={project} />
                  ))}
                </Stack>
              </TabPanel>
            )}
            {currentUser?.features.admin_code_server_environment_variables && (
              <TabPanel pl="16" pr="0">
                <Stack as="section" spacing="6">
                  <HeadingGroup
                    title="VS Code Environment Variables"
                    description="Manage your environment variables for each project environment."
                  />
                  {currentUser?.user_environments.map((userEnv) => (
                    <UserEnvironmentSettings key={userEnv.id} userEnvironment={userEnv} />
                  ))}
                </Stack>
              </TabPanel>
            )}
            {currentUser?.features.user_profile_delete_account && (
              <TabPanel pl="16" pr="0">
                <DeleteProfile />
              </TabPanel>
            )}
          </TabPanels>
        </Tabs>
      </Box>
    </BasePage>
  );
};
