import {
  Avatar,
  Box,
  Flex,
  HStack,
  Menu,
  MenuItem,
  MenuList,
  Text,
  useMenuButton,
  UseMenuButtonProps,
  useColorModeValue as mode,
  Divider,
} from '@chakra-ui/react';
import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';

import { API_URL } from '../../config';
import { UserContext } from '../../context/UserContext';

const UserAvatar = () => {
  const { currentUser } = useContext(UserContext);
  return <Avatar size="sm" src={currentUser?.avatar} name={currentUser?.name || 'User Name'} />;
};

const ProfileMenuButton = (props: UseMenuButtonProps) => {
  const buttonProps = useMenuButton(props);
  return (
    <Flex
      {...buttonProps}
      as="button"
      flexShrink={0}
      rounded="full"
      outline="0"
      _focus={{ shadow: 'outline' }}
    >
      <Box srOnly>Open user menu</Box>
      <UserAvatar />
    </Flex>
  );
};

export const ProfileDropdown = () => {
  const navigate = useNavigate();
  const { currentUser } = useContext(UserContext);

  return (
    <Box>
      <Menu>
        <ProfileMenuButton />
        <MenuList rounded="md" shadow="lg" py="1" color={mode('gray.600', 'inherit')} fontSize="sm">
          <HStack px="3" py="4">
            <UserAvatar />
            <Box lineHeight="1">
              <Text fontWeight="semibold">{currentUser?.name || 'User Name'}</Text>
              <Text mt="1" fontSize="xs" color="gray.500">
                {currentUser?.email}
              </Text>
            </Box>
          </HStack>
          <Divider />
          {(currentUser?.features.user_profile_change_credentials ||
            currentUser?.features.user_profile_change_name ||
            currentUser?.features.user_profile_delete_account) && (
            <MenuItem onClick={() => navigate('/settings')} fontWeight="medium">
              Settings
            </MenuItem>
          )}
          <Divider />
          <MenuItem
            fontWeight="medium"
            color={mode('red.500', 'red.300')}
            onClick={() => (window.location = `${API_URL}/iam/logout` as any)}
          >
            Sign out
          </MenuItem>
        </MenuList>
      </Menu>
    </Box>
  );
};
