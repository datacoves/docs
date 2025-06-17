import { Box } from '@chakra-ui/layout';
import React, { useContext, useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

import { EnvironmentsTable, EnvironmentsTableActions } from '../..';
import { BasePage } from '../../../../components/AdminLayout';
import { TablePagination } from '../../../../components/AdminLayout/components/TablePagination';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { useAllProjects } from '../../projects/api/getProjects';
import { useEnvironments } from '../api/getEnvironments';

export const Environments = () => {
  const [searchParams] = useSearchParams();
  const pId = searchParams.get('projectId');

  const pageLimit = 10;
  const [pageOffset, setPageOffset] = useState(0);
  const [selectedProject, setSelectedProject] = useState<string | undefined>();
  const { currentAccount } = useContext(AccountContext);

  useEffect(() => {
    if (pId !== null) {
      setSelectedProject(pId);
    }
  }, [pId]);

  const environmentsQuery = useEnvironments({
    account: currentAccount?.slug,
    project: selectedProject,
    limit: pageLimit,
    offset: pageOffset,
  });

  const { data: projects } = useAllProjects({
    account: currentAccount?.slug,
  });
  const prevPageHandler = () => {
    setPageOffset((current) => current - pageLimit);
  };
  const nextPageHandler = () => {
    setPageOffset((current) => current + pageLimit);
  };

  return (
    <BasePage header="Environments">
      <Box maxW={{ base: 'xl', md: '7xl' }} mx="auto" p="6">
        <LoadingWrapper
          isLoading={environmentsQuery.isLoading}
          showElements={environmentsQuery.isSuccess}
        >
          <EnvironmentsTableActions
            projects={projects}
            setSelectedProject={setSelectedProject}
            selectedProject={selectedProject}
            total={environmentsQuery.data?.count}
          />
          <EnvironmentsTable data={environmentsQuery.data?.results} projects={projects} />
          <TablePagination
            prevLink={environmentsQuery.data?.previous}
            prevHandler={prevPageHandler}
            nextLink={environmentsQuery.data?.next}
            nextHandler={nextPageHandler}
            total={environmentsQuery.data?.count}
            objectName="environment"
          />
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
