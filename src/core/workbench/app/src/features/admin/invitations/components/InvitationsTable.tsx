import { DeleteIcon, EmailIcon } from '@chakra-ui/icons';
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
import React, { useContext, useState } from 'react';

import { AlertDialog } from '../../../../components/AlertDialog';
import { AccountContext } from '../../../../context/AccountContext';
import { UsersRow } from '../../users/components/UsersRow';
import { useDeleteInvitation } from '../api/deleteInvitation';
import { useResendInvitation } from '../api/resendInvitation';
import { Invitation } from '../types';

type IInvitationColumn = {
  header: string;
  cell: (data: Invitation) => JSX.Element;
};

export const InvitationsTable = (props: any) => {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [selectedInvitation, setSelectedInvitation] = React.useState<string>();
  const { currentAccount } = useContext(AccountContext);
  const onClose = () => setIsConfirmOpen(false);

  const deleteMutation = useDeleteInvitation();
  const handleDelete = (invitationId: string) => {
    setSelectedInvitation(invitationId);
    setIsConfirmOpen(true);
  };

  const resendMutation = useResendInvitation();
  const handleResend = (invitationId: string) => {
    if (invitationId && currentAccount) {
      resendMutation.mutate({
        account: currentAccount.slug,
        id: invitationId,
      });
    }
  };
  const handleConfirmDelete = () => {
    if (selectedInvitation && currentAccount) {
      deleteMutation.mutate({
        account: currentAccount.slug,
        id: selectedInvitation,
      });
    }
  };

  const columns: IInvitationColumn[] = [
    {
      header: 'Name and Email',
      cell: function MemberCell(data: Invitation) {
        return <UsersRow data={{ image: '', name: data.name, email: data.email }} />;
      },
    },
    {
      header: 'Groups',
      cell: function MemberCell(data: Invitation) {
        const result = data.groups.map((group: any) => group.name).join(', ');
        return (
          <Text isTruncated maxWidth="300px">
            {result}
          </Text>
        );
      },
    },
    {
      header: 'Status',
      cell: function StatusCell(data: Invitation) {
        return <Text>{data.status}</Text>;
      },
    },
    {
      header: '',
      cell: function ActionsCell(data: Invitation) {
        return (
          <Stack direction="row" justifyContent="flex-start">
            <Button
              title="Delete invitation"
              variant="ghost"
              colorScheme="red"
              onClick={() => handleDelete(data.id)}
            >
              <DeleteIcon />
            </Button>
            <Button
              title="Resend invitation"
              variant="ghost"
              colorScheme="blue"
              onClick={() => handleResend(data.id)}
            >
              <EmailIcon />
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
        header="Delete invitation"
        message="Are you sure? You can't undo this action."
        confirmLabel="Delete"
        onClose={onClose}
        onConfirm={handleConfirmDelete}
      />
    </Box>
  );
};
