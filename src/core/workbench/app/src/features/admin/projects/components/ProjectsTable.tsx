import { EditIcon, DeleteIcon, LockIcon } from '@chakra-ui/icons';
import {
  Button,
  Stack,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Box,
  Tr,
  useColorModeValue as mode,
} from '@chakra-ui/react';
import React, { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AlertDialog } from '../../../../components/AlertDialog';
import { TestButton } from '../../../../components/TestButton';
import { AccountContext } from '../../../../context/AccountContext';
import { Project } from '../../../../context/UserContext/types';
import { useTestGitConnection } from '../../../global/api/testGitConnection';
import { ConnectionTemplate } from '../../../global/types';
import { useDeleteProject } from '../api/deleteProjects';

import { ConnectionTemplatesRow } from './ConnectionTemplatesRow';
import { EnvironmentsRow } from './EnvironmentsRow';
import { ProjectsRow } from './ProjectsRow';

type IProjectColumn = {
  header: string;
  cell: (data: Project) => JSX.Element;
};

export const ProjectsTable = (props: any) => {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  // const [currentProject, setCurrentProject] = useState<string>();
  const [selectedProject, setSelectedProject] = useState<string>();
  const { currentAccount } = useContext(AccountContext);
  const onClose = () => setIsConfirmOpen(false);
  const navigate = useNavigate();

  const deleteMutation = useDeleteProject();
  const testGitMutation = useTestGitConnection(true);
  const handleDelete = (projectId: string) => {
    setSelectedProject(projectId);
    setIsConfirmOpen(true);
  };
  const handleConfirmDelete = () => {
    if (selectedProject && currentAccount) {
      deleteMutation.mutate({
        account: currentAccount.slug,
        id: selectedProject,
      });
    }
  };
  const handleTest = (project: Project) => {
    testGitMutation.mutate({ project_id: parseInt(project.id) });
  };

  const columns: IProjectColumn[] = [
    {
      header: 'Name',
      cell: function NameCell(data: Project) {
        return <ProjectsRow name={data.name} url={data.repository.git_url} />;
      },
    },
    {
      header: 'Connection Templates',
      cell: function ConnectionsCell(data: Project) {
        const connTemplates = data?.connection_templates?.map((conn: ConnectionTemplate) => {
          return conn.name;
        });
        return (
          <ConnectionTemplatesRow
            conns={connTemplates}
            projectName={data.name}
            projectId={data.id}
          />
        );
      },
    },
    {
      header: 'Environments',
      cell: function EnviromentsCell(data: Project) {
        const envs = data?.environments?.map((env: any) => {
          return env.name;
        });
        return <EnvironmentsRow envs={envs} projectName={data.name} projectId={data.id} />;
      },
    },
    {
      header: '',
      cell: function ActionsCell(data: Project) {
        return (
          <Stack direction="row" justifyContent="flex-start" alignItems="center">
            <TestButton
              testType="connection"
              validatedAt={data.validated_at}
              onClick={() => handleTest(data)}
              isLoading={testGitMutation.isLoading}
            />
            <Button
              variant="ghost"
              colorScheme="blue"
              p={1}
              onClick={() => navigate(`/admin/projects/edit/${data.id}`)}
            >
              <EditIcon />
            </Button>
            <Button
              variant="ghost"
              colorScheme="blue"
              onClick={() => window.open(`/admin/projects/edit/${data.id}/keys`, '_blank')}
            >
              <LockIcon />
            </Button>
            <Button p={1} variant="ghost" colorScheme="red" onClick={() => handleDelete(data.id)}>
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
        header="Delete project"
        message="Are you sure? You can't undo this action."
        confirmLabel="Delete"
        onClose={onClose}
        onConfirm={handleConfirmDelete}
      />
    </Box>
  );
};
