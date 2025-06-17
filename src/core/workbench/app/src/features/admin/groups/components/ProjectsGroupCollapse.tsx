import { ChevronDownIcon, ChevronUpIcon } from '@chakra-ui/icons';
import { Tr, Td, Box } from '@chakra-ui/react';
import { Fragment, useState } from 'react';

import { Group } from '../types';

import { EnvGroupCollapse } from './EnvGroupCollapse';

interface Props {
  columns: {
    header: string;
    cell: (data: Group) => JSX.Element;
  }[];
  projectsGroup: { permissions: Group[]; environments: { [key: string]: Group[] } };
}

export const ProjectsGroupCollapse = ({ columns, projectsGroup }: Props) => {
  const [showProject, setShowProject] = useState(false);
  const [showEnvs, setShowEnvs] = useState(false);
  return (
    <>
      <Fragment>
        {!!projectsGroup.permissions.length && (
          <Tr onClick={() => setShowProject((prev) => !prev)} cursor="pointer">
            <Td fontWeight="bold" pl={10} colSpan={4}>
              {projectsGroup.permissions[0].extended_group.project?.name} Project
              {showProject ? <ChevronUpIcon /> : <ChevronDownIcon />}
            </Td>
          </Tr>
        )}

        {showProject && (
          <>
            {projectsGroup.permissions.map((projectGroup) => {
              return (
                <Tr key={projectGroup.id}>
                  {columns.map((column, index) => (
                    <Td whiteSpace="nowrap" key={index} pl={index === 0 ? 14 : 6}>
                      <Box as="span" flex="1" textAlign="left">
                        {column.cell?.(projectGroup)}
                      </Box>
                    </Td>
                  ))}
                </Tr>
              );
            })}
            {!!Object.keys(projectsGroup.environments).length && (
              <Tr
                onClick={() => setShowEnvs((prev) => !prev)}
                fontWeight="bold"
                fontSize="sm"
                w="full"
                cursor="pointer"
              >
                <Td pl={14} colSpan={4}>
                  Environment Groups
                  {showEnvs ? <ChevronUpIcon /> : <ChevronDownIcon />}
                </Td>
              </Tr>
            )}
            {showEnvs &&
              Object.keys(projectsGroup.environments).map((env) => (
                <EnvGroupCollapse
                  key={env}
                  env={env}
                  columns={columns}
                  environmentGroups={projectsGroup.environments[env]}
                />
              ))}
          </>
        )}
      </Fragment>
    </>
  );
};
