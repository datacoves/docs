import { ChevronUpIcon, ChevronDownIcon } from '@chakra-ui/icons';
import { Box } from '@chakra-ui/layout';
import { Tr, Td } from '@chakra-ui/react';
import { useState } from 'react';

import { Group } from '../types';

interface Props {
  environmentGroups: Group[];
  columns: {
    header: string;
    cell: (data: Group) => JSX.Element;
  }[];
  env: string;
}

export const EnvGroupCollapse = ({ environmentGroups, columns, env }: Props) => {
  const [showEnv, setShowEnv] = useState(false);
  return (
    <>
      {!!environmentGroups.length && (
        <Tr onClick={() => setShowEnv((prev) => !prev)} cursor="pointer">
          <Td colSpan={4} pl={16} fontWeight="semibold" fontSize="sm">
            {env} Environment
            {showEnv ? <ChevronUpIcon /> : <ChevronDownIcon />}
          </Td>
        </Tr>
      )}
      {showEnv &&
        environmentGroups.map((envGroup) => {
          return (
            <Tr key={envGroup.id}>
              {columns.map((column, index) => (
                <Td whiteSpace="nowrap" key={index} pl={index === 0 ? 20 : 6}>
                  <Box as="span" flex="1" textAlign="left">
                    {column.cell?.(envGroup)}
                  </Box>
                </Td>
              ))}
            </Tr>
          );
        })}
    </>
  );
};
