import {
  ButtonGroup,
  FormControl,
  FormLabel,
  HStack,
  Input,
  InputGroup,
  InputLeftElement,
  Stack,
} from '@chakra-ui/react';
import { BsSearch } from 'react-icons/bs';

import { ModalAddPermission } from './ModalAddPermission';

export const PermissionsGroupTableActions = () => {
  return (
    <Stack spacing="4" direction={{ base: 'column', md: 'row' }} justify="space-between">
      <HStack>
        <FormControl minW={{ md: '320px' }} id="search">
          <InputGroup size="sm">
            <FormLabel srOnly>Search by name</FormLabel>
            <InputLeftElement pointerEvents="none" color="gray.400">
              <BsSearch />
            </InputLeftElement>
            <Input rounded="base" type="search" placeholder="Search..." />
          </InputGroup>
        </FormControl>
      </HStack>
      <ButtonGroup size="sm" variant="outline">
        <ModalAddPermission />
      </ButtonGroup>
    </Stack>
  );
};
