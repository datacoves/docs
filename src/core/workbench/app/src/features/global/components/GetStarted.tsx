import { Box, Button, Flex, Icon, Stack, Text } from '@chakra-ui/react';
import { useContext } from 'react';
import { FaBook } from 'react-icons/fa';

import { UserContext } from '../../../context/UserContext';
import { usePersistedState } from '../../../hooks/usePersistedState';

const GetStarted = () => {
  const { currentUser } = useContext(UserContext);
  const [showGetStarted, setShowGetCollapsed] = usePersistedState('showGetStarted', true);
  const hideGetStarted = () => setShowGetCollapsed(false);
  return (
    <>
      {showGetStarted && currentUser?.features.show_get_started_banner && (
        <Box rounded="lg" bg="white" shadow="base" p={{ base: '4', md: '8' }} pos="relative">
          <Flex alignItems="center" justifyContent="space-between" gap={8}>
            <Flex alignItems="center" gap={8}>
              <Icon as={FaBook} boxSize="60px" color="docs.header" />
              <Box>
                <Text fontSize="xl" fontWeight="bold" mb="2">
                  Let&apos;s get your Datacoves journey started on the right track.
                </Text>
                <Text textAlign="justify">
                  Follow the getting started guides in our documentation.
                </Text>
              </Box>
            </Flex>
            <Stack
              gap={2}
              w="fit-content"
              alignItems="end"
              h="full"
              direction={{ base: 'column', xl: 'row' }}
            >
              <Button variant="outline" px={4} onClick={hideGetStarted}>
                Don&apos;t show this again
              </Button>
              <Button
                variant="solid"
                colorScheme="blue"
                px={4}
                onClick={() => window.open('https://docs.datacoves.com/', '_blank')}
              >
                Go to the docs
              </Button>
            </Stack>
          </Flex>
        </Box>
      )}
    </>
  );
};

export default GetStarted;
