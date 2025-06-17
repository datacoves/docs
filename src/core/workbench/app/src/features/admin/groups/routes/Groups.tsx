import { Box } from '@chakra-ui/react';
import React, { useContext, useMemo, useState } from 'react';

import { GroupsTableActions, GroupsTable } from '../..';
import { BasePage } from '../../../../components/AdminLayout';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import {
  addProjectsIntoProjectGroup,
  ProjectGroupType,
} from '../../../../components/UserGroups/utils';
import { AccountContext } from '../../../../context/AccountContext';
import { useDebounce } from '../../../../hooks/useDebounce';
import { useGroups } from '../api/getGroups';
import { Group } from '../types';

export const Groups = () => {
  const [selectedGroup, setSelectedGroup] = useState();
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 500);
  const { currentAccount } = useContext(AccountContext);

  const groupsQuery = useGroups({
    account: currentAccount?.slug,
    search: debouncedSearchTerm,
    group: selectedGroup,
    limit: 300,
  });

  const allGroups = groupsQuery.data?.results;

  const categorizedGroups: {
    account: { accountGroups: Group[]; name: string };
    projects: ProjectGroupType;
  } = useMemo(() => {
    const accountGroup = allGroups?.filter(
      (group: Group) => !group.extended_group.project && !group.extended_group.environment
    );
    const projectsGroup = addProjectsIntoProjectGroup(allGroups);
    return {
      account: {
        accountGroups: [...(accountGroup || [])],
        name: `${currentAccount?.name} Account`,
      },
      projects: projectsGroup,
    };
  }, [allGroups, currentAccount?.name]);

  return (
    <BasePage header="Groups">
      <Box maxW={{ base: 'xl', md: '7xl' }} mx="auto" p="6">
        <Box overflowX="auto" p={1}>
          <GroupsTableActions setSelectedGroup={setSelectedGroup} setSearchTerm={setSearchTerm} />
          <LoadingWrapper isLoading={groupsQuery.isLoading} showElements={groupsQuery.isSuccess}>
            <GroupsTable data={groupsQuery.data?.results} categorizedGroups={categorizedGroups} />
          </LoadingWrapper>
        </Box>
      </Box>
    </BasePage>
  );
};
