import { Box } from '@chakra-ui/react';
import React, { useContext, useState } from 'react';

import { BasePage } from '../../../../components/AdminLayout';
import { TablePagination } from '../../../../components/AdminLayout/components/TablePagination';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { useDebounce } from '../../../../hooks/useDebounce';
import { useAllGroups } from '../../groups/api/getGroups';
import { UsersTableActions } from '../../users/components';
import { useInvitations } from '../api/getInvitations';
import { InvitationsTable } from '../components';

export const Invitations = () => {
  const pageLimit = 10;
  const [pageOffset, setPageOffset] = useState(0);
  const [selectedGroup, setSelectedGroup] = useState();
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 500);
  const { currentAccount } = useContext(AccountContext);

  const invitationsQuery = useInvitations({
    account: currentAccount?.slug,
    search: debouncedSearchTerm,
    group: selectedGroup,
    limit: pageLimit,
    offset: pageOffset,
  });
  const {
    data: groups,
    isSuccess: groupsSuccess,
    isLoading,
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
    <BasePage header="Invitations">
      <Box maxW={{ base: 'xl', md: '7xl' }} mx="auto" p="6">
        <LoadingWrapper isLoading={isLoading} showElements={groupsSuccess}>
          <Box overflowX="auto" p={1}>
            <UsersTableActions
              setSelectedGroup={setSelectedGroup}
              groups={groups}
              setSearchTerm={setSearchTermAndResetPage}
            />
            <LoadingWrapper isLoading={invitationsQuery.isLoading}>
              <InvitationsTable data={invitationsQuery.data?.results} />
              <TablePagination
                prevLink={invitationsQuery.data?.previous}
                prevHandler={prevPageHandler}
                nextLink={invitationsQuery.data?.next}
                nextHandler={nextPageHandler}
                total={invitationsQuery.data?.count}
                objectName="invitation"
              />
            </LoadingWrapper>
          </Box>
        </LoadingWrapper>
      </Box>
    </BasePage>
  );
};
