import { useBreakpointValue } from '@chakra-ui/react';
import { MouseEvent, useContext, useMemo, useState } from 'react';

import { AccountContext } from '../../context/AccountContext';
import { TabsContext } from '../../context/TabsContext';
import { UserContext } from '../../context/UserContext';
import { usePersistedState } from '../../hooks/usePersistedState';
import { getSiteContext } from '../../utils/siteContext';

import DesktopSidebar from './DesktopSidebar';
import MobileSidebar from './MobileSidebar';
import { getAccountAdministrationMenu } from './utils';

export enum SidebarVariant {
  Mobile = 'Mobile',
  Desktop = 'Desktop',
}

const Sidebar = () => {
  const { env } = getSiteContext();
  const { currentUser } = useContext(UserContext);
  const { currentAccount } = useContext(AccountContext);
  const { currentTab } = useContext(TabsContext);
  const [isCollapsed, setIsCollapsed] = usePersistedState('sidebarCollapsed', false);
  const [isMobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  const isWorkbench = useMemo(() => window.location.host.split('.')[0] === env, [env]);

  const sidebarVariant =
    useBreakpointValue(
      { base: SidebarVariant.Mobile, md: SidebarVariant.Desktop },
      { ssr: false }
    ) || SidebarVariant.Desktop;

  const containsAdminPermissions = currentUser?.permissions.join(':').includes('admin');

  const dark = ['docs', 'load', 'transform', 'observe', 'orchestrate'].includes(currentTab);

  const menu = getAccountAdministrationMenu(currentUser, currentAccount);

  // Do not show empty sections
  const filteredMenu = Object.keys(menu).filter(
    (key) => menu[key].filter(({ shouldRender }) => shouldRender).length
  );

  const shouldShowSidebar =
    !!(filteredMenu.length && currentUser && containsAdminPermissions) && !isWorkbench;

  const shouldShowDesktopSidebar = sidebarVariant === SidebarVariant.Desktop && !isWorkbench;

  const toggleSidebar = (e: MouseEvent) => {
    e.preventDefault();
    setIsCollapsed((prev: boolean) => !prev);
  };

  const toggleMobileSidebar = () => setMobileSidebarOpen((prevState) => !prevState);

  return (
    <>
      {shouldShowSidebar &&
        (shouldShowDesktopSidebar ? (
          <DesktopSidebar
            isCollapsed={isCollapsed}
            toggleSidebar={toggleSidebar}
            currentTab={currentTab}
            menu={menu}
            filteredMenu={filteredMenu}
          />
        ) : (
          sidebarVariant === SidebarVariant.Mobile && (
            <MobileSidebar
              isWorkbench={isWorkbench}
              onClose={toggleMobileSidebar}
              isOpen={isMobileSidebarOpen}
              dark={dark}
              menu={menu}
              filteredMenu={filteredMenu}
            />
          )
        ))}
    </>
  );
};

export default Sidebar;
