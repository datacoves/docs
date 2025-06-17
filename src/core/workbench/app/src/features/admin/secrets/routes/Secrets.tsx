import { Box } from '@chakra-ui/layout';
import React, { useContext, useState } from 'react';

import { BasePage } from '../../../../components/AdminLayout';
import { TablePagination } from '../../../../components/AdminLayout/components/TablePagination';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { useDebounce } from '../../../../hooks/useDebounce';
import { useAllEnvironments } from '../../environments/api/getEnvironments';
import { useAllProjects } from '../../projects/api/getProjects';
import { useSecrets } from '../api/getSecrets';
import { SecretsTable, SecretsTableActions } from '../components';

export const Secrets = () => {
  const pageLimit = 10;
  const [pageOffset, setPageOffset] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 500);
  const { currentAccount } = useContext(AccountContext);

  const {
    data: projects,
    isLoading: isLoadingProjects,
    isSuccess: isProjectsSuccess,
  } = useAllProjects({
    account: currentAccount?.slug,
  });

  const {
    data: environments,
    isSuccess: isEnvironmentsSuccess,
    isLoading: isLoadingEnvs,
  } = useAllEnvironments({
    account: currentAccount?.slug,
  });

  const secretsQuery = useSecrets({
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
    <BasePage header="Secrets">
      <Box maxW={{ base: 'xl', md: '7xl' }} mx="auto" p="6">
        <LoadingWrapper
          isLoading={isLoadingProjects || isLoadingEnvs}
          showElements={isProjectsSuccess && isEnvironmentsSuccess}
        >
          <SecretsTableActions projects={projects} setSearchTerm={setSearchTermAndResetPage} />
          <LoadingWrapper isLoading={secretsQuery.isLoading}>
            <SecretsTable
              data={secretsQuery.data?.results}
              projects={projects}
              environments={environments}
            />
            <TablePagination
              prevLink={secretsQuery.data?.previous}
              prevHandler={prevPageHandler}
              nextLink={secretsQuery.data?.next}
              nextHandler={nextPageHandler}
              total={secretsQuery.data?.count}
              objectName="secret"
            />
          </LoadingWrapper>
        </LoadingWrapper>
      </Box>
      <style>{`
        main div.chakra-container {
          display: table;
        }
      `}</style>
    </BasePage>
  );
};
