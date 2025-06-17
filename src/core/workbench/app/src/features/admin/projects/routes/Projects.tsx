import { Box } from '@chakra-ui/react';
import React, { useContext, useState } from 'react';

import { ProjectsTableActions, ProjectsTable } from '../..';
import { BasePage } from '../../../../components/AdminLayout';
import { TablePagination } from '../../../../components/AdminLayout/components/TablePagination';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { useDebounce } from '../../../../hooks/useDebounce';
import { useProjects } from '../api/getProjects';

export const Projects = () => {
  const pageLimit = 10;
  const [pageOffset, setPageOffset] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 500);
  const { currentAccount } = useContext(AccountContext);

  const projectsQuery = useProjects({
    account: currentAccount?.slug,
    search: debouncedSearchTerm,
    limit: pageLimit,
    offset: pageOffset,
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
    <BasePage header="Projects">
      <Box maxW={{ base: 'xl', md: '7xl' }} mx="auto" p="6">
        <Box>
          <ProjectsTableActions
            setSearchTerm={setSearchTermAndResetPage}
            total={projectsQuery.data?.count}
          />
          <LoadingWrapper
            isLoading={projectsQuery.isLoading}
            showElements={projectsQuery.isSuccess}
          >
            <ProjectsTable data={projectsQuery.data?.results} />
            <TablePagination
              prevLink={projectsQuery.data?.previous}
              prevHandler={prevPageHandler}
              nextLink={projectsQuery.data?.next}
              nextHandler={nextPageHandler}
              total={projectsQuery.data?.count}
              objectName="project"
            />
          </LoadingWrapper>
        </Box>
      </Box>
      <style>{`
        main div.chakra-container {
          display: table;
        }
      `}</style>
    </BasePage>
  );
};
