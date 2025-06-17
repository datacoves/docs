import { Box, Heading, Flex, Image, Text, Button } from '@chakra-ui/react';

import logo_navyblue from '../../assets/logo_navyblue.svg';
import { getSiteContext } from '../../utils/siteContext';
export const ErrorPage = ({ svg, title, subtitle, body }: any) => {
  const siteContext = getSiteContext();
  const logoUrl = `https://${siteContext.launchpadHost}`;
  return (
    <Flex
      flexDirection="column"
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
            <Image src={svg} alt="Error Icon" />
          </Flex>
        </Box>
        <Box marginLeft="2rem" width="50%" height="100%">
          <Flex height="100%" justify="space-between" flexDirection="column">
            <Box my="0">
              <Heading as="h1" fontSize="10rem" color="blue.900" marginBottom="-5">
                {title}
              </Heading>
              <Heading as="h2" size="xl" color="blue.400">
                {subtitle}
              </Heading>
            </Box>
            <Box>
              {body.map((line: string, index: number) => (
                <Text key={index} fontSize="3xl" color="gray.800">
                  {line}
                </Text>
              ))}
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
  );
};
