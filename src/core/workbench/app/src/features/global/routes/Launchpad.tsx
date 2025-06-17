import {
  Box,
  Flex,
  Stack,
  useColorModeValue,
  Heading,
  Container,
  Text,
  Button,
  HStack,
  CircularProgress,
} from '@chakra-ui/react';
import { useContext } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '../../../components/AdminLayout/components/PageHeader';
import { Header } from '../../../components/Header';
import PageSidebarContainer from '../../../components/Sidebar/PageSidebarContainer';
import { AccountContext } from '../../../context/AccountContext';
import { UserContext } from '../../../context/UserContext';
import GetStarted from '../components/GetStarted';

import { EnvironmentsStack } from './EnvironmentsStack';
import { LaunchpadSetupContainer } from './LaunchpadSetupContainer';

export const Launchpad = () => {
  const { currentUser } = useContext(UserContext);
  const { currentAccount } = useContext(AccountContext);
  const navigate = useNavigate();
  const contactSales = () => {
    window.location.href = 'mailto:sales@datacoves.com';
    navigate('/');
  };
  const isSuspended =
    currentAccount && currentAccount.has_environments && currentAccount.is_suspended;

  return (
    <Flex flexFlow="column" h="100vh">
      <Flex position="fixed" right="40px" bottom="0px" color="gray.500" p="5" fontSize="small">
        v{currentUser?.release}
      </Flex>
      <Header />
      <PageSidebarContainer>
        {!isSuspended && currentUser?.projects && currentUser?.projects.length > 0 && (
          <PageHeader mt="12" header="Launch Pad" width="full" />
        )}

        <Flex bg={useColorModeValue('gray.50', 'gray.800')} px="10" py="12" grow="1">
          {currentUser === undefined && (
            <HStack m="0 auto">
              <CircularProgress isIndeterminate />
              <Text fontWeight="bold">Loading user settings...</Text>
            </HStack>
          )}
          {isSuspended && currentUser && (
            <Box maxW="2xl" mx="auto">
              <Container py={{ base: '16', md: '24' }}>
                <Stack spacing={{ base: '8', md: '10' }}>
                  <Stack spacing={{ base: '4', md: '5' }} align="center">
                    <Heading>Account is suspended</Heading>
                    <Text color="muted" maxW="2xl" textAlign="center" fontSize="xl">
                      There is no active subscription on this account.
                    </Text>
                  </Stack>
                  <Stack spacing="3" direction={{ base: 'column', sm: 'row' }} justify="center">
                    {currentAccount?.owned_by === currentUser.email && (
                      <>
                        <Button onClick={contactSales}>Contact sales</Button>
                        <Button colorScheme="blue" onClick={() => navigate('/admin/account')}>
                          Manage account subscription
                        </Button>
                      </>
                    )}
                    {currentAccount?.owned_by !== currentUser.email && (
                      <Text color="muted" maxW="2xl" textAlign="center" fontSize="xl">
                        Ask the account owner to solve this issue.
                      </Text>
                    )}
                  </Stack>
                </Stack>
              </Container>
            </Box>
          )}
          {!isSuspended && currentUser?.projects && currentUser?.projects.length > 0 && (
            <Stack spacing="12" w="7xl" mx="auto">
              <GetStarted />
              <EnvironmentsStack currentUser={currentUser} />
            </Stack>
          )}
          {!isSuspended && currentUser?.projects.length === 0 && (
            <Stack w="7xl" mx="auto" pt={4}>
              <GetStarted />
              <Box maxW="2xl" mx="auto !important">
                <Container maxW={'container.md'} py={{ base: '16', md: '24' }}>
                  <Stack spacing={{ base: '8', md: '10' }}>
                    <Stack spacing={{ base: '4', md: '5' }} align="center">
                      <Heading>
                        Welcome to Datacoves!{' '}
                        <span role="img" aria-label="Hooray">
                          🎉
                        </span>
                      </Heading>
                      {currentUser.features.accounts_signup && (
                        <Text color="muted" maxW="2xl" textAlign="center" fontSize="xl">
                          {currentAccount &&
                            !currentAccount.has_environments &&
                            'Start your analytics journey by continuing with your account setup process.'}
                          {currentAccount &&
                            currentAccount.has_environments &&
                            'You don’t appear to have access to any project.'}
                          {!currentAccount &&
                            'Start your analytics journey by creating a new account now.'}
                        </Text>
                      )}
                      {currentUser.features.accounts_signup &&
                        currentAccount &&
                        currentAccount.has_environments && (
                          <Text color="muted" maxW="2xl" textAlign="center" fontSize="xl">
                            Ask an Administrator to add you to the right access groups.
                          </Text>
                        )}
                      {!currentUser.features.accounts_signup && (
                        <>
                          <Text color="muted" maxW="2xl" textAlign="center" fontSize="xl">
                            You don’t appear to have access to this account.
                          </Text>

                          <Text color="muted" maxW="2xl" textAlign="center" fontSize="xl">
                            Ask an Administrator to add you to the right access groups. If you
                            already have the group try signing out and signing in again.
                          </Text>
                        </>
                      )}
                    </Stack>

                    {currentUser.features.accounts_signup &&
                      (!currentAccount || !currentAccount.has_environments) && (
                        <LaunchpadSetupContainer
                          account={currentAccount}
                          user={currentUser}
                          contact={contactSales}
                        />
                      )}
                  </Stack>
                </Container>
              </Box>
            </Stack>
          )}
        </Flex>
      </PageSidebarContainer>
    </Flex>
  );
};
