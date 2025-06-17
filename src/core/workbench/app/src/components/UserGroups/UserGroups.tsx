import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Heading,
  SimpleGrid,
} from '@chakra-ui/react';
import React from 'react';

import { Group } from '../../features/admin/groups/types';

import AllEnvGroups from './AllEnvGroups';
import { GroupCheckboxItem } from './CheckboxItem';
import SingleEnvGroups from './SingleEnvGroups';
import { GroupFormValues, ProjectGroupType } from './utils';

interface Props {
  projectsGroup: ProjectGroupType;
  accountGroup: Group[] | undefined;
  values: GroupFormValues;
  accountName: string | undefined;
}

export const UserGroups = ({ projectsGroup, accountGroup, values, accountName }: Props) => {
  return (
    <Box width="full">
      <Heading size="md" as="span" flex="1" textAlign="left">
        {`${accountName} Account`}
      </Heading>
      <SimpleGrid columns={3} spacing={8} pb={5} gridAutoFlow="dense">
        {accountGroup?.map((group: Group) => (
          <GroupCheckboxItem group={group} key={group.id} />
        ))}
      </SimpleGrid>

      <Accordion allowToggle>
        {Object.keys(projectsGroup).map((project) => {
          return (
            <AccordionItem key={project}>
              <h2>
                <AccordionButton>
                  <Heading size="sm" as="span" flex="1" textAlign="left">
                    {`${project} Project`}
                  </Heading>
                  <AccordionIcon />
                </AccordionButton>
              </h2>
              <AccordionPanel pb={4}>
                <AllEnvGroups projectsGroup={projectsGroup} projectKey={project} />
                <SingleEnvGroups
                  projectsGroup={projectsGroup}
                  projectKey={project}
                  values={values}
                />
              </AccordionPanel>
            </AccordionItem>
          );
        })}
      </Accordion>
    </Box>
  );
};

export default UserGroups;
