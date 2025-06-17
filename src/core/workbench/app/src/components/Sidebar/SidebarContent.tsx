import {
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionIcon,
  AccordionPanel,
  Heading,
  Text,
} from '@chakra-ui/react';
import { useLocation } from 'react-router';

import { NavLink } from './NavLink';
import { MenuSection } from './utils';

interface ExpandedProps {
  menuItems: MenuSection;
  filteredMenuItems: string[];
}

export const ExpandedSidebarContent = ({ menuItems, filteredMenuItems }: ExpandedProps) => {
  const itemNumber = Object.keys(menuItems).length;
  const { pathname } = useLocation();
  return (
    <>
      <Heading size="sm" py={6} px={4}>
        Account Administration
      </Heading>
      <Accordion allowMultiple defaultIndex={Array.from(Array(itemNumber).keys())}>
        {filteredMenuItems.map((key) => (
          <AccordionItem border="none" key={key}>
            <AccordionButton display="flex" justifyContent="flex-start" gap={2}>
              <AccordionIcon />
              <Text fontSize="xs" textAlign="left" fontWeight="semibold">
                {key.toUpperCase()}
              </Text>
            </AccordionButton>
            <AccordionPanel>
              {menuItems[key]
                .filter(({ shouldRender }) => shouldRender)
                .map(({ heading, navigateTo, icon }) => (
                  <NavLink
                    label={heading}
                    icon={icon}
                    href={navigateTo}
                    isActive={pathname.indexOf(navigateTo) >= 0}
                    key={heading}
                  />
                ))}
            </AccordionPanel>
          </AccordionItem>
        ))}
      </Accordion>
    </>
  );
};
