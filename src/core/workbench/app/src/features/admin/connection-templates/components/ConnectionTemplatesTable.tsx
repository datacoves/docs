import { EditIcon, DeleteIcon } from '@chakra-ui/icons';
import {
  Button,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  Text,
  useColorModeValue as mode,
  Stack,
  VStack,
  Box,
} from '@chakra-ui/react';
import React, { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AlertDialog } from '../../../../components/AlertDialog';
import { AccountContext } from '../../../../context/AccountContext';
import { Project } from '../../../../context/UserContext/types';
import { ConnectionTypeCell } from '../../../global/components/ConnectionTypeCell';
import { ConnectionTemplate } from '../../../global/types';
import { useDeleteConnectionTemplates } from '../api/deleteConnectionTemplate';

type IConnectionColumn = {
  header: string;
  cell: (data: ConnectionTemplate) => JSX.Element;
};

export const ConnectionTemplatesTable = (props: any) => {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [selectedConnectionTemplate, setSelectedConnectionTemplate] =
    useState<ConnectionTemplate>();
  const { currentAccount } = useContext(AccountContext);
  const onClose = () => setIsConfirmOpen(false);
  const navigate = useNavigate();
  const deleteMutation = useDeleteConnectionTemplates();
  const handleDelete = (connection: ConnectionTemplate) => {
    setSelectedConnectionTemplate(connection);
    setIsConfirmOpen(true);
  };
  const handleConfirmDelete = () => {
    if (selectedConnectionTemplate && currentAccount) {
      deleteMutation.mutate({
        account: currentAccount.slug,
        id: selectedConnectionTemplate.id,
      });
    }
  };
  const columns: IConnectionColumn[] = [
    {
      header: 'Project',
      cell: function ProjectCell(data: ConnectionTemplate) {
        const project = props.projects?.find((project: Project) => project.id === data.project);
        return <Text>{project?.name}</Text>;
      },
    },
    {
      header: 'Name',
      cell: function NameCell(data: ConnectionTemplate) {
        return <Text>{data.name}</Text>;
      },
    },
    {
      header: 'Type',
      cell: function NameCell(connection_template: ConnectionTemplate) {
        return <ConnectionTypeCell connectionTemplate={connection_template} />;
      },
    },
    {
      header: 'Used by',
      cell: function NameCell(conn: ConnectionTemplate) {
        const services = conn.service_credentials_count === 1 ? 'service' : 'services';
        const users = conn.user_credentials_count === 1 ? 'user' : 'users';
        return (
          <Text>{`${conn.service_credentials_count} ${services}, ${conn.user_credentials_count} ${users}`}</Text>
        );
      },
    },
    {
      header: '',
      cell: function ActionsCell(data: ConnectionTemplate) {
        return (
          <Stack direction="row" justifyContent="flex-start">
            <Button
              variant="ghost"
              colorScheme="blue"
              onClick={() => navigate(`/admin/connection-templates/edit/${data.id}`)}
            >
              <EditIcon />
            </Button>
            <Button variant="ghost" colorScheme="red" onClick={() => handleDelete(data)}>
              <DeleteIcon />
            </Button>
          </Stack>
        );
      },
    },
  ];
  return (
    <Box w="full" overflow="scroll">
      <Table my="8" borderWidth="1px" fontSize="sm">
        <Thead bg={mode('gray.50', 'gray.800')}>
          <Tr>
            {columns.map((column, index) => (
              <Th whiteSpace="nowrap" scope="col" key={index}>
                {column.header}
              </Th>
            ))}
            <Th />
          </Tr>
        </Thead>
        <Tbody>
          {props.data?.map((row: any, index: number) => (
            <Tr key={index}>
              {columns.map((column, index) => (
                <Td whiteSpace="nowrap" key={index}>
                  {column.cell?.(row)}
                </Td>
              ))}
            </Tr>
          ))}
        </Tbody>
      </Table>
      <AlertDialog
        isOpen={isConfirmOpen}
        header="Delete connection template"
        message={
          <VStack alignItems="flex-start">
            {selectedConnectionTemplate?.service_credentials_count === 0 &&
            selectedConnectionTemplate?.user_credentials_count === 0 ? (
              <Text>You cannot undo this action.</Text>
            ) : (
              <Text>{`${selectedConnectionTemplate?.service_credentials_count} service connections and ${selectedConnectionTemplate?.user_credentials_count} user connections will be permanently deleted.`}</Text>
            )}
            <Text>Are you sure?</Text>
          </VStack>
        }
        confirmLabel="Delete"
        onClose={onClose}
        onConfirm={handleConfirmDelete}
      />
    </Box>
  );
};
