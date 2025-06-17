import { Flex, Heading, Button, Text, Box, Link, Image } from '@chakra-ui/react';

import icon from '../../assets/500.svg';
import logo_navyblue from '../../assets/logo_navyblue.svg';
import { getSiteContext } from '../../utils/siteContext';
import { HeaderOffline } from '../Header/HeaderOffline';

export const Error500Page = () => {
  const siteContext = getSiteContext();
  const logoUrl = `https://${siteContext.launchpadHost}`;
  return (
    <>
      <HeaderOffline />
      <Flex
        flexDirection="column"
        flexFlow="column"
        width="75vw"
        mx="auto"
        height="100vh"
        justify="center"
        align="center"
      >
        <Box width="100%" py="4" marginBottom="10">
          <Flex justifyContent="center" alignItems="center">
            <Image src={logo_navyblue} alt="DataCoves Logo" w="auto" h="50px" />
          </Flex>
        </Box>
        <Flex width="100%" height="50%" justify="space-between" align="center" flexDirection="row">
          <Box width="50%" height="100%" justifyContent="space-between" alignItems="center">
            <Flex height="100%" justify="center" align="center" flexDirection="column">
              <Image src={icon} alt="Error Icon" />
            </Flex>
          </Box>
          <Box marginLeft="2rem" width="50%" height="100%">
            <Flex height="100%" justify="space-between" flexDirection="column">
              <Box my="0">
                <Heading as="h1" fontSize="10rem" color="blue.900" marginBottom="-5">
                  500
                </Heading>
                <Heading as="h2" size="xl" color="blue.400">
                  Internal Server Error
                </Heading>
              </Box>
              <Box>
                <Text fontSize="3xl" color="gray.800">
                  Something isn’t done loading
                </Text>
                <Text fontSize="3xl" color="gray.800">
                  If this continues,{' '}
                  <Link color="blue.400" href="mailto:support@datacoves.com">
                    contact support
                  </Link>
                </Text>
              </Box>
              <Button
                as="a"
                href={logoUrl}
                size="lg"
                marginLeft="2"
                variant="solid"
                colorScheme="blue"
                width="fit-content"
                alignSelf="flex-start"
              >
                Back to Launchpad
              </Button>
            </Flex>
          </Box>
        </Flex>
      </Flex>
    </>
  );
};
