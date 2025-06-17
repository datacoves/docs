import { VStack, HStack } from '@chakra-ui/layout';
import { Dispatch } from 'react';

import { EnvironmentVariablesDeletable } from '../../../../context/UserContext/types';

import { EnvironmentVariableModal } from './EnvironmentVariableModal';
import { EnvironmentVariablesTable } from './EnvironmentVariablesTable';

interface Props {
  setEnvironmentVariables: Dispatch<React.SetStateAction<EnvironmentVariablesDeletable>>;
  environmentVariables: EnvironmentVariablesDeletable;
}

const CodeServerEnvForm = ({ setEnvironmentVariables, environmentVariables }: Props) => {
  return (
    <VStack width="full" spacing="6">
      <HStack w="full" justifyContent="flex-end">
        <EnvironmentVariableModal
          setVariables={setEnvironmentVariables}
          variables={environmentVariables}
        />
      </HStack>
      <HStack w="full">
        <EnvironmentVariablesTable
          setVariables={setEnvironmentVariables}
          variables={environmentVariables}
        />
      </HStack>
    </VStack>
  );
};

export default CodeServerEnvForm;
