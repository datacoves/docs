import { Box } from '@chakra-ui/layout';
import React, { useContext, useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

import { BasePage } from '../../../../components/AdminLayout';
import { TablePagination } from '../../../../components/AdminLayout/components/TablePagination';
import { AccountContext } from '../../../../context/AccountContext';
import { useAllProjects } from '../../projects/api/getProjects';
import { useProfiles } from '../api/getProfiles';
import { ProfilesTable, ProfilesTableActions } from '../components';

export const Profiles = () => {
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

  const profilesQuery = useProfiles({
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
    <BasePage header="Profiles">
      <Box maxW={{ base: 'xl', md: '7xl' }} mx="auto" p="6">
        <ProfilesTableActions
          projects={projects}
          setSelectedProject={setSelectedProject}
          selectedProject={selectedProject}
          total={profilesQuery.data?.count}
        />
        <ProfilesTable data={profilesQuery.data?.results} projects={projects} />
        <TablePagination
          prevLink={profilesQuery.data?.previous}
          prevHandler={prevPageHandler}
          nextLink={profilesQuery.data?.next}
          nextHandler={nextPageHandler}
          total={profilesQuery.data?.count}
          objectName="profile"
        />
      </Box>
    </BasePage>
  );
};
