import { Flex, Tooltip, Box } from '@chakra-ui/react';

import { getSiteContext } from '../../utils/siteContext';

import { Logo } from './Logo';

export function HeaderOffline() {
  const siteContext = getSiteContext();
  const logoUrl = `https://${siteContext.launchpadHost}`;
  return (
    <Flex
      align="center"
      zIndex="10"
      bg="blue.900"
      color="white"
      px="6"
      minH="12"
      position="fixed"
      w="100%"
      borderBottom="1px"
      borderColor="gray.600"
    >
      <Flex justify="space-between" align="center" w="full">
        <Flex flexBasis="100%">
          {/* Desktop Logo placement */}
          <Flex alignItems="center">
            <Tooltip label="Go to Launchpad" placement="right" hasArrow bg="white" color="black">
              <Box href={logoUrl} id="logo-button" as="a" justifyContent="flex-start">
                <Logo display={{ base: 'none', lg: 'block' }} flexShrink={0} h="6" w="auto" />
              </Box>
            </Tooltip>
          </Flex>
        </Flex>
      </Flex>
    </Flex>
  );
}
