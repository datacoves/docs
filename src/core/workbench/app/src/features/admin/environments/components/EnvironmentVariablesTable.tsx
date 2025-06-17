import { Stack, Table, Tbody, Td, Text, Thead, Box, Tr, Th, Switch } from '@chakra-ui/react';
import React from 'react';

import { EnvironmentVariablesDeletable } from '../../../../context/UserContext/types';

import { EnvironmentVariableModal } from './EnvironmentVariableModal';

interface EnvironmentVariablesTableProps {
  setVariables: (environmentVariables: EnvironmentVariablesDeletable) => void;
  variables: EnvironmentVariablesDeletable;
}

export const EnvironmentVariablesTable = (props: EnvironmentVariablesTableProps) => {
  const { setVariables, variables } = props;

  return (
    <>
      {Object.keys(variables).length === 0 && <Text>No environment variables created yet.</Text>}
      {Object.keys(variables).length > 0 && (
        <Box w="full" overflow="scroll">
          <Table borderWidth="1px" fontSize="sm">
            <Thead>
              <Tr>
                <Th>Key</Th>
                <Th>Value</Th>
                <Th />
                <Th>Delete?</Th>
              </Tr>
            </Thead>
            <Tbody>
              {Object.keys(variables).map((key: string, index: number) => (
                <Tr key={index}>
                  <Td>
                    <Text>{key}</Text>
                  </Td>
                  <Td whiteSpace="nowrap" key={index}>
                    <Text>{variables[key].value}</Text>
                  </Td>
                  <Td>
                    <Stack direction="row" justifyContent="flex-start">
                      <EnvironmentVariableModal
                        setVariables={setVariables}
                        variables={variables}
                        variable={key}
                      />
                    </Stack>
                  </Td>
                  <Td>
                    <Switch
                      onChange={(event: any) => {
                        setVariables({
                          ...variables,
                          [key]: { value: variables[key].value, delete: event.target.checked },
                        });
                      }}
                    />
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}
    </>
  );
};
