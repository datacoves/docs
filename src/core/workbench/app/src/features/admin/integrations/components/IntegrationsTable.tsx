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
  Box,
  useColorModeValue as mode,
  Stack,
  Icon,
} from '@chakra-ui/react';
import React, { useContext, useState } from 'react';
import { HiOutlineCheck, HiOutlineX } from 'react-icons/hi';
import { useNavigate } from 'react-router-dom';

import { AlertDialog } from '../../../../components/AlertDialog';
import { AccountContext } from '../../../../context/AccountContext';
import { Integration } from '../../../global/types';
import { useDeleteIntegrations } from '../api/deleteIntegration';

type IIntegrationColumn = {
  header: string;
  cell: (data: Integration) => JSX.Element;
};

export const IntegrationsTable = (props: any) => {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration>();
  const { currentAccount } = useContext(AccountContext);
  const onClose = () => setIsConfirmOpen(false);
  const navigate = useNavigate();
  const deleteMutation = useDeleteIntegrations();
  const handleDelete = (integration: Integration) => {
    setSelectedIntegration(integration);
    setIsConfirmOpen(true);
  };
  const handleConfirmDelete = () => {
    if (selectedIntegration && currentAccount) {
      deleteMutation.mutate({
        account: currentAccount.slug,
        id: selectedIntegration.id,
      });
    }
  };
  const columns: IIntegrationColumn[] = [
    {
      header: 'Name',
      cell: function NameCell(data: Integration) {
        return <Text>{data.name}</Text>;
      },
    },
    {
      header: 'Type',
      cell: function NameCell(integration: Integration) {
        return <Text>{integration.type}</Text>;
      },
    },
    {
      header: 'Is Default',
      cell: function NameCell(integration: Integration) {
        return (
          <Icon ml={5} fontSize="xl">
            {integration.is_default ? <HiOutlineCheck /> : <HiOutlineX />}
          </Icon>
        );
      },
    },
    {
      header: '',
      cell: function ActionsCell(data: Integration) {
        return (
          <Stack direction="row" justifyContent="flex-start">
            <Button
              variant="ghost"
              colorScheme="blue"
              onClick={() => navigate(`/admin/integrations/edit/${data.id}`)}
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
        header="Delete integration"
        message="Are you sure? You can't undo this action."
        confirmLabel="Delete"
        onClose={onClose}
        onConfirm={handleConfirmDelete}
      />
    </Box>
  );
};
