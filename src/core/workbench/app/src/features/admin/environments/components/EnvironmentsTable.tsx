import { EditIcon, DeleteIcon, LockIcon } from '@chakra-ui/icons';
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
  Spinner,
} from '@chakra-ui/react';
import React, { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AlertDialog } from '../../../../components/AlertDialog';
import { MaxWidthTableCell } from '../../../../components/MaxWidthTableCell';
import { AccountContext } from '../../../../context/AccountContext';
import { Environment, Project } from '../../../../context/UserContext/types';
import { ServiceCredentialsRow } from '../../projects/components/ServiceCredentialsRow';
import { useDeleteEnvironments } from '../api/deleteEnvironment';

type IEnvironmentColumn = {
  header: string;
  cell: (data: Environment) => JSX.Element;
};

export const EnvironmentsTable = (props: any) => {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [selectedEnvironment, setSelectedEnvironment] = useState<string>();
  const { currentAccount } = useContext(AccountContext);
  const onClose = () => setIsConfirmOpen(false);
  const navigate = useNavigate();
  const deleteMutation = useDeleteEnvironments();
  const handleDelete = (environmentId: string) => {
    setSelectedEnvironment(environmentId);
    setIsConfirmOpen(true);
  };
  const handleConfirmDelete = () => {
    if (selectedEnvironment && currentAccount) {
      deleteMutation.mutate({
        account: currentAccount.slug,
        id: selectedEnvironment,
      });
    }
  };
  const columns: IEnvironmentColumn[] = [
    {
      header: 'Project',
      cell: (env: Environment) => {
        const project = props.projects?.find((project: Project) => project.id === env.project);
        return <MaxWidthTableCell value={project?.name} maxW="250px" />;
      },
    },
    {
      header: 'Name',
      cell: (data: Environment) => {
        return <MaxWidthTableCell value={data?.name} maxW="250px" />;
      },
    },
    {
      header: 'Service connections',
      cell: (env: Environment) => {
        return (
          <ServiceCredentialsRow
            credsCount={env.service_credentials_count}
            environmentId={env.id}
          />
        );
      },
    },
    {
      header: '',
      cell: (env: Environment) => {
        if (Number(env.id) === Number(selectedEnvironment) && deleteMutation.isLoading) {
          return (
            <Stack direction="row" justifyContent="flex-start" gap={2}>
              <Spinner size="sm" />
              <Text>Deletion in progress</Text>
            </Stack>
          );
        } else {
          return (
            <Stack direction="row" justifyContent="flex-start">
              <Button
                variant="ghost"
                colorScheme="blue"
                onClick={() => navigate(`/admin/environments/edit/${env.id}`)}
              >
                <EditIcon />
              </Button>
              {env.airflow_config?.api_enabled && (
                <Button
                  variant="ghost"
                  colorScheme="blue"
                  onClick={() => window.open(`/admin/environments/edit/${env.id}/keys`, '_blank')}
                >
                  <LockIcon />
                </Button>
              )}
              <Button
                variant="ghost"
                colorScheme="red"
                onClick={() => handleDelete(env.id.toString())}
              >
                <DeleteIcon />
              </Button>
            </Stack>
          );
        }
      },
    },
  ];
  const selectedEnvInfo = props.data.find(
    ({ id }: { id: number }) => id === Number(selectedEnvironment)
  );
  const envName =
    selectedEnvironment && `"${selectedEnvInfo?.name} (${selectedEnvInfo?.slug})" Environment`;

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
                <Td
                  whiteSpace="nowrap"
                  key={index}
                  px={2}
                  opacity={
                    row.id === Number(selectedEnvironment) && deleteMutation.isLoading ? 0.5 : 1
                  }
                >
                  {column.cell?.(row)}
                </Td>
              ))}
            </Tr>
          ))}
        </Tbody>
      </Table>
      <AlertDialog
        isOpen={isConfirmOpen}
        header="Delete environment"
        message={`Are you sure that you want to delete ${envName}? You can't undo this action`}
        confirmLabel="Delete"
        onClose={onClose}
        onConfirm={handleConfirmDelete}
      />
    </Box>
  );
};
