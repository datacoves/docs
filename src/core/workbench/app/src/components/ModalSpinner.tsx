import {
  VStack,
  Text,
  Flex,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Center,
  Box,
  HStack,
} from '@chakra-ui/react';
import { sample } from 'lodash';
import React, { useEffect, useState } from 'react';
import { FaLightbulb } from 'react-icons/fa';

import { DatacovesSpinner } from './DatacovesSpinner';
import { replaceJSX, TIPS } from './utils';

interface ModalSpinnerProps {
  message: string;
  showSpinner?: boolean;
  sidebar?: boolean;
  details?: string[];
}

export const ModalSpinner = ({ message, showSpinner, sidebar, details }: ModalSpinnerProps) => {
  const [tip, setTip] = useState(sample(TIPS));

  useEffect(() => {
    const interval = setInterval(() => {
      setTip(sample(TIPS));
    }, 15000);

    return () => clearInterval(interval);
  }, []);

  return (
    <Flex
      w={sidebar ? 'calc(100% - 95px)' : '100%'}
      ml={sidebar ? '95px' : '0'}
      h="full"
      background="blackAlpha.500"
      position="fixed"
    >
      <Card m="auto" px="50px" background="white">
        <CardHeader textAlign="center">
          <Heading fontSize="xl">{message}</Heading>
        </CardHeader>
        <CardBody pb={6}>
          {showSpinner && (
            <VStack verticalAlign="center" spacing={2}>
              <Center pos="relative" py={4}>
                <DatacovesSpinner />
              </Center>
              <Box minH="24" my="auto">
                <Card flexDir="row" justifyContent="left" gap={2} p={4} w="md">
                  <VStack alignItems="flex-start">
                    <HStack>
                      <FaLightbulb color="#F49D0C" size={20} />
                      <strong>{tip?.service}</strong>
                    </HStack>
                    <Text>{replaceJSX(tip?.tip || '')}</Text>
                  </VStack>
                </Card>
              </Box>
              {details && details.length > 0 && (
                <VStack mt="20px" my="auto" w="100%">
                  <Box w="100%">
                    <Card maxH="120px" overflowY="auto" color="gray.600">
                      <Flex>
                        <VStack align="start" spacing={1} p={2}>
                          {details?.map((detail, index) => (
                            <Text key={index} fontSize="sm" whiteSpace="pre-wrap">
                              {detail}
                            </Text>
                          ))}
                        </VStack>
                      </Flex>
                    </Card>
                  </Box>
                </VStack>
              )}
            </VStack>
          )}
        </CardBody>
      </Card>
    </Flex>
  );
};
