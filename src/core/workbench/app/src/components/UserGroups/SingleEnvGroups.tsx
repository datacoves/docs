import { Box, Heading, SimpleGrid } from '@chakra-ui/layout';

import { Group } from '../../features/admin/groups/types';

import { GroupCheckboxItem } from './CheckboxItem';
import { GroupFormValues, labelGroup, ProjectGroupType } from './utils';

interface Props {
  projectsGroup: ProjectGroupType;
  projectKey: string;
  values: GroupFormValues;
}

const SingleEnvGroups = ({ projectsGroup, projectKey, values }: Props) => {
  const { environments: projectEnvs, permissions: projects } = projectsGroup[projectKey];

  const selectedProjectGroups = projects
    .filter(({ id }) => values.groups.includes(id.toString()))
    .map((group) => labelGroup(group.extended_group.name));

  const isProjectGroupSelected = (group: Group) =>
    selectedProjectGroups.includes(labelGroup(group.extended_group.name));

  return (
    <>
      {Object.keys(projectEnvs)?.map((key) => {
        return (
          <Box key={key} pl={4}>
            <Heading size="sm" pt={6} pb={2}>
              {`Only ${key}`}
            </Heading>
            <SimpleGrid columns={3} spacing={8} gridAutoFlow="dense">
              {projectEnvs[key].map((group: Group) => (
                <GroupCheckboxItem
                  group={group}
                  key={group.id}
                  isDisabled={isProjectGroupSelected(group)}
                />
              ))}
            </SimpleGrid>
          </Box>
        );
      })}
    </>
  );
};

export default SingleEnvGroups;
