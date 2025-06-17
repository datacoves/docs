import { ButtonGroup, HStack, Stack, Select, Button, Tooltip } from '@chakra-ui/react';
import React, { useContext } from 'react';
import { RiAddFill } from 'react-icons/ri';
import { useNavigate } from 'react-router-dom';

import { AccountContext } from '../../../../context/AccountContext';

export const EnvironmentsTableActions = (props: any) => {
  const { currentAccount } = useContext(AccountContext);
  const navigate = useNavigate();
  const handleChange = (event: any) => {
    props.setSelectedProject(event.target.value);
  };
  const createDisabled = currentAccount?.plan?.kind === 'starter' && props.total >= 1;

  return (
    <Stack spacing="4" direction={{ base: 'column', md: 'row' }} justify="space-between">
      <HStack>
        <Select
          w={{ base: '300px' }}
          rounded="base"
          size="sm"
          onChange={handleChange}
          value={props.selectedProject}
        >
          <option value="">All projects</option>
          {props.projects?.map((project: any) => (
            <option key={`project-${project.id}`} value={project.id.toString()}>
              {project.name}
            </option>
          ))}
        </Select>
      </HStack>
      <Tooltip
        label={
          createDisabled
            ? 'No more than 1 environment can be created on Starter plans'
            : 'Create a new environment'
        }
        hasArrow
      >
        <ButtonGroup size="sm" variant="solid" colorScheme="blue">
          <Button
            iconSpacing="1"
            leftIcon={<RiAddFill fontSize="1.25em" />}
            onClick={() => navigate('/admin/environments/create')}
            isDisabled={createDisabled}
          >
            New Environment
          </Button>
        </ButtonGroup>
      </Tooltip>
    </Stack>
  );
};
