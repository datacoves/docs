import './error.css';
import { Box, Button, Container, Flex, Heading, Stack, Text } from '@chakra-ui/react';

import { Header } from '../Header';
import PageSidebarContainer from '../Sidebar/PageSidebarContainer';

const NotAuthorized = ({ error }: any) => (
  <Flex flexFlow="column" h="100vh">
    <Header />
    <PageSidebarContainer>
      <Box maxW="2xl" mx="auto" py="12">
        <Container py={{ base: '16', md: '24' }}>
          <Stack spacing={{ base: '8', md: '10' }}>
            <Stack spacing={{ base: '4', md: '5' }} align="center">
              <Heading>Action not authorized</Heading>
              <Text color="muted" maxW="2xl" textAlign="center" fontSize="xl">
                {error?.response.data.detail ??
                  "You don't have enough permissions to access this feature."}
              </Text>
              <Stack spacing="3" direction={{ base: 'column', sm: 'row' }} justify="center">
                <Button colorScheme="blue" onClick={() => (window.location.href = '/')}>
                  Continue to launchpad
                </Button>
              </Stack>
            </Stack>
          </Stack>
        </Container>
      </Box>
    </PageSidebarContainer>
  </Flex>
);

export default NotAuthorized;
