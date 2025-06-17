import { Text } from '@chakra-ui/layout';
import { Box, Button, Container, Flex, Heading, Stack, useColorModeValue } from '@chakra-ui/react';
import { useContext } from 'react';
import { useNavigate } from 'react-router-dom';

import { Header } from '../../../../components/Header';
import PageSidebarContainer from '../../../../components/Sidebar/PageSidebarContainer';
import { AccountContext } from '../../../../context/AccountContext';
import { UserContext } from '../../../../context/UserContext';

export const Checkout = () => {
  const { currentUser } = useContext(UserContext);
  const { currentAccount } = useContext(AccountContext);
  const navigate = useNavigate();
  return (
    <Flex flexFlow="column" h="100vh">
      <Header />
      <PageSidebarContainer>
        <Flex bg={useColorModeValue('gray.50', 'gray.800')} px="10" py="12" grow="1">
          <Box maxW="2xl" mx="auto">
            <Container py={{ base: '16', md: '24' }}>
              <Stack spacing={{ base: '8', md: '10' }}>
                <Stack spacing={{ base: '4', md: '5' }} align="center">
                  <Heading>Subscription process completed</Heading>
                  <Text textAlign="center">
                    You&apos;ve just completed the subscription process.
                  </Text>
                  <Stack spacing="3" direction={{ base: 'column', sm: 'row' }} justify="center">
                    {currentUser && currentUser.projects.length > 0 && (
                      <Button colorScheme="blue" onClick={() => navigate('/')}>
                        Continue to launchpad
                      </Button>
                    )}
                    {currentUser?.projects.length === 0 && (
                      <Button colorScheme="blue" onClick={() => navigate('/account-setup')}>
                        {currentAccount?.owned_by === currentUser?.email
                          ? 'Continue account setup'
                          : 'Create new account'}
                      </Button>
                    )}
                  </Stack>
                </Stack>
              </Stack>
            </Container>
          </Box>
        </Flex>
      </PageSidebarContainer>
    </Flex>
  );
};
