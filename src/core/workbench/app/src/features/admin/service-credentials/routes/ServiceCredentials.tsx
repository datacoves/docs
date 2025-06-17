import { Box } from '@chakra-ui/layout';
import React, { useContext, useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

import { BasePage } from '../../../../components/AdminLayout';
import { TablePagination } from '../../../../components/AdminLayout/components/TablePagination';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { useAllEnvironments } from '../../environments/api/getEnvironments';
import { useServiceCredentials } from '../api/getServiceCredentials';
import { ServiceCredentialsTable, ServiceCredentialsTableActions } from '../components';

export const ServiceCredentials = () => {
  const [searchParams] = useSearchParams();
  const envId = searchParams.get('environmentId');

  const pageLimit = 10;
  const [pageOffset, setPageOffset] = useState(0);
  const [selectedEnvironment, setSelectedEnvironment] = useState<string | undefined>();
  const { currentAccount } = useContext(AccountContext);

  useEffect(() => {
    if (envId !== null) {
      setSelectedEnvironment(envId);
    }
  }, [envId]);

  const serviceCredentialsQuery = useServiceCredentials({
    account: currentAccount?.slug,
    environment: selectedEnvironment,
    limit: pageLimit,
    offset: pageOffset,
  });

  const {
    data: environments,
    isLoading: isLoadingEnvs,
    isSuccess: isEnvsSuccess,
  } = useAllEnvironments({
    account: currentAccount?.slug,
  });
  const prevPageHandler = () => {
    setPageOffset((current) => current - pageLimit);
  };
  const nextPageHandler = () => {
    setPageOffset((current) => current + pageLimit);
  };

  return (
    <BasePage header="Service connections">
      <Box maxW={{ base: 'xl', md: '7xl' }} mx="auto" p="6">
        <LoadingWrapper
          isLoading={isLoadingEnvs || serviceCredentialsQuery.isLoading}
          showElements={isEnvsSuccess && serviceCredentialsQuery.isSuccess}
        >
          <ServiceCredentialsTableActions
            environments={environments}
            setSelectedEnvironment={setSelectedEnvironment}
            selectedEnvironment={selectedEnvironment}
          />
          <ServiceCredentialsTable
            data={serviceCredentialsQuery.data?.results}
            environments={environments}
          />
          <TablePagination
            prevLink={serviceCredentialsQuery.data?.previous}
            prevHandler={prevPageHandler}
            nextLink={serviceCredentialsQuery.data?.next}
            nextHandler={nextPageHandler}
            total={serviceCredentialsQuery.data?.count}
            objectName="service connection"
          />
        </LoadingWrapper>
      </Box>
    </BasePage>
  );
};
