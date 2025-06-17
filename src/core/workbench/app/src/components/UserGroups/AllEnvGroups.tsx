import { Heading, SimpleGrid } from '@chakra-ui/react';

import { Group } from '../../features/admin/groups/types';

import { GroupCheckboxItem } from './CheckboxItem';
import { ProjectGroupType } from './utils';

interface Props {
  projectsGroup: ProjectGroupType;
  projectKey: string;
}

const AllEnvGroups = ({ projectsGroup, projectKey }: Props) => {
  const { permissions: projects } = projectsGroup[projectKey];

  return (
    <>
      <Heading size="sm" pt={4} pb={2}>
        {'All environments'}
      </Heading>
      <SimpleGrid columns={3} spacing={8} gridAutoFlow="dense">
        {projects.map((group: Group) => (
          <GroupCheckboxItem group={group} key={group.id} />
        ))}
      </SimpleGrid>
    </>
  );
};

export default AllEnvGroups;
