import { Box } from '@chakra-ui/layout';
import React, { useContext, useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

import { BasePage } from '../../../../components/AdminLayout';
import { TablePagination } from '../../../../components/AdminLayout/components/TablePagination';
import { LoadingWrapper } from '../../../../components/LoadingWrapper';
import { AccountContext } from '../../../../context/AccountContext';
import { useAllProjects } from '../../projects/api/getProjects';
import { useConnectionTemplates } from '../api/getConnectionTemplates';
import { ConnectionTemplatesTable, ConnectionTemplatesTableActions } from '../components';

export const ConnectionTemplates = () => {
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

  const connectionsQuery = useConnectionTemplates({
    account: currentAccount?.slug,
    project: selectedProject,
    limit: pageLimit,
    offset: pageOffset,
  });

  const {
    data: projects,
    isLoading: isLoadingProjects,
    isSuccess: isProjectsSuccess,
  } = useAllProjects({
    account: currentAccount?.slug,
  });
  const prevPageHandler = () => {
    setPageOffset((current) => current - pageLimit);
  };
  const nextPageHandler = () => {
    setPageOffset((current) => current + pageLimit);
  };

  return (
    <BasePage header="Connection Templates">
      <Box maxW={{ base: 'xl', md: '7xl' }} mx="auto" p="6">
        <LoadingWrapper
          isLoading={isLoadingProjects || connectionsQuery.isLoading}
          showElements={isProjectsSuccess && connectionsQuery.isSuccess}
        >
          <ConnectionTemplatesTableActions
            projects={projects}
            setSelectedProject={setSelectedProject}
            selectedProject={selectedProject}
          />
          <ConnectionTemplatesTable data={connectionsQuery.data?.results} projects={projects} />
          <TablePagination
            prevLink={connectionsQuery.data?.previous}
            prevHandler={prevPageHandler}
            nextLink={connectionsQuery.data?.next}
            nextHandler={nextPageHandler}
            total={connectionsQuery.data?.count}
            objectName="connection template"
          />
        </LoadingWrapper>
      </Box>
    </BasePage>
  );
};
