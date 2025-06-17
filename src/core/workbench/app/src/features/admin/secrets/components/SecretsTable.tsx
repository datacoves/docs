import { EditIcon, DeleteIcon, WarningTwoIcon } from '@chakra-ui/icons';
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
  Tag,
  Tooltip,
} from '@chakra-ui/react';
import { formatRelative, parseISO } from 'date-fns';
import React, { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AlertDialog } from '../../../../components/AlertDialog';
import { MaxWidthTableCell } from '../../../../components/MaxWidthTableCell';
import { AccountContext } from '../../../../context/AccountContext';
import { Project, Environment } from '../../../../context/UserContext/types';
import { Secret } from '../../../global/types';
import { useDeleteSecrets } from '../api/deleteSecret';

type ISecretColumn = {
  header: string;
  cell: (data: Secret) => JSX.Element;
};

export const SecretsTable = (props: any) => {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [selectedSecret, setSelectedSecret] = useState<Secret>();
  const { currentAccount } = useContext(AccountContext);
  const onClose = () => setIsConfirmOpen(false);
  const navigate = useNavigate();
  const deleteMutation = useDeleteSecrets();
  const handleDelete = (secret: Secret) => {
    setSelectedSecret(secret);
    setIsConfirmOpen(true);
  };
  const handleConfirmDelete = () => {
    if (selectedSecret && currentAccount) {
      deleteMutation.mutate({
        account: currentAccount.slug,
        id: selectedSecret.id,
      });
    }
  };
  const columns: ISecretColumn[] = [
    {
      header: 'Project',
      cell: (data: Secret) => {
        const project = props.projects?.find((project: Project) => project.id == data.project);
        return (
          <Text>
            {data.secrets_backend_error && (
              <Tooltip label={`Issues found when retrieving secret from ${data.backend}`}>
                <WarningTwoIcon color="orange.400" />
              </Tooltip>
            )}
            &nbsp;
            {project?.name}
          </Text>
        );
      },
    },
    {
      header: 'Slug',
      cell: function NameCell(data: Secret) {
        return <MaxWidthTableCell value={data?.slug} maxW="150px" />;
      },
    },
    {
      header: 'Tags',
      cell: function NameCell(data: any) {
        return (
          <Text>
            {data.tags.map((tag: string) => (
              <Tag key={tag} mr="1">
                {tag}
              </Tag>
            ))}
          </Text>
        );
      },
    },
    {
      header: 'Shared with',
      cell: function NameCell(data: Secret) {
        const environment = props.environments?.find(
          (env: Environment) => env.id == data.environment
        );
        const resource = environment ? `${environment.name} (${environment.slug})` : 'Project';
        return (
          <MaxWidthTableCell
            value={
              data.users && data.services
                ? resource
                : data.users
                ? `${resource} Users`
                : data.services
                ? `${resource} Services`
                : 'Not shared'
            }
            maxW="150px"
          />
        );
      },
    },
    {
      header: 'Author',
      cell: function NameCell(data: Secret) {
        return <MaxWidthTableCell value={data.created_by_name} maxW="150px" />;
      },
    },
    {
      header: 'Last Retrieved',
      cell: function NameCell(data: Secret) {
        return (
          <MaxWidthTableCell
            value={data.accessed_at ? formatRelative(parseISO(data.accessed_at), new Date()) : ''}
            maxW="150px"
          />
        );
      },
    },
    {
      header: '',
      cell: function ActionsCell(data: Secret) {
        return data.is_system ? (
          <></>
        ) : (
          <Stack direction="row" justifyContent="flex-start">
            <Button
              variant="ghost"
              colorScheme="blue"
              onClick={() => navigate(`/admin/secrets/edit/${data.id}`)}
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
    <Box w="full">
      <Table my="8" borderWidth="1px" fontSize="sm">
        <Thead bg={mode('gray.50', 'gray.800')}>
          <Tr>
            {columns.map((column, index) => (
              <Th whiteSpace="nowrap" scope="col" key={index} px={2}>
                {column.header}
              </Th>
            ))}
          </Tr>
        </Thead>
        <Tbody>
          {props.data?.map((row: any, index: number) => (
            <Tr key={index}>
              {columns.map((column, index) => (
                <Td whiteSpace="nowrap" key={index} px={2}>
                  {column.cell?.(row)}
                </Td>
              ))}
            </Tr>
          ))}
        </Tbody>
      </Table>
      <AlertDialog
        isOpen={isConfirmOpen}
        header="Delete secret"
        message="Are you sure? You can't undo this action."
        confirmLabel="Delete"
        onClose={onClose}
        onConfirm={handleConfirmDelete}
      />
    </Box>
  );
};
