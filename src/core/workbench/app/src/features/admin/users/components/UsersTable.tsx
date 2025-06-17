import { EditIcon, DeleteIcon } from '@chakra-ui/icons';
import {
  Button,
  Stack,
  Table,
  Text,
  Tbody,
  Td,
  Th,
  Thead,
  Box,
  Tr,
  useColorModeValue as mode,
} from '@chakra-ui/react';
import { formatRelative, parseISO } from 'date-fns';
import React, { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AlertDialog } from '../../../../components/AlertDialog';
import { AccountContext } from '../../../../context/AccountContext';
import { useDeleteUser } from '../api/deleteUser';
import { UsersRow } from '../components/UsersRow';
import { User } from '../types';

type IUserColumn = {
  header: string;
  cell: (data: User) => JSX.Element;
};

export const UsersTable = (props: any) => {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [selectedUser, setSelectedUser] = React.useState<string>();
  const { currentAccount } = useContext(AccountContext);
  const onClose = () => setIsConfirmOpen(false);
  const navigate = useNavigate();

  const deleteMutation = useDeleteUser();
  const handleDelete = (userId: string) => {
    setSelectedUser(userId);
    setIsConfirmOpen(true);
  };
  const handleConfirmDelete = () => {
    if (selectedUser && currentAccount) {
      deleteMutation.mutate({
        account: currentAccount.slug,
        id: selectedUser,
      });
    }
  };

  const columns: IUserColumn[] = [
    {
      header: 'Name and Email',
      cell: function MemberCell(data: User) {
        return <UsersRow data={{ image: '', name: data.name, email: data.email }} />;
      },
    },
    {
      header: 'Groups',
      cell: function MemberCell(data: User) {
        const result = data.groups.map((group: any) => group.name).join(', ');
        return (
          <Text isTruncated maxWidth="300px">
            {result}
          </Text>
        );
      },
    },
    {
      header: 'Last Login',
      cell: function StatusCell(data: User) {
        return (
          <Text>
            {data.last_login ? formatRelative(parseISO(data.last_login), new Date()) : ''}
          </Text>
        );
      },
    },
    {
      header: '',
      cell: function ActionsCell(data: User) {
        return (
          <Stack direction="row" justifyContent="flex-start">
            <Button
              title="Edit user"
              variant="ghost"
              colorScheme="blue"
              onClick={() => navigate(`/admin/users/edit/${data.id}`)}
            >
              <EditIcon />
            </Button>
            <Button
              title="Delete user"
              variant="ghost"
              colorScheme="red"
              onClick={() => handleDelete(data.id)}
            >
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
        header="Delete user"
        message="Are you sure? You can't undo this action."
        confirmLabel="Delete"
        onClose={onClose}
        onConfirm={handleConfirmDelete}
      />
    </Box>
  );
};
