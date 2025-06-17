import { Stack } from '@chakra-ui/layout';
import { Button, Flex, HStack, Heading, Text } from '@chakra-ui/react';
import { useEffect, useState } from 'react';

import { Card } from '../../../components/Card';
import { EnvironmentVariablesDeletable, UserEnvironment } from '../../../context/UserContext/types';
import { objectMap } from '../../../utils/inlineListEditable';
import { EnvironmentVariableModal } from '../../admin/environments/components/EnvironmentVariableModal';
import { EnvironmentVariablesTable } from '../../admin/environments/components/EnvironmentVariablesTable';
import { useUpdateUserEnvironmentVariables } from '../api/updateUserEnvironment';

export const UserEnvironmentSettings = ({
  userEnvironment,
}: {
  userEnvironment: UserEnvironment;
}) => {
  const [environmentVariables, setEnvironmentVariables] = useState<EnvironmentVariablesDeletable>(
    objectMap(userEnvironment.variables, (v: string) => {
      return { value: v, delete: false };
    })
  );
  const updateMutation = useUpdateUserEnvironmentVariables(userEnvironment.env_slug);
  const handleSubmit = () => {
    const body = {
      variables: objectMap(environmentVariables, (v) => (v.delete ? undefined : v.value)),
    };
    updateMutation.mutateAsync({ id: userEnvironment.id, body });
  };

  useEffect(() => {
    setEnvironmentVariables(
      objectMap(userEnvironment.variables, (v: string) => {
        return { value: v, delete: false };
      })
    );
  }, [userEnvironment.variables]);

  return (
    <Card>
      <Stack spacing="5">
        <Flex>
          <HStack spacing="1" alignItems="center">
            <Heading size="sm" fontWeight="semibold">
              {userEnvironment.env_name}
            </Heading>
            <Text color="gray.600" size="sm">
              | {userEnvironment.project_name}
            </Text>
          </HStack>
          <Flex flex="1" justifyContent="flex-end">
            <EnvironmentVariableModal
              setVariables={setEnvironmentVariables}
              variables={environmentVariables}
            />
          </Flex>
        </Flex>
        <EnvironmentVariablesTable
          variables={environmentVariables}
          setVariables={setEnvironmentVariables}
        />
        {Object.keys(environmentVariables).length > 0 && (
          <Flex justifyContent="flex-end">
            <Button
              size="sm"
              colorScheme="blue"
              isLoading={updateMutation.isLoading}
              alignSelf="flex-end"
              onClick={() => handleSubmit()}
            >
              Save
            </Button>
          </Flex>
        )}
      </Stack>
    </Card>
  );
};
