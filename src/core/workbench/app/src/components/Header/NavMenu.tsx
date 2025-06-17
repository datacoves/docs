import { ExternalLinkIcon } from '@chakra-ui/icons';
import {
  Box,
  Divider,
  Flex,
  HStack,
  MenuGroup,
  MenuItem,
  MenuList,
  VStack,
  Text,
  List,
  ListItem,
  ListIcon,
} from '@chakra-ui/react';
import { Fragment, useContext, useState } from 'react';
import {
  HiViewGridAdd,
  HiAdjustments,
  HiEye,
  HiBookOpen,
  HiInboxIn,
  HiChartBar,
  HiOutlinePlay,
  HiOutlineUser,
  HiOutlineUserGroup,
  HiOutlineRefresh,
  HiCode,
} from 'react-icons/hi';
import { MdCheckCircle } from 'react-icons/md';

import { TabsContext } from '../../context/TabsContext';
import {
  UserContext,
  HasTabAccess,
  tabPermissions,
  confirmUserPermissions,
  HasWorkbenchAccess,
  HasWorkbenchServiceAccess,
} from '../../context/UserContext';
import { restartCodeServer } from '../../features/global/api/restartCodeServer';
import { startLocalAirflow } from '../../features/global/api/startLocalAirflow';
import { WebSocketContext } from '../../features/global/websocket/WebSocketContext';
import { WorkbenchStatus } from '../../features/workbench/workbench';
import {
  analyzeLink,
  docsLink,
  loadLink,
  localAirflowLink,
  openLink,
  orchestrateLink,
  transformLink,
} from '../../utils/link';
import { getSiteContext } from '../../utils/siteContext';
import { AlertDialog } from '../AlertDialog';

import { NavItem } from './NavItem';

const MobileNavMenu = (props: { isOpen?: boolean; dark?: boolean }) => {
  const { isOpen } = props;
  const { currentTab, setCurrentTab } = useContext(TabsContext);
  const { currentUser } = useContext(UserContext);
  const tabs = ['docs', 'load', 'transform', 'observe', 'orchestrate', 'analyze'];

  return (
    <Flex
      hidden={!isOpen}
      as="nav"
      direction="column"
      bg="blue.600"
      position="fixed"
      height="calc(100vh - 4rem)"
      top="12"
      insetX="0"
      zIndex={10}
      w="full"
    >
      <Box px="4">
        {currentUser &&
          tabs.map((tab) => (
            <NavItem.Mobile
              key={tab}
              onClick={() => setCurrentTab(tab)}
              active={currentTab === tab}
              label={tab}
              dark={props.dark}
            />
          ))}
      </Box>
    </Flex>
  );
};

const DesktopNavMenu = (props: { dark?: boolean; wstatus?: WorkbenchStatus }) => {
  const { isWebSocketReady, sendMessageBySocket } = useContext(WebSocketContext);
  const { currentTab, setCurrentTab } = useContext(TabsContext);
  const { currentUser } = useContext(UserContext);
  const siteContext = getSiteContext();
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const onClose = () => setIsConfirmOpen(false);
  const [isLocalAirflowConfirmOpen, setIsLocalAirflowConfirmOpen] = useState(false);
  const onCloseLocalAirflow = () => setIsLocalAirflowConfirmOpen(false);
  const [showRestartingText, setShowRestartingText] = useState<boolean>(false);
  const [isLocalAirflowContinueOpen, setIsLocalAirflowContinueOpen] = useState(
    (() => {
      return localStorage.getItem('openLocalAirflow') === 'true';
    })()
  );

  const envShareLinks = currentUser?.user_environments.find(
    (x) => x.env_slug === siteContext.env
  )?.share_links;
  const shareLinks: string[] = envShareLinks ? Object.keys(envShareLinks) : [];

  const envSlug = getSiteContext().env;
  const project = currentUser?.projects.find((project) =>
    project.environments.find((environment) => environment.slug === envSlug)
  );
  const env = project && project.environments.find((environment) => environment.slug === envSlug);

  const handleResetCodeServer = () => {
    if (siteContext.env) {
      setShowRestartingText(true);
      if (isWebSocketReady) {
        sendMessageBySocket({
          message_type: 'env.restart.code-server',
          env_slug: siteContext.env,
        });
        setTimeout(() => window.location.reload(), 5000);
      } else {
        restartCodeServer(siteContext.env).then(() => {
          setTimeout(() => window.location.reload(), 5000);
        });
      }
    }
  };

  const handleStartLocalAirflow = () => {
    if (siteContext.env) {
      setShowRestartingText(true);

      if (isWebSocketReady) {
        sendMessageBySocket({
          message_type: 'env.start.local-airflow',
          env_slug: siteContext.env,
        });
        setTimeout(() => {
          localStorage.setItem('openLocalAirflow', 'true');
          localStorage.setItem('currentTab', JSON.stringify('transform'));
          window.location.reload();
        }, 5000);
      } else {
        startLocalAirflow(siteContext.env).then(() => {
          setTimeout(() => {
            localStorage.setItem('openLocalAirflow', 'true');
            localStorage.setItem('currentTab', JSON.stringify('transform'));
            window.location.reload();
          }, 5000);
        });
      }
    }
  };

  const handleContinueLocalAirflow = () => {
    if (currentUser) {
      openLink(localAirflowLink(currentUser.slug));
      onCloseContinueLocalAirflow();
    }
  };

  const onCloseContinueLocalAirflow = () => {
    setIsLocalAirflowContinueOpen(false);

    // Clean the local storage
    localStorage.removeItem('openLocalAirflow');
    setCurrentTab('transform');
  };

  const shouldShowTab = (tab: string) => {
    if (currentUser) {
      // If local airflow is enabled we also check for code-server on the orchestrate tab
      const tabPerms = tabPermissions[tab].concat(
        tab === 'orchestrate' && currentUser?.features.local_airflow ? ['code-server'] : []
      );

      const checkServicePermission = (code: string) =>
        env?.services[code]?.enabled &&
        env?.services[code]?.valid &&
        confirmUserPermissions(currentUser, [code], envSlug, project?.slug);

      const getRequiredCheckMethod = () => {
        if (tab === 'orchestrate') {
          return env?.type === 'prod' ? 'some' : 'every';
        }
        return 'some';
      };

      return tabPerms.length > 0
        ? tabPerms[getRequiredCheckMethod()](checkServicePermission)
        : HasWorkbenchAccess(currentUser);
    }
    return false;
  };

  const getUnmetConditions = (tab: string) => {
    const unmetConditions: Array<string> = [];
    if (tab !== 'docs') {
      if (currentUser) {
        const servicesInvalid = tabPermissions[tab].filter(
          (code) => env?.services[code].valid === false
        );
        if (servicesInvalid.length === tabPermissions[tab].length) {
          servicesInvalid.map((service) =>
            env?.services[service].unmet_preconditions?.map((unmet) =>
              unmetConditions.push(unmet.message)
            )
          );
        }
      }
    }
    return unmetConditions;
  };

  const getUnmetUserServiceConditions = (service: string) => {
    if (currentUser) {
      const ue = currentUser.user_environments.find(
        (environment) => environment.env_slug == envSlug
      );

      if (ue?.services[service]) {
        return ue.services[service].unmet_preconditions;
      }
    }

    return [];
  };

  return (
    <HStack spacing="3" flex="1" display={{ base: 'none', lg: 'flex' }} justifyContent="center">
      {currentUser && shouldShowTab('docs') && (
        <NavItem.Desktop
          onClick={() => setCurrentTab('docs')}
          active={currentTab === 'docs'}
          icon={<HiBookOpen />}
          label="Docs"
          dark={props.dark}
          href={docsLink(true)}
          isEnabled={!getUnmetConditions('docs').length}
          unmetConditions={getUnmetConditions('docs')}
        />
      )}
      {currentUser && shouldShowTab('load') && (
        <NavItem.Desktop
          onClick={() => setCurrentTab('load')}
          active={currentTab === 'load'}
          icon={<HiInboxIn />}
          label="Load"
          dark={props.dark}
          href={loadLink()}
          isEnabled={!getUnmetConditions('load').length}
          unmetConditions={getUnmetConditions('load')}
        />
      )}
      {currentUser && shouldShowTab('transform') && currentUser.has_license && (
        <NavItem.Desktop
          onClick={() =>
            HasTabAccess(currentUser, 'transform') &&
            currentUser.has_license &&
            setCurrentTab('transform')
          }
          active={currentTab === 'transform'}
          icon={<HiViewGridAdd />}
          label="Transform"
          dark={props.dark}
          isEnabled={!getUnmetConditions('transform').length}
          unmetConditions={getUnmetConditions('transform')}
          href={transformLink(currentUser.slug)}
          menuList={
            (!getUnmetConditions('transform').length && currentUser?.features.codeserver_restart) ||
            shareLinks.length > 0 ? (
              <MenuList color="black" mt={-1}>
                <MenuItem onClick={() => setCurrentTab('transform')} icon={<HiCode />}>
                  Open VS Code
                </MenuItem>
                <MenuItem
                  onClick={() => setIsConfirmOpen(true)}
                  icon={<HiOutlineRefresh />}
                  isDisabled={
                    !props.wstatus?.services ||
                    props.wstatus?.services?.['code-server'] !== 'running'
                  }
                >
                  Reset my environment
                </MenuItem>
                {shareLinks.length > 0 && (
                  <>
                    <Divider />
                    <MenuGroup title="Other links">
                      {shareLinks.map((service: string) => (
                        <MenuItem
                          icon={<ExternalLinkIcon />}
                          onClick={() => envShareLinks && openLink(envShareLinks[service])}
                          key={service}
                        >
                          {service}
                        </MenuItem>
                      ))}
                    </MenuGroup>
                  </>
                )}
              </MenuList>
            ) : undefined
          }
        />
      )}
      {currentUser && shouldShowTab('observe') && (
        <NavItem.Desktop
          onClick={() => setCurrentTab('observe')}
          active={currentTab === 'observe'}
          icon={<HiEye />}
          label="Observe"
          dark={props.dark}
          isEnabled={!getUnmetConditions('observe').length}
          unmetConditions={getUnmetConditions('observe')}
        />
      )}
      {currentUser &&
        shouldShowTab('orchestrate') &&
        (currentUser?.features.local_airflow &&
        confirmUserPermissions(
          currentUser,
          ['airflow:admin', 'airflow:sysadmin'],
          envSlug,
          project?.slug
        ) ? (
          <NavItem.Desktop
            onClick={() => setCurrentTab('orchestrate')}
            active={currentTab === 'orchestrate'}
            icon={<HiAdjustments />}
            label="Orchestrate"
            dark={props.dark}
            href={orchestrateLink()}
            isEnabled={!getUnmetConditions('orchestrate').length}
            unmetConditions={getUnmetConditions('orchestrate')}
            menuList={
              <MenuList color="black" mt={-1}>
                {HasWorkbenchServiceAccess(currentUser, ['airflow']) && (
                  <MenuItem
                    onClick={() => setCurrentTab('orchestrate')}
                    icon={<HiOutlineUserGroup />}
                  >
                    Open Team Airflow
                  </MenuItem>
                )}
                {env?.type != 'prod' ? (
                  getUnmetUserServiceConditions('local-airflow').length ? (
                    <>
                      <MenuItem
                        onClick={(event) => {
                          event.stopPropagation();
                          setIsLocalAirflowConfirmOpen(true);
                        }}
                        isDisabled={props.wstatus?.services?.['code-server'] !== 'running'}
                        icon={<HiOutlinePlay />}
                      >
                        Start My Airflow
                      </MenuItem>
                    </>
                  ) : (
                    <>
                      <MenuItem
                        onClick={() => openLink(localAirflowLink(currentUser.slug))}
                        isDisabled={props.wstatus?.services?.['code-server'] !== 'running'}
                        icon={<HiOutlineUser />}
                      >
                        Open My Airflow
                      </MenuItem>
                    </>
                  )
                ) : (
                  <></>
                )}
              </MenuList>
            }
          />
        ) : (
          <NavItem.Desktop
            onClick={() => setCurrentTab('orchestrate')}
            active={currentTab === 'orchestrate'}
            icon={<HiAdjustments />}
            label="Orchestrate"
            dark={props.dark}
            href={orchestrateLink()}
            isEnabled={!getUnmetConditions('orchestrate').length}
            unmetConditions={getUnmetConditions('orchestrate')}
          />
        ))}
      {currentUser && shouldShowTab('analyze') && (
        <NavItem.Desktop
          onClick={() => setCurrentTab('analyze')}
          active={currentTab === 'analyze'}
          icon={<HiChartBar />}
          label="Analyze"
          dark={props.dark}
          href={analyzeLink()}
          isEnabled={!getUnmetConditions('analyze').length}
          unmetConditions={getUnmetConditions('analyze')}
        />
      )}
      <AlertDialog
        isOpen={isConfirmOpen}
        header="Reset my environment"
        message={
          <VStack alignItems="flex-start">
            <Text>This action will restore the following items to defaults:</Text>
            <List spacing={3}>
              <ListItem>
                <ListIcon as={MdCheckCircle} color="green.500" />
                Python libraries
              </ListItem>
              <ListItem>
                <ListIcon as={MdCheckCircle} color="green.500" />
                Code extensions
              </ListItem>
              <ListItem>
                <ListIcon as={MdCheckCircle} color="green.500" />
                Code settings
              </ListItem>
              <ListItem>
                <ListIcon as={MdCheckCircle} color="green.500" />
                SSH and database keys
              </ListItem>
              <ListItem>
                <ListIcon as={MdCheckCircle} color="green.500" />
                dbt profiles
              </ListItem>
            </List>
            {showRestartingText && <Text>Restarting your environment...</Text>}
          </VStack>
        }
        confirmLabel="OK, go ahead"
        onClose={onClose}
        onConfirm={handleResetCodeServer}
        isLoadingOnSubmit={true}
      />
      <AlertDialog
        isOpen={isLocalAirflowConfirmOpen}
        header="Start My Airflow"
        // The prettier is driving me insane trying to format this text
        // in utterly pointless ways.
        // prettier-ignore
        message={
          <VStack alignItems="flex-start">
            <Text>
              Starting{' '}<Text as="b" color="blue.900">My Airflow</Text> will require a reload of VS Code.
              You will not lose any settings or data.
            </Text>
            {showRestartingText && <Text>Reloading...</Text>}
          </VStack>
        }
        confirmLabel="OK, go ahead"
        onClose={onCloseLocalAirflow}
        onConfirm={handleStartLocalAirflow}
        isLoadingOnSubmit={true}
        confirmColor="green"
      />
      <AlertDialog
        isOpen={
          isLocalAirflowContinueOpen && props.wstatus?.services?.['code-server'] === 'running'
        }
        header="My Airflow is Ready"
        // The prettier is driving me insane trying to format this text
        // in utterly pointless ways.
        // prettier-ignore
        message={
          <VStack alignItems="flex-start">
            <Text>Any changes to your DAGS in VS Code will appear in your{' '}<Text as="b" color="blue.900">My Airflow</Text> instance</Text>
            <Text>
              Click the button below to open {' '}<Text as="b" color="blue.900">My Airflow</Text> in a new tab.
            </Text>
          </VStack>
        }
        confirmLabel="Open My Airflow"
        onClose={onCloseContinueLocalAirflow}
        onConfirm={handleContinueLocalAirflow}
        isLoadingOnSubmit={true}
        confirmColor="green"
      />
    </HStack>
  );
};

export const NavMenu = {
  Mobile: MobileNavMenu,
  Desktop: DesktopNavMenu,
};
