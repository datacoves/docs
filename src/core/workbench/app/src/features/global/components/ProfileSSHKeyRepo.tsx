import { Td, Text, Tr } from '@chakra-ui/react';
import React from 'react';

import { TestButton } from '../../../components/TestButton';
import { useTestGitConnection } from '../api/testGitConnection';
import { UserRepository } from '../types';

interface SSHKeyRepoProps {
  repo: UserRepository;
}

export const ProfileSSHKeyRepo = (props: SSHKeyRepoProps) => {
  const { repo } = props;

  const testGitMutation = useTestGitConnection(true);

  const handleTest = () => {
    testGitMutation.mutate({ user_repository_id: parseInt(repo.id) });
  };

  return (
    <Tr>
      <Td>
        <Text maxW="sm">{repo.url}</Text>
      </Td>
      <Td>
        <TestButton
          onClick={handleTest}
          isLoading={testGitMutation.isLoading}
          testType="git clone"
          validatedAt={repo.validated_at}
        />
      </Td>
    </Tr>
  );
};
