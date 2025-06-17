import {
  Button,
  ButtonGroup,
  FormControl,
  FormLabel,
  HStack,
  Input,
  InputGroup,
  InputLeftElement,
  Stack,
} from '@chakra-ui/react';
import React, { useContext } from 'react';
import { BsSearch } from 'react-icons/bs';
import { RiAddFill } from 'react-icons/ri';
import { useNavigate } from 'react-router-dom';

import { UserContext } from '../../../../context/UserContext';

export const GroupsTableActions = (props: any) => {
  const navigate = useNavigate();
  const { currentUser } = useContext(UserContext);

  return (
    <Stack spacing="4" direction={{ base: 'column', md: 'row' }} justify="space-between">
      <HStack>
        <FormControl minW={{ md: '320px' }} id="search">
          <InputGroup size="sm">
            <FormLabel srOnly>Search by name</FormLabel>
            <InputLeftElement pointerEvents="none" color="gray.400">
              <BsSearch />
            </InputLeftElement>
            <Input
              rounded="base"
              type="search"
              placeholder="Search by name..."
              onChange={(e) => props.setSearchTerm(e.target.value)}
            />
          </InputGroup>
        </FormControl>
      </HStack>
      {currentUser?.features.admin_create_groups && (
        <ButtonGroup size="sm" variant="solid" colorScheme="blue">
          <Button
            iconSpacing="1"
            leftIcon={<RiAddFill fontSize="1.25em" />}
            onClick={() => navigate('/admin/groups/create')}
          >
            New Group
          </Button>
        </ButtonGroup>
      )}
    </Stack>
  );
};
