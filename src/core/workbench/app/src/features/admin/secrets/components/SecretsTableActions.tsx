import {
  ButtonGroup,
  Stack,
  Button,
  HStack,
  FormControl,
  InputGroup,
  FormLabel,
  InputLeftElement,
  Input,
} from '@chakra-ui/react';
import React from 'react';
import { BsSearch } from 'react-icons/bs';
import { RiAddFill } from 'react-icons/ri';
import { useNavigate } from 'react-router-dom';

export const SecretsTableActions = (props: any) => {
  const navigate = useNavigate();

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
      <ButtonGroup size="sm" variant="solid" colorScheme="blue">
        <Button
          iconSpacing="1"
          leftIcon={<RiAddFill fontSize="1.25em" />}
          onClick={() => navigate('/admin/secrets/create')}
        >
          New Secret
        </Button>
      </ButtonGroup>
    </Stack>
  );
};
