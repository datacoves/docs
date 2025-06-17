import { Box } from '@chakra-ui/react';
import React, { useContext, useState } from 'react';

import { UsersTableActions, UsersTable } from '../..';
import { BasePage } from '../../../../components/AdminLayout';
import { TablePagination } from '../../../../components/AdminLayout/components/TablePagination';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { useDebounce } from '../../../../hooks/useDebounce';
import { useAllGroups } from '../../groups/api/getGroups';
import { useUsers } from '../api/getUsers';

export const Users = () => {
  const pageLimit = 10;
  const [pageOffset, setPageOffset] = useState(0);
  const [selectedGroup, setSelectedGroup] = useState();
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 500);
  const { currentAccount } = useContext(AccountContext);

  const usersQuery = useUsers({
    account: currentAccount?.slug,
    search: debouncedSearchTerm,
    group: selectedGroup,
    limit: pageLimit,
    offset: pageOffset,
  });
  const {
    data: groups,
    isSuccess: groupsSuccess,
    isLoading: isLoadingGroups,
  } = useAllGroups({
    account: currentAccount?.slug,
  });
  const prevPageHandler = () => {
    setPageOffset((current) => current - pageLimit);
  };
  const nextPageHandler = () => {
    setPageOffset((current) => current + pageLimit);
  };
  const setSearchTermAndResetPage = (term: string) => {
    setSearchTerm(term);
    setPageOffset(0);
  };
  return (
    <BasePage header="Users">
      <Box maxW={{ base: 'xl', md: '7xl' }} mx="auto" p="6">
        <LoadingWrapper isLoading={isLoadingGroups} showElements={groupsSuccess}>
          <Box overflowX="auto" p={1}>
            <UsersTableActions
              setSelectedGroup={setSelectedGroup}
              groups={groups}
              setSearchTerm={setSearchTermAndResetPage}
            />
            <LoadingWrapper isLoading={usersQuery.isLoading}>
              <UsersTable data={usersQuery.data?.results} />
              <TablePagination
                prevLink={usersQuery.data?.previous}
                prevHandler={prevPageHandler}
                nextLink={usersQuery.data?.next}
                nextHandler={nextPageHandler}
                total={usersQuery.data?.count}
                objectName="user"
              />
            </LoadingWrapper>
          </Box>
        </LoadingWrapper>
      </Box>
    </BasePage>
  );
};
