import {
  Button,
  ButtonGroup,
  FormControl,
  FormLabel,
  HStack,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Stack,
} from '@chakra-ui/react';
import * as React from 'react';
import { BsSearch } from 'react-icons/bs';
import { RiAddFill } from 'react-icons/ri';
import { useNavigate } from 'react-router-dom';

export const UsersTableActions = (props: any) => {
  const navigate = useNavigate();

  const handleChange = (event: any) => {
    props.setSelectedGroup(event.target.value);
  };

  return (
    <Stack spacing="4" direction={{ base: 'column', md: 'row' }} justify="space-between">
      <HStack>
        <FormControl minW={{ md: '300px' }} id="search">
          <InputGroup size="sm">
            <FormLabel srOnly>Filter by name or email</FormLabel>
            <InputLeftElement pointerEvents="none" color="gray.400">
              <BsSearch />
            </InputLeftElement>
            <Input
              rounded="base"
              type="search"
              placeholder="Filter by name or email..."
              onChange={(e) => props.setSearchTerm(e.target.value)}
            />
          </InputGroup>
        </FormControl>
        <Select w={{ base: '300px' }} rounded="base" size="sm" onChange={handleChange}>
          <option value="">All groups</option>
          {props.groups.map((group: any) => (
            <option key={`group-${group.id}`} value={group.id.toString()}>
              {group.name}
            </option>
          ))}
        </Select>
      </HStack>
      <ButtonGroup size="sm" variant="solid" colorScheme="blue">
        <Button
          iconSpacing="1"
          leftIcon={<RiAddFill fontSize="1.25em" />}
          onClick={() => navigate('/admin/invitations/create')}
        >
          Invite User
        </Button>
      </ButtonGroup>
    </Stack>
  );
};
