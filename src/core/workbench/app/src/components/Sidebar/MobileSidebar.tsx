import { Box } from '@chakra-ui/layout';
import {
  Drawer,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  DrawerBody,
} from '@chakra-ui/modal';

import { MobileHamburgerMenu } from '../Header/MobileHamburgerMenu';
import { NavMenu } from '../Header/NavMenu';

import { ExpandedSidebarContent } from './SidebarContent';
import { MenuSection } from './utils';

interface Props {
  isWorkbench: boolean;
  onClose: () => void;
  isOpen: boolean;
  dark: boolean;
  menu: MenuSection;
  filteredMenu: string[];
}

const MobileSidebar = ({ isWorkbench, onClose, isOpen, dark, menu, filteredMenu }: Props) => (
  <>
    <Box color="white" zIndex={10} pl={4}>
      <MobileHamburgerMenu onClick={onClose} isOpen={isOpen} />
    </Box>
    {isWorkbench ? (
      <NavMenu.Mobile isOpen={isOpen} dark={dark} />
    ) : (
      <Drawer isOpen={isOpen} placement="left" onClose={onClose}>
        <DrawerOverlay>
          <DrawerContent>
            <DrawerCloseButton />
            <DrawerBody color="black">
              <ExpandedSidebarContent menuItems={menu} filteredMenuItems={filteredMenu} />
            </DrawerBody>
          </DrawerContent>
        </DrawerOverlay>
      </Drawer>
    )}
  </>
);

export default MobileSidebar;
