import { Button, VStack, Text } from '@chakra-ui/react';
import React, { useContext, useState } from 'react';

import { AzureDevopsIcon } from '../../../../components/Icons/AzureDevops';
import { BitbucketIcon } from '../../../../components/Icons/Bitbucket';
import { DataHubIcon } from '../../../../components/Icons/DataHub';
import { DocsIcon } from '../../../../components/Icons/Docs';
import { GithubIcon } from '../../../../components/Icons/Github';
import { GitlabIcon } from '../../../../components/Icons/Gitlab';
import { WorkbenchTab } from '../../../../components/WorkbenchTab';
import { ObserveSubTabsContext } from '../../../../context/ObserveSubTabsContext';
import { TabsContext } from '../../../../context/TabsContext';
import { UserContext } from '../../../../context/UserContext';
import { getSiteContext } from '../../../../utils/siteContext';

export function ObserveTab({ isLoading }: { isLoading: boolean }) {
  const { currentTab } = useContext(TabsContext);
  const { currentSubTab, setCurrentSubTab } = useContext(ObserveSubTabsContext);
  const { currentUser } = useContext(UserContext);
  const site = getSiteContext();

  const localDocsUrl = currentUser
    ? `https://${currentUser.slug}-dbt-docs-${site.host}`
    : undefined;
  const prodDocsUrl = currentUser ? `https://dbt-docs-${site.host}` : undefined;
  const datahubUrl = currentUser ? `https://datahub-${site.host}` : undefined;

  const proj = currentUser?.projects.find((project) =>
    project.environments.find((environment) => environment.slug === site.env)
  );
  const env = proj?.environments.find((environment) => environment.slug === site.env);
  const ciCdUrl = proj?.ci_home_url;

  const hasLocalDbtDocs =
    currentUser &&
    localDocsUrl &&
    currentUser.projects &&
    env &&
    env.services['local-dbt-docs'].enabled &&
    env.services['local-dbt-docs'].valid &&
    currentUser.has_license &&
    currentUser?.permissions.find((permission) => permission.includes('workbench:local-dbt-docs'));

  const hasProdDbtDocs =
    prodDocsUrl &&
    currentUser &&
    env &&
    env.services['dbt-docs'].enabled &&
    env.services['dbt-docs'].valid &&
    currentUser?.permissions.find((permission) => permission.includes('workbench:dbt-docs'));

  const hasDataHub =
    datahubUrl &&
    currentUser &&
    env &&
    env.services['datahub'].enabled &&
    env.services['datahub'].valid &&
    currentUser?.permissions.find((permission) => permission.includes('workbench:datahub'));

  const defaultUrl = () => {
    if (hasLocalDbtDocs) {
      return localDocsUrl;
    } else if (hasProdDbtDocs) {
      return prodDocsUrl;
    } else if (hasDataHub) {
      return datahubUrl;
    } else {
      return undefined;
    }
  };
  const subTabUrl = () => {
    if (currentSubTab === 'local-dbt-docs') {
      return localDocsUrl;
    } else if (currentSubTab === 'dbt-docs') {
      return prodDocsUrl;
    } else if (currentSubTab === 'datahub') {
      return datahubUrl;
    } else {
      return undefined;
    }
  };

  const useForceUpdate = () => useState()[1];

  const forceUpdate = useForceUpdate();

  const bg = currentTab === 'docs' ? 'blue.500' : `${currentTab}.header`;

  function cicd() {
    if (currentUser) {
      const newWindow = window.open(ciCdUrl, '_blank', 'noopener,noreferrer');
      if (newWindow) newWindow.opener = null;
    }
  }

  return (
    <WorkbenchTab
      name="observe"
      isLoading={isLoading}
      url={subTabUrl() || defaultUrl()}
      sidebar={
        <VStack float="left" p={2} bg={bg} h="calc(100vh - 48px)" w={95} alignItems="stretch">
          {hasLocalDbtDocs && (
            <Button
              flexDirection="column"
              isActive={currentSubTab === 'local-dbt-docs'}
              onClick={() => {
                setCurrentSubTab('local-dbt-docs');
                forceUpdate;
              }}
              bg="transparent"
              colorScheme="blue"
              p={3}
              h="auto"
            >
              <DocsIcon boxSize={6} />
              <Text fontSize="xs" mt={1}>
                Local Docs
              </Text>
            </Button>
          )}
          {hasProdDbtDocs && (
            <Button
              flexDirection="column"
              isActive={currentSubTab === 'dbt-docs'}
              onClick={() => setCurrentSubTab('dbt-docs')}
              bg="transparent"
              colorScheme="blue"
              p={3}
              h="auto"
            >
              <DocsIcon boxSize={6} />
              <Text fontSize="xs" mt={1}>
                Docs
              </Text>
            </Button>
          )}
          {hasDataHub && (
            <Button
              flexDirection="column"
              isActive={currentSubTab === 'datahub'}
              onClick={() => setCurrentSubTab('datahub')}
              bg="transparent"
              colorScheme="blue"
              p={3}
              h="auto"
            >
              <DataHubIcon boxSize={6} />
              <Text fontSize="xs" mt={1}>
                DataHub
              </Text>
            </Button>
          )}
          {ciCdUrl && (
            <Button
              flexDirection="column"
              onClick={cicd}
              bg="transparent"
              color="white"
              _hover={{ bg: 'blue.400' }}
              p={3}
              h="auto"
            >
              {currentUser && proj?.ci_provider === 'github' && <GithubIcon boxSize={6} />}
              {currentUser && proj?.ci_provider === 'gitlab' && <GitlabIcon boxSize={6} />}
              {currentUser && proj?.ci_provider === 'bitbucket' && <BitbucketIcon boxSize={6} />}
              {currentUser && proj?.ci_provider === 'azure_devops' && (
                <AzureDevopsIcon boxSize={6} />
              )}
              <Text fontSize="xs" mt={1}>
                CI/CD
              </Text>
            </Button>
          )}
        </VStack>
      }
    />
  );
}
