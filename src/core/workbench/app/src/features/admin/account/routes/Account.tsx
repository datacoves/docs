import { Box, Flex, Stack, useColorModeValue } from '@chakra-ui/react';
import { useContext } from 'react';

import { Breadcrumb } from '../../../../components/Breadcrumb';
import { Header } from '../../../../components/Header';
import PageSidebarContainer from '../../../../components/Sidebar/PageSidebarContainer';
import { AccountContext } from '../../../../context/AccountContext';
import { UserContext } from '../../../../context/UserContext';
import { AccountSettings } from '../components/AccountSettings';
import { AccountSubscription } from '../components/AccountSubscription';
import { DangerZone } from '../components/DangerZone';

export const Account = () => {
  const { currentUser } = useContext(UserContext);
  const { currentAccount } = useContext(AccountContext);

  return (
    <Flex flexFlow="column" h="100vh">
      <Header />
      <PageSidebarContainer>
        <Breadcrumb mt="12" />
        <Flex
          bg={useColorModeValue('gray.50', 'gray.800')}
          px={{ base: '4', md: '10' }}
          py="16"
          grow="1"
        >
          <Box maxW="xl" mx="auto">
            <Stack spacing="12">
              <AccountSettings />
              {currentUser?.features.accounts_signup &&
                currentAccount?.owned_by === currentUser.email && <AccountSubscription />}
              <DangerZone />
            </Stack>
          </Box>
        </Flex>
      </PageSidebarContainer>
    </Flex>
  );
};
