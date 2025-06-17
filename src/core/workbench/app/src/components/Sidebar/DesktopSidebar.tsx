import { Box, IconButton, Icon, Flex, useColorModeValue as mode } from '@chakra-ui/react';
import { MouseEventHandler, ReactNode } from 'react';
import { MdKeyboardArrowRight, MdKeyboardArrowLeft } from 'react-icons/md';

import { ExpandedSidebarContent } from './SidebarContent';
import { MenuSection } from './utils';

interface DesktopSidebarContainerProps {
  toggleSidebar: MouseEventHandler;
  isCollapsed: boolean;
  currentTab: string;
  children: ReactNode;
}

interface DesktopSidebarProps {
  isCollapsed: boolean;
  toggleSidebar: MouseEventHandler;
  currentTab: string;
  menu: MenuSection;
  filteredMenu: string[];
}

const DesktopSidebarContainer = ({
  toggleSidebar,
  isCollapsed,
  currentTab,
  children,
}: DesktopSidebarContainerProps) => (
  <Box>
    <IconButton
      onClick={toggleSidebar}
      aria-label="Collapse sidebar"
      rounded="full"
      pos="absolute"
      top="58px"
      left={isCollapsed ? '10' : '225px'}
      bgColor={`${currentTab}.header`}
      zIndex={2}
      h={9}
      w={9}
      icon={
        <Icon
          as={isCollapsed ? MdKeyboardArrowRight : MdKeyboardArrowLeft}
          color="white"
          _hover={{
            color: `${currentTab}.header`,
          }}
          h={8}
          w={8}
          boxSize={8}
        />
      }
    />
    <Flex
      height="100vh"
      direction="column"
      borderRightWidth="1px"
      pt={20}
      pb={4}
      w={isCollapsed ? '16' : 'full'}
      minW={!isCollapsed ? { lg: '250px' } : 'unset'}
      bgColor={`${currentTab}.header`}
      h="100%"
      overflowY="auto"
      color={mode('whiteAlpha.800', 'blackAlpha.800')}
    >
      {children}
    </Flex>
  </Box>
);

const DesktopSidebar = ({
  isCollapsed,
  toggleSidebar,
  currentTab,
  menu,
  filteredMenu,
}: DesktopSidebarProps) => (
  <DesktopSidebarContainer
    toggleSidebar={toggleSidebar}
    isCollapsed={isCollapsed}
    currentTab={currentTab}
  >
    {!isCollapsed && <ExpandedSidebarContent menuItems={menu} filteredMenuItems={filteredMenu} />}
  </DesktopSidebarContainer>
);

export default DesktopSidebar;
