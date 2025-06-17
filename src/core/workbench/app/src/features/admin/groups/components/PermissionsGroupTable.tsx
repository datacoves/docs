import { EditIcon, DeleteIcon } from '@chakra-ui/icons';
import {
  Button,
  Stack,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  useColorModeValue as mode,
} from '@chakra-ui/react';
// import React, { useState } from 'react';
import React from 'react';

interface PermissionData {
  project: string;
  resource: string;
  action: string;
}

export const columns = [
  {
    Header: 'Project',
    accessor: 'project',
  },
  {
    Header: 'Resource',
    accessor: 'resource',
  },
  {
    Header: 'Action',
    accessor: 'action',
  },
];
export const PermissionsGroupTable = (props: any) => {
  // const [data, setData] = useState([]);
  const result: PermissionData[] = [];
  props.data?.map((permission: any) => {
    result.push({
      project: permission.project,
      resource: permission.resource,
      action: permission.action,
    });
  });
  // props.setData(result);
  return (
    <Table my="8" borderWidth="1px" fontSize="sm">
      <Thead bg={mode('gray.50', 'gray.800')}>
        <Tr>
          {columns.map((column, index) => (
            <Th whiteSpace="nowrap" scope="col" key={index}>
              {column.Header}
            </Th>
          ))}
          <Th />
        </Tr>
      </Thead>
      <Tbody>
        {result &&
          result.map((row, index) => (
            <Tr key={index}>
              {columns.map((column, index) => {
                const cell = row[column.accessor as keyof typeof row];
                return (
                  <Td whiteSpace="nowrap" key={index}>
                    {cell}
                  </Td>
                );
              })}
              <Td textAlign="right">
                <Stack direction="row">
                  <Button variant="ghost" colorScheme="blue">
                    <EditIcon />
                  </Button>
                  <Button variant="ghost" colorScheme="red">
                    <DeleteIcon />
                  </Button>
                </Stack>
              </Td>
            </Tr>
          ))}
      </Tbody>
    </Table>
  );
};
