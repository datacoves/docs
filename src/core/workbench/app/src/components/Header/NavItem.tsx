import { ChevronDownIcon } from '@chakra-ui/icons';
import {
  Box,
  HStack,
  ListItem,
  Menu,
  Tooltip,
  UnorderedList,
  useMenuButton,
  UseMenuButtonProps,
} from '@chakra-ui/react';
import { css } from '@emotion/react';
import * as React from 'react';
import { useState } from 'react';

import { openLink } from '../../utils/link';
interface NavItemProps {
  href?: string;
  active?: boolean;
  label: string;
  onClick: (ev: any) => void;
  dark?: boolean;
  menuList?: React.ReactNode;
  isEnabled?: boolean;
  unmetConditions?: Array<string>;
}

interface TabMenuProps extends UseMenuButtonProps {
  icon?: React.ReactNode;
  label: string;
}

const TabMenuButton = (props: TabMenuProps) => {
  const { icon, label } = props;
  const buttonProps = useMenuButton(props);
  return (
    <HStack {...buttonProps} as="button" role="group" spacing="0">
      {icon && (
        <Box aria-hidden fontSize="md" display="block" mr="1">
          {icon}
        </Box>
      )}
      <Box fontWeight="semibold">{label}</Box>
      <Box aria-hidden fontSize="md" display="block" mr="1">
        <ChevronDownIcon />
      </Box>
    </HStack>
  );
};

interface DesktopNavItemProps extends NavItemProps {
  icon?: React.ReactNode;
}

const DesktopNavItem = (props: DesktopNavItemProps) => {
  const {
    icon,
    label,
    href = null,
    active,
    onClick,
    dark,
    menuList,
    isEnabled = true,
    unmetConditions = [],
  } = props;
  const menu = menuList !== undefined;

  const handleClick = (event: any) => {
    const isCommandOrCtrlPressed = event.metaKey || event.ctrlKey;

    if (isCommandOrCtrlPressed) {
      // Prevent the default behavior (e.g., opening the link)
      event.preventDefault();

      if (href) {
        openLink(href);
      }
    } else {
      onClick(event);
    }
  };
  const [hoveredMenu, setHoveredMenu] = useState<string | null>(null);
  const [isHovered, setIsHovered] = useState(false);
  const handleMouseEnter = (label: string) => {
    setHoveredMenu(label);
    setIsHovered(true);
  };
  const handleMouseLeave = () => {
    setHoveredMenu(null);
    setIsHovered(false);
  };
  const customFocusStyle = css`
    &:focus-visible {
      outline: none; /* Overwrite the default outline */
    }
  `;
  const content = (
    <HStack
      as="a"
      aria-current={active || isHovered ? 'page' : undefined}
      px="3"
      py="1"
      spacing="0"
      rounded="md"
      transition="all 0.2s"
      color="white"
      _hover={{ bg: dark ? 'whiteAlpha.300' : 'whiteAlpha.200' }}
      _activeLink={{
        bg: dark ? 'whiteAlpha.500' : 'blackAlpha.300',
        color: 'white',
      }}
      opacity={isEnabled ? 1 : 0.5}
      onClick={handleClick}
      cursor={isEnabled ? 'pointer' : 'not-allowed'}
      onMouseEnter={() => handleMouseEnter(label)}
      onMouseLeave={handleMouseLeave}
      border={isHovered ? 'none' : undefined}
      css={customFocusStyle}
    >
      {menu && (
        <Menu isOpen={hoveredMenu === label}>
          <TabMenuButton icon={icon} label={label} />
          {menuList}
        </Menu>
      )}
      {!menu && icon && (
        <Box aria-hidden fontSize="md" mr="1">
          {icon}
        </Box>
      )}
      {!menu && <Box fontWeight="semibold">{label}</Box>}
    </HStack>
  );

  const tooltipContent = (
    <>
      <UnorderedList>
        {unmetConditions.map((condition, index) => (
          <ListItem key={index}>{condition}</ListItem>
        ))}
      </UnorderedList>
    </>
  );

  return !isEnabled ? <Tooltip label={tooltipContent}>{content}</Tooltip> : <>{content}</>;
};

const MobileNavItem = (props: NavItemProps) => {
  const { label, active, onClick, dark } = props;
  return (
    <Box
      as="a"
      display="block"
      px="3"
      py="3"
      rounded="md"
      fontWeight="semibold"
      aria-current={active ? 'page' : undefined}
      _hover={{ bg: dark ? 'whiteAlpha.400' : 'whiteAlpha.200' }}
      _activeLink={{
        bg: dark ? 'whiteAlpha.300' : 'blackAlpha.300',
        color: 'white',
      }}
      onClick={onClick}
    >
      {label}
    </Box>
  );
};

export const NavItem = {
  Desktop: DesktopNavItem,
  Mobile: MobileNavItem,
};
