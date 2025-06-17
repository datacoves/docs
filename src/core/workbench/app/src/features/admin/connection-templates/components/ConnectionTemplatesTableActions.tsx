import { ButtonGroup, HStack, Stack, Select, Button } from '@chakra-ui/react';
import React from 'react';
import { RiAddFill } from 'react-icons/ri';
import { useNavigate } from 'react-router-dom';

export const ConnectionTemplatesTableActions = (props: any) => {
  const navigate = useNavigate();
  const handleChange = (event: any) => {
    props.setSelectedProject(event.target.value);
  };

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
      <ButtonGroup size="sm" variant="solid" colorScheme="blue">
        <Button
          iconSpacing="1"
          leftIcon={<RiAddFill fontSize="1.25em" />}
          onClick={() => navigate('/admin/connection-templates/create')}
        >
          New Connection Template
        </Button>
      </ButtonGroup>
    </Stack>
  );
};
