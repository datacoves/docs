import { EditIcon, DeleteIcon, ChevronDownIcon, ChevronUpIcon } from '@chakra-ui/icons';
import {
  Button,
  Stack,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Box,
  Tr,
  useColorModeValue as mode,
} from '@chakra-ui/react';
import { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AlertDialog } from '../../../../components/AlertDialog';
import { ProjectGroupType } from '../../../../components/UserGroups/utils';
import { AccountContext } from '../../../../context/AccountContext';
import { useDeleteGroup } from '../api/deleteGroup';
import { Group } from '../types';

import { ProjectsGroupCollapse } from './ProjectsGroupCollapse';

type IGroupColumn = {
  header: string;
  cell: (data: Group) => JSX.Element;
};

export const GroupsTable = (props: any) => {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<string>();
  const [showProjects, setShowProjects] = useState(true);
  const [showAccountGroups, setShowAccountGroups] = useState(false);
  const { currentAccount } = useContext(AccountContext);
  const onClose = () => setIsConfirmOpen(false);
  const navigate = useNavigate();

  const deleteMutation = useDeleteGroup();
  const handleDelete = (groupId: string) => {
    setSelectedGroup(groupId);
    setIsConfirmOpen(true);
  };
  const handleConfirmDelete = () => {
    if (selectedGroup && currentAccount) {
      deleteMutation.mutate({
        account: currentAccount.slug,
        id: selectedGroup,
      });
    }
  };

  const {
    categorizedGroups,
  }: {
    categorizedGroups: {
      account: { accountGroups: Group[]; name: string };
      projects: ProjectGroupType;
    };
  } = props;

  const columns: IGroupColumn[] = [
    {
      header: 'Name',
      cell: function MemberCell(data: Group) {
        return <Text>{data.extended_group.name}</Text>;
      },
    },
    {
      header: 'Permissions',
      cell: function PermissionsCell(data: Group) {
        return <Text>{data.permissions.length}</Text>;
      },
    },
    {
      header: 'Users',
      cell: function UsersCell(data: Group) {
        return <Text>{data.users_count}</Text>;
      },
    },
    {
      header: '',
      cell: function ActionsCell(data: Group) {
        return (
          <Stack direction="row" justifyContent="flex-start">
            <Button
              variant="ghost"
              colorScheme="blue"
              onClick={() => navigate(`/admin/groups/edit/${data.id}`)}
            >
              <EditIcon />
            </Button>
            <Button variant="ghost" colorScheme="red" onClick={() => handleDelete(data.id)}>
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
          {!!categorizedGroups.account.accountGroups.length && (
            <Tr
              onClick={() => setShowAccountGroups((prev) => !prev)}
              fontWeight="bold"
              w="full"
              cursor="pointer"
            >
              <Td colSpan={4}>
                {categorizedGroups.account.name} Groups
                {showAccountGroups ? <ChevronUpIcon /> : <ChevronDownIcon />}
              </Td>
            </Tr>
          )}
          {showAccountGroups &&
            categorizedGroups.account.accountGroups?.map((row: Group, index: number) => (
              <Tr key={index}>
                {columns.map((column, index) => (
                  <Td pl={10} whiteSpace="nowrap" key={index}>
                    <Box as="span" flex="1" textAlign="left">
                      {column.cell?.(row)}
                    </Box>
                  </Td>
                ))}
              </Tr>
            ))}
          {!!Object.keys(categorizedGroups.projects).length && (
            <Tr
              onClick={() => setShowProjects((prev) => !prev)}
              fontWeight="bold"
              w="full"
              cursor="pointer"
            >
              <Td colSpan={4}>
                Project Groups
                {showProjects ? <ChevronUpIcon /> : <ChevronDownIcon />}
              </Td>
            </Tr>
          )}

          {showProjects &&
            Object.keys(categorizedGroups.projects).map((key) => (
              <ProjectsGroupCollapse
                projectsGroup={categorizedGroups.projects[key]}
                columns={columns}
                key={key}
              />
            ))}
        </Tbody>
      </Table>
      <AlertDialog
        isOpen={isConfirmOpen}
        header="Delete group"
        message="Are you sure? You can't undo this action."
        confirmLabel="Delete"
        onClose={onClose}
        onConfirm={handleConfirmDelete}
      />
    </Box>
  );
};
