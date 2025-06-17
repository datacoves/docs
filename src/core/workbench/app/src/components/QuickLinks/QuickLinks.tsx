import { Box, Text, SimpleGrid } from '@chakra-ui/react';
import { useContext } from 'react';

import { UserContext } from '../../context/UserContext';
import { Datacoves } from '../Icons/Datacoves';
import { DbtIcon } from '../Icons/Dbt';
import { GithubIcon } from '../Icons/Github';
import { GitlabIcon } from '../Icons/Gitlab';
import { SqlIcon } from '../Icons/Sql';
import { SupersetIcon } from '../Icons/Superset';

import { QuickLink } from './QuickLink';

export function QuickLinks() {
  const { currentUser } = useContext(UserContext);

  return (
    <Box bg="white" boxShadow={'md'} rounded={'md'} p={6}>
      <Text
        color={'orange.500'}
        textTransform={'uppercase'}
        fontWeight={800}
        fontSize={'sm'}
        letterSpacing={1.1}
      >
        Quick links
      </Text>
      <SimpleGrid columns={5} spacing={5} mt="5">
        <QuickLink
          title="Datacoves Docs"
          link="https://docs.datacoves.com"
          icon={<Datacoves boxSize={6} />}
        />
        <QuickLink
          title="Learn SQL"
          link="https://dataschool.com/learn-sql/"
          icon={<SqlIcon boxSize={6} />}
        />
        <QuickLink
          title="dbt Docs"
          link="https://docs.getdbt.com/"
          icon={<DbtIcon boxSize={6} />}
        />
        {currentUser && currentUser.projects.find(Boolean)?.repository.provider === 'github' && (
          <QuickLink
            title="Github Actions"
            link="https://docs.github.com/en/actions"
            icon={<GithubIcon boxSize={6} />}
          />
        )}
        {currentUser && currentUser.projects.find(Boolean)?.repository.provider === 'gitlab' && (
          <QuickLink
            title="Gitlab CI"
            link="https://docs.gitlab.com/ee/ci/"
            icon={<GitlabIcon boxSize={6} />}
          />
        )}
        {currentUser && currentUser.projects.find(Boolean)?.repository.provider === 'bitbucket' && (
          <QuickLink
            title="Bitbucket"
            link="https://bitbucket.com"
            icon={<GitlabIcon boxSize={6} />}
          />
        )}
        {currentUser &&
          currentUser.permissions.find((permission) =>
            permission.includes('workbench:superset')
          ) && (
            <QuickLink
              title="Superset Tutorial"
              link="https://superset.apache.org/docs/creating-charts-dashboards/creating-your-first-dashboard"
              icon={<SupersetIcon boxSize={6} />}
            />
          )}
      </SimpleGrid>
    </Box>
  );
}
