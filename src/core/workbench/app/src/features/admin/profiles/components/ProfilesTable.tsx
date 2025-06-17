import { EditIcon, DeleteIcon } from '@chakra-ui/icons';
import {
  Button,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  Box,
  Text,
  useColorModeValue as mode,
  Stack,
} from '@chakra-ui/react';
import React, { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AlertDialog } from '../../../../components/AlertDialog';
import { AccountContext } from '../../../../context/AccountContext';
import { Profile } from '../../../../context/UserContext/types';
import { ProfileFilesRow } from '../../projects/components/ProfileFilesRow';
import { useDeleteProfiles } from '../api/deleteProfile';

type IProfileColumn = {
  header: string;
  cell: (data: Profile) => JSX.Element;
};

export const ProfilesTable = (props: any) => {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState<string>();
  const { currentAccount } = useContext(AccountContext);
  const onClose = () => setIsConfirmOpen(false);
  const navigate = useNavigate();
  const deleteMutation = useDeleteProfiles();
  const handleDelete = (profileId: string) => {
    setSelectedProfile(profileId);
    setIsConfirmOpen(true);
  };
  const handleConfirmDelete = () => {
    if (selectedProfile && currentAccount) {
      deleteMutation.mutate({
        account: currentAccount.slug,
        id: selectedProfile,
      });
    }
  };
  const columns: IProfileColumn[] = [
    {
      header: 'Name',
      cell: (data: Profile) => {
        return <Text>{data.name}</Text>;
      },
    },
    {
      header: 'Base Profile',
      cell: (data: Profile) => {
        return <Text>{data.files_from?.name ?? 'None'}</Text>;
      },
    },
    {
      header: 'Code Files',
      cell: (data: Profile) => {
        return <ProfileFilesRow filesCount={data.profile_files_count} />;
      },
    },
    {
      header: '',
      cell: (data: Profile) => {
        return (
          <Stack direction="row" justifyContent="flex-start">
            <Button
              variant="ghost"
              colorScheme="blue"
              onClick={() => navigate(`/admin/profiles/edit/${data.id}`)}
            >
              <EditIcon />
            </Button>
            <Button
              variant="ghost"
              colorScheme="red"
              onClick={() => handleDelete(data.id.toString())}
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
        header="Delete profile"
        message="Are you sure? You can't undo this action."
        confirmLabel="Delete"
        onClose={onClose}
        onConfirm={handleConfirmDelete}
      />
    </Box>
  );
};
