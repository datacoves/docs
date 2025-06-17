import { ButtonGroup, HStack, Stack, Select, Button } from '@chakra-ui/react';
import React from 'react';
import { RiAddFill } from 'react-icons/ri';
import { useNavigate } from 'react-router-dom';

import { Environment } from '../../../../context/UserContext/types';

export const ServiceCredentialsTableActions = (props: any) => {
  const navigate = useNavigate();
  const handleChange = (event: any) => {
    props.setSelectedEnvironment(event.target.value);
  };

  return (
    <Stack spacing="4" direction={{ base: 'column', md: 'row' }} justify="space-between">
      <HStack>
        <Select
          w={{ base: '300px' }}
          rounded="base"
          size="sm"
          onChange={handleChange}
          value={props.selectedEnvironment}
        >
          <option value="">All Environments</option>
          {props.environments?.map((environment: Environment) => (
            <option key={`environment-${environment.id}`} value={environment.id.toString()}>
              {environment.name} ({environment.slug})
            </option>
          ))}
        </Select>
      </HStack>
      <ButtonGroup size="sm" variant="solid" colorScheme="blue">
        <Button
          iconSpacing="1"
          leftIcon={<RiAddFill fontSize="1.25em" />}
          onClick={() => navigate('/admin/service-connections/create')}
        >
          New Connection
        </Button>
      </ButtonGroup>
    </Stack>
  );
};
