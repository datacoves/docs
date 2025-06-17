import { Flex, Text, Heading, Stack, HStack, Table, Thead, Tr, Th } from '@chakra-ui/react';
import React, { useContext } from 'react';

import { AccountContext } from '../../../context/AccountContext';
import { Project, Environment } from '../../../context/UserContext/types';
import { ModalCredentials } from '../../admin';
import { useAllConnectionTemplates } from '../api/getAllConnections';

import { EnvironmentConnections } from './EnvironmentConnections';

export const ProjectSettings = ({ project }: { project: Project }) => {
  const { currentAccount } = useContext(AccountContext);
  const { data: connections, isSuccess: connectionsSuccess } = useAllConnectionTemplates({
    account: currentAccount?.slug,
    project: parseInt(project.id),
    forUsers: true,
  });

  return (
    <>
      {connectionsSuccess &&
        connections &&
        project.environments.map((env: Environment) => {
          return (
            <div key={env.id}>
              {env.services['code-server'].enabled && (
                <Stack spacing="5" pt="8">
                  <HStack>
                    <HStack spacing="1" alignItems="center">
                      <Heading size="sm" fontWeight="semibold">
                        {env.name}
                      </Heading>
                      <Text color="gray.600" size="sm">
                        | {project.name}
                      </Text>
                    </HStack>
                    <Flex flex="1" justifyContent="flex-end">
                      <ModalCredentials
                        title={`New connection for ${project.name} ${env.name}`}
                        connectionTemplates={connections}
                        environmentId={env.id}
                      />
                    </Flex>
                  </HStack>
                  <Table my="8" borderWidth="1px" fontSize="sm">
                    <Thead>
                      <Tr>
                        <Th>Name</Th>
                        <Th>Type</Th>
                        <Th />
                      </Tr>
                    </Thead>
                    <EnvironmentConnections
                      project={project}
                      environment={env}
                      connections={connections}
                    />
                  </Table>
                </Stack>
              )}
            </div>
          );
        })}
    </>
  );
};
