import { Box } from '@chakra-ui/layout';
import React, { useContext, useState } from 'react';

import { BasePage } from '../../../../components/AdminLayout';
import { TablePagination } from '../../../../components/AdminLayout/components/TablePagination';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { useDebounce } from '../../../../hooks/useDebounce';
import { useIntegrations } from '../api/getIntegrations';
import { IntegrationsTable, IntegrationsTableActions } from '../components';

export const Integrations = () => {
  const pageLimit = 10;
  const [pageOffset, setPageOffset] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 500);
  const { currentAccount } = useContext(AccountContext);

  const integrationsQuery = useIntegrations({
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
    <BasePage header="Integrations">
      <Box maxW={{ base: 'xl', md: '7xl' }} mx="auto" p="6">
        <IntegrationsTableActions setSearchTerm={setSearchTermAndResetPage} />
        <LoadingWrapper
          isLoading={integrationsQuery.isLoading}
          showElements={integrationsQuery.isSuccess}
        >
          <IntegrationsTable data={integrationsQuery.data?.results} />
          <TablePagination
            prevLink={integrationsQuery.data?.previous}
            prevHandler={prevPageHandler}
            nextLink={integrationsQuery.data?.next}
            nextHandler={nextPageHandler}
            total={integrationsQuery.data?.count}
            objectName="integration"
          />
        </LoadingWrapper>
      </Box>
    </BasePage>
  );
};
