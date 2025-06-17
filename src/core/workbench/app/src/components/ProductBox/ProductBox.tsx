import {
  Flex,
  Button,
  Text,
  SimpleGrid,
  Heading,
  Stack,
  useColorModeValue,
  Image,
  GridItem,
} from '@chakra-ui/react';
import React from 'react';

export function ProductBox(props: any) {
  return (
    <Flex bg="white" boxShadow={'md'} rounded={'md'} p={6} overflow={'hidden'} role="group">
      <Flex
        w={'210px'}
        bg={'gray.100'}
        mt={-6}
        ml={-6}
        mb={-6}
        pos={'relative'}
        overflow={'hidden'}
      >
        <Image
          src={props.url}
          objectFit="cover"
          filter="saturate(0.5) opacity(0.8)"
          _groupHover={{ filter: 'saturate(0.9) opacity(0.9)' }}
          transition="filter 0.3s ease-in-out;"
        />
      </Flex>
      <Stack flex={1} pl="6">
        <Heading
          color={useColorModeValue('gray.700', 'white')}
          fontSize={'2xl'}
          fontFamily={'body'}
        >
          {props.title}
        </Heading>
        <Text
          color={'blue.500'}
          textTransform={'uppercase'}
          fontWeight={800}
          fontSize={'sm'}
          letterSpacing={1.1}
        >
          {props.subtitle}
        </Text>
        <SimpleGrid columns={4} spacing={4}>
          <GridItem colSpan={3}>
            <Text color={'gray.500'}>{props.text}</Text>
          </GridItem>
          <GridItem colSpan={1} alignItems="flex-end" justifyItems="flex-end" display="flex">
            <Button colorScheme="blue" width="100%" size="sm" onClick={props.onClick}>
              {props.button}
            </Button>
          </GridItem>
        </SimpleGrid>
      </Stack>
    </Flex>
  );
}
