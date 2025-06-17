import {
  Box,
  Flex,
  Heading,
  HStack,
  Text,
  useColorModeValue as mode,
  Stack,
  Input,
  Button,
} from '@chakra-ui/react';
import * as React from 'react';
import { HiOutlineExternalLink } from 'react-icons/hi';

import { Logo } from '../../../components/Icons/Logo';
import { getSiteContext } from '../../../utils/siteContext';

export const SignIn = () => {
  const siteContext = getSiteContext();

  return (
    <Flex minH="100vh" direction={{ base: 'column', md: 'row' }}>
      <Box
        display={{ base: 'none', md: 'block' }}
        maxW={{ base: '20rem', lg: '40rem' }}
        flex="1"
        bg="docs.header"
        color="white"
        px="10"
        py="8"
      >
        <Box>
          <Logo w="auto" h="7" color="white" />
        </Box>
        <Flex
          direction="column"
          align="center"
          justify="center"
          h="full"
          textAlign="center"
          mt="-10"
        >
          <Box>
            <Text
              maxW="md"
              mx="auto"
              fontWeight="extrabold"
              fontSize={{ base: '4xl', lg: '5xl' }}
              letterSpacing="tight"
              lineHeight="normal"
            >
              The most flexible Managed dbt Core platform on the market
            </Text>
            <Text mt="5" maxW="sm" mx="auto">
              We integrate all the modern components needed for an end-to-end secure data platform.
              SaaS or private cloud deployments available.
            </Text>
          </Box>
          <HStack
            justify="center"
            as="a"
            href="https://datacoves.com/product"
            target="blank"
            minW="2xs"
            py="3"
            fontWeight="semibold"
            px="2"
            mt="5"
            border="2px solid white"
            rounded="lg"
            _hover={{ bg: 'whiteAlpha.200' }}
          >
            <Box>Find out more</Box>
            <HiOutlineExternalLink />
          </HStack>
        </Flex>
      </Box>
      <Box
        flex="1"
        px={{ base: '6', md: '10', lg: '16', xl: '28' }}
        py={{ base: '10', md: '64' }}
        bg={{ md: mode('gray.50', 'gray.800') }}
      >
        <Box maxW="xl">
          <Box>
            <Box display={{ md: 'none' }} mb="16">
              <Logo w="auto" h="7" iconColor="blue.400" />
            </Box>
            <Heading
              color="blue.500"
              as="h1"
              size="2xl"
              fontWeight="extrabold"
              letterSpacing="tight"
            >
              Welcome to Datacoves
            </Heading>
            <Text
              mt="3"
              fontSize={{ base: 'xl', md: '3xl' }}
              fontWeight="bold"
              color={mode('gray.500', 'inherit')}
            >
              Sign in to continue
            </Text>
          </Box>

          <Box
            minW={{ md: '420px' }}
            mt="10"
            rounded="xl"
            bg={{ md: mode('white', 'gray.700') }}
            shadow={{ md: 'lg' }}
            px={{ md: '10' }}
            pt={{ base: '8', md: '12' }}
            pb="8"
          >
            <Stack spacing="8">
              <Text fontWeight="semibold" color="gray.500" mb="-20px">
                Cluster Domain
              </Text>
              <Input size="lg" fontSize="md" value={siteContext.host} disabled />
            </Stack>
            <Flex
              direction={{ base: 'column-reverse', md: 'row' }}
              mt="6"
              align="center"
              justify="space-between"
            >
              <Button
                mb={{ base: '4', md: '0' }}
                w={{ base: 'full', md: 'auto' }}
                type="submit"
                as="a"
                href={'https://' + siteContext.host}
                colorScheme="blue"
                size="lg"
                fontSize="md"
                fontWeight="bold"
              >
                Sign in
              </Button>
            </Flex>
          </Box>
        </Box>
      </Box>
    </Flex>
  );
};
