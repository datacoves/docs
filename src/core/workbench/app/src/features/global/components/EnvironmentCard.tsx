import {
  Box,
  Button,
  HStack,
  Stack,
  Icon,
  Tag,
  Text,
  useColorModeValue,
  Wrap,
  Flex,
  Heading,
  Link,
  Tooltip,
  Progress,
  Skeleton,
} from '@chakra-ui/react';
import * as Sentry from '@sentry/react';
import React, { useContext, useEffect, useRef, useState } from 'react';
import { FaLink } from 'react-icons/fa';
import { useQueryClient } from 'react-query';

import { UserContext } from '../../../context/UserContext';
import { Environment, Project } from '../../../context/UserContext/types';
import { getSiteContext } from '../../../utils/siteContext';
import { WorkbenchStatus } from '../../workbench/workbench';
import { getWorkbenchStatus } from '../../workbench/workbench/api/getWorkbenchStatus';
import { WebSocketContext } from '../websocket/WebSocketContext';

type TEnvironmentCard = {
  environment: Environment;
  project: Project;
};

const STATUS_POLLING_PERIOD = 2; // seconds
const POLLING_PERIOD_LIMIT = 100; // seconds

export const EnvironmentCard = (props: TEnvironmentCard) => {
  const siteContext = getSiteContext();
  const queryClient = useQueryClient();

  const { environment } = props;
  const url = `https://${environment.slug}.${siteContext.launchpadHost}`;
  const { currentUser } = useContext(UserContext);
  const [wstatus, setWstatus] = useState<WorkbenchStatus>();
  const { webSocketFailed, getEnvStatus } = useContext(WebSocketContext);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const pollingPeriod = useRef(STATUS_POLLING_PERIOD);

  useEffect(() => {
    // Check Pomerium state
    const pomeriumStatus = wstatus?.services?.pomerium;
    if (pomeriumStatus && pomeriumStatus === 'not_found') {
      setIsLoading(true);
    } else {
      setIsLoading(
        (wstatus === undefined || wstatus?.status === 'not_found') &&
          pollingPeriod.current <= POLLING_PERIOD_LIMIT
      );
    }
  }, [wstatus]);

  useEffect(() => {
    const envStatus = getEnvStatus(environment.slug);
    if (envStatus) {
      const result = Object.assign(envStatus);
      if (result.check_status === 'max_retries') {
        pollingPeriod.current = POLLING_PERIOD_LIMIT + 1;
      }
      setWstatus(result.details);
    }
  }, [environment.slug, getEnvStatus]);

  useEffect(() => {
    if (webSocketFailed && currentUser && pollingPeriod.current <= POLLING_PERIOD_LIMIT) {
      setTimeout(() => {
        getWorkbenchStatus(environment.slug).then((resp) => {
          if (resp.status === 'running') {
            queryClient.invalidateQueries('getUserInfo');
          }
          setWstatus(resp);
        });
        pollingPeriod.current = pollingPeriod.current * 1.5;
        if (pollingPeriod.current > POLLING_PERIOD_LIMIT) {
          Sentry.captureMessage(
            `Launchpad polling period time exceeded for environment ${environment.slug}`
          );
        }
      }, 1000 * pollingPeriod.current);
    }
  }, [currentUser, wstatus, environment, queryClient, webSocketFailed]);

  return (
    <Box
      bg={useColorModeValue('white', 'gray.700')}
      w="full"
      p={{ base: '6', md: '8' }}
      rounded={{ sm: 'lg' }}
      shadow={{ md: 'base' }}
    >
      {wstatus === undefined && (
        <Box>
          <Stack>
            <Skeleton height="20px" />
            <Skeleton height="20px" />
            <Skeleton height="20px" />
            <Skeleton height="20px" />
            <Skeleton height="20px" />
          </Stack>
        </Box>
      )}

      {wstatus !== undefined && (
        <Box>
          <Flex justifyContent="space-between" alignItems="center">
            <Heading
              size="md"
              fontWeight="bold"
              letterSpacing="tight"
              marginEnd="6"
              textTransform="capitalize"
            >
              {environment.name}
            </Heading>
            <Button
              size="sm"
              colorScheme={pollingPeriod.current <= POLLING_PERIOD_LIMIT ? 'blue' : 'red'}
              isLoading={isLoading}
              isDisabled={pollingPeriod.current > POLLING_PERIOD_LIMIT}
              onClick={() => {
                setIsLoading(true);
                window.location.href = url;
              }}
            >
              {pollingPeriod.current > POLLING_PERIOD_LIMIT ? (
                <Tooltip label="Environment wait time exceeded. Retry again in a few minutes.">
                  Error
                </Tooltip>
              ) : (
                'Open'
              )}
            </Button>
          </Flex>
        </Box>
      )}

      {wstatus?.status === 'not_found' && (
        <Box>
          <Stack spacing="1" mt="2">
            <HStack fontSize="sm">
              <Icon as={FaLink} color="gray.500" />
              <Text>{url}</Text>
            </HStack>
            <Text mt="4" mb="2">
              Setting up environment...
            </Text>
            <Flex align="center" gap={2}>
              <Progress
                hasStripe
                colorScheme="blue"
                size="xs"
                flex="1"
                value={wstatus?.progress ?? 100}
              />
              <Text fontSize="sm" minW="30px">
                {Math.round(wstatus?.progress ?? 100)}%
              </Text>
            </Flex>
            <Text fontSize="sm" minW="30px">
              This can take up to 10 minutes while we set everything up.
            </Text>
          </Stack>
        </Box>
      )}

      {wstatus && wstatus.status !== 'not_found' && (
        <Box>
          <Stack spacing="1" mt="2">
            <HStack fontSize="sm">
              <Icon as={FaLink} color="gray.500" />
              <Link href={url}>{url}</Link>
            </HStack>
            <Text fontWeight="semibold" mt="4" mb="2">
              Stack
            </Text>
          </Stack>

          <Wrap mt="2">
            {Object.keys(environment.services)
              .map((serviceKey) => (serviceKey === 'code-server' ? 'vs-code' : serviceKey))
              .sort((a, b) => (a > b ? 1 : -1))
              .map((displayServiceKey) => {
                const serviceKey =
                  displayServiceKey === 'vs-code' ? 'code-server' : displayServiceKey;
                return (
                  environment.services[serviceKey].enabled &&
                  (environment.services[serviceKey].valid ? (
                    !currentUser?.has_license &&
                    ['code-server', 'local-dbt-docs'].includes(serviceKey) ? (
                      <Tooltip
                        key={serviceKey}
                        label="Missing developer license, please contact your account administrator."
                      >
                        <Tag colorScheme="orange">{displayServiceKey}</Tag>
                      </Tooltip>
                    ) : (
                      <Tooltip key={serviceKey} label="Service enabled">
                        <Tag colorScheme="green">{displayServiceKey}</Tag>
                      </Tooltip>
                    )
                  ) : environment.services[serviceKey].unmet_preconditions ? (
                    <Tooltip
                      key={serviceKey}
                      label={environment.services[serviceKey].unmet_preconditions
                        ?.map((precond) => precond.message)
                        .join(', ')}
                    >
                      <Tag colorScheme="red">{displayServiceKey}</Tag>
                    </Tooltip>
                  ) : (
                    <Tooltip key={serviceKey} label="Service enabled">
                      <Tag colorScheme="green">{displayServiceKey}</Tag>
                    </Tooltip>
                  ))
                );
              })}
          </Wrap>
        </Box>
      )}
    </Box>
  );
};
