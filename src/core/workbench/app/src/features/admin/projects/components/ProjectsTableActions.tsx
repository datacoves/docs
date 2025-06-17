import {
  Button,
  ButtonGroup,
  FormControl,
  FormLabel,
  HStack,
  Input,
  InputGroup,
  Tooltip,
  InputLeftElement,
  Stack,
} from '@chakra-ui/react';
import React, { useContext } from 'react';
import { BsSearch } from 'react-icons/bs';
import { RiAddFill } from 'react-icons/ri';
import { useNavigate } from 'react-router-dom';

import { AccountContext } from '../../../../context/AccountContext';

export const ProjectsTableActions = (props: any) => {
  const { currentAccount } = useContext(AccountContext);
  const navigate = useNavigate();
  const createDisabled = currentAccount?.plan?.kind === 'starter' && props.total >= 1;
  return (
    <Stack spacing="4" direction={{ base: 'column', md: 'row' }} justify="space-between">
      <HStack>
        <FormControl minW={{ md: '320px' }} id="search">
          <InputGroup size="sm">
            <FormLabel srOnly>Filter by name</FormLabel>
            <InputLeftElement pointerEvents="none" color="gray.400">
              <BsSearch />
            </InputLeftElement>
            <Input
              rounded="base"
              type="search"
              placeholder="Filter by name..."
              onChange={(e) => props.setSearchTerm(e.target.value)}
            />
          </InputGroup>
        </FormControl>
      </HStack>
      <Tooltip
        label={
          createDisabled
            ? 'No more than 1 project can be created on Starter plans'
            : 'Create a new project'
        }
        hasArrow
      >
        <ButtonGroup size="sm" variant="solid" colorScheme="blue">
          <Button
            iconSpacing="1"
            leftIcon={<RiAddFill fontSize="1.25em" />}
            m={1}
            onClick={() => navigate('/admin/projects/create')}
            isDisabled={createDisabled}
          >
            New Project
          </Button>
        </ButtonGroup>
      </Tooltip>
    </Stack>
  );
};
