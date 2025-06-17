import { Box, HStack, Stack, Text, useColorModeValue as mode } from '@chakra-ui/react';
import { CheckboxControl } from 'formik-chakra-ui';
import { Fragment } from 'react';

import { Permission } from '../types';

import { CheckboxBox } from './CheckboxBox';

interface Props {
  permission: Permission[];
  disabled: boolean;
}

const PermissionCheckbox = ({ permission, disabled }: Props) => (
  <Stack alignItems="flex-start" spacing="4" w="full">
    <CheckboxBox w="full">
      <HStack spacing="0">
        <Box flex="1">
          <Text textTransform="capitalize">{permission[0].resource.replaceAll(':', ' > ')}</Text>
        </Box>
        {permission.map((perm) => (
          <Fragment key={perm.id}>
            <CheckboxControl
              value={perm.id.toString()}
              name="permissions"
              isDisabled={disabled}
              pl={8}
            />
            <Box fontWeight="bold" color={mode('blue.600', 'blue.400')} marginInlineStart={0}>
              {perm.action}
            </Box>
          </Fragment>
        ))}
      </HStack>
    </CheckboxBox>
  </Stack>
);

export default PermissionCheckbox;
