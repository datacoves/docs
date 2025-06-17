import { Text, Tbody, Tr, Td } from '@chakra-ui/react';
import React from 'react';

import { Environment, Project } from '../../../context/UserContext/types';
import { ModalCredentials } from '../../admin';
import { useProfileCredentialsList } from '../api/getProfileCredentialsList';
import { RConnectionTemplate, UserCredential } from '../types';

import { ConnectionTypeCell } from './ConnectionTypeCell';

interface EnvironmentConnectionProps {
  project: Project;
  environment: Environment;
  connections: RConnectionTemplate[];
}

export const EnvironmentConnections = (props: EnvironmentConnectionProps) => {
  const { project, environment, connections } = props;
  const { data: userCredentials, isSuccess: userCredentialsSuccess } = useProfileCredentialsList({
    environment: parseInt(environment.id),
  });

  return (
    <Tbody>
      {userCredentialsSuccess &&
        userCredentials
          ?.sort((a, b) => (a.name > b.name ? 1 : -1))
          .map((credential: UserCredential) => {
            const connectionTemplate = connections?.find(
              (connection) => connection.id === credential.connection_template
            );
            return (
              <Tr key={credential.id} fontSize="sm">
                {connectionTemplate && (
                  <>
                    <Td>
                      <Text fontSize="sm" maxW="100px">
                        {credential.name}
                      </Text>
                    </Td>
                    <Td>
                      <ConnectionTypeCell connectionTemplate={connectionTemplate} />
                    </Td>
                    <Td alignItems="center">
                      <ModalCredentials
                        title={`Edit connection for ${project.name} ${environment.name}`}
                        connectionTemplates={connections}
                        userCredential={credential}
                        environmentId={environment.id}
                      />
                    </Td>
                  </>
                )}
              </Tr>
            );
          })}
    </Tbody>
  );
};
