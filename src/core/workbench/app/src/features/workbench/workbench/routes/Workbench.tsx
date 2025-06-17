/* eslint-disable react-hooks/exhaustive-deps */
import { Flex, useDisclosure } from '@chakra-ui/react';
import { startInactiveSpan } from '@sentry/react';
import React, { useEffect, useContext, useState, useRef } from 'react';

import { Header } from '../../../../components/Header';
import { ModalSpinner } from '../../../../components/ModalSpinner';
import PageSidebarContainer from '../../../../components/Sidebar/PageSidebarContainer';
import { AccountContext } from '../../../../context/AccountContext';
import { Account } from '../../../../context/AccountContext/types';
import { ObserveSubTabsContext } from '../../../../context/ObserveSubTabsContext';
import { TabsContext } from '../../../../context/TabsContext';
import { HasWorkbenchAccess, UserContext } from '../../../../context/UserContext';
import { getSiteContext } from '../../../../utils/siteContext';
import { WebSocketContext } from '../../../global/websocket/WebSocketContext';
import { AnalyzeTab } from '../../analyze/components/AnalyzeTab';
import { DocsTab } from '../../docs';
import { LoadTab } from '../../load';
import { ObserveTab } from '../../observe';
import { OrchestrateTab } from '../../orchestrate';
import { TransformTab } from '../../transform';
import { WorkbenchStatus } from '../types';

const ONE_MINUTE_IN_MILLISECONDS = 60e3; // 60 seconds to milliseconds

const TAB_TO_SERVICE: { [key: string]: string } = {
  load: 'airbyte',
  transform: 'code-server',
  analyze: 'superset',
  'local-dbt-docs': 'code-server',
  'dbt-docs': 'dbt-docs',
  datahub: 'datahub',
  orchestrate: 'airflow',
};

export const Workbench = () => {
  const { isOpen, onOpen, onClose } = useDisclosure({ defaultIsOpen: true });
  const { currentUser } = useContext(UserContext);
  const { currentTab } = useContext(TabsContext);
  const { currentSubTab } = useContext(ObserveSubTabsContext);
  const { setCurrentAccount, accounts } = useContext(AccountContext);
  const [wstatus, setWstatus] = useState<WorkbenchStatus>();
  const [errorResponse, setErrorResponse] = useState('');
  const [heartbeatRestart, setHeartbeatRestart] = useState<number>(0);
  const [workspaceLogs, setWorkspaceLogs] = useState<string[]>([]);
  const siteContext = getSiteContext();

  const { isWebSocketReady, webSocketFailed, sendMessageBySocket, getEnvStatus, getSocketMessage } =
    useContext(WebSocketContext);
  /*
   * In my testing, it seems like it's possible for useEffect to "bounce"
   * and thus call timingSpan.end twice -- let's keep track of if the
   * span has ended yet.
   */
  const [timingState, setTimingState] = useState('started');
  /*
   * We can use app.start.warm / app.start.cold if we know we are doing
   * a warm or cold start.  I'm not sure how to figure that out at this
   * point, so I'm going to use a generic app.start
   */
  const timingSpan = useState(
    startInactiveSpan({
      name: 'Workbench Load Time',
      op: 'app.start',
      forceTransaction: true,
    })
  );

  const isCodeServerActive = useRef(false);
  const socketAttempts = useRef(0);
  const heartbeatPingPongSuccess = useRef(false);
  const heartbeatCounter = useRef(0);
  const heartbeatInterval = useRef<any>();
  const timer = useRef(0);

  const checkStatus = () => {
    sendMessageBySocket({
      message_type: 'env.status',
      env_slugs: siteContext.env,
      component: 'workbench',
      attempt: socketAttempts.current,
    });
  };

  const heartbeat = () => {
    heartbeatCounter.current++;
    sendMessageBySocket({
      message_type: 'env.heartbeat',
      env_slug: siteContext.env,
      counter: heartbeatCounter.current,
    });
  };

  useEffect(() => {
    // Set up an interval to check the timer every second
    const interval = setInterval(() => {
      timer.current += 2;

      // If heartbeat fails after 10, 20, 30, N seconds, restart the heartbeat
      if (!heartbeatPingPongSuccess.current && [10, 20, 30, 40, 50, 60].includes(timer.current)) {
        heartbeatCounter.current = 0;
        setHeartbeatRestart(timer.current); // can be any value to trigger useEffect
      }

      // If the code server is not running after 60 seconds, we do something.
      if (!isCodeServerActive.current && timer.current == 60) {
        // TODO: Here we can show a toast message or something for example events from the pod
        console.log('Code server took too long to start. Please try again.');
      }

      // Stop the interval after 10 minutes
      if (timer.current == 10 * ONE_MINUTE_IN_MILLISECONDS) {
        clearInterval(interval);
      }
    }, 2 * ONE_MINUTE_IN_MILLISECONDS); // Check every second

    // Cleanup the interval on component unmount
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const message = getSocketMessage('env.heartbeat');
    if (message) {
      // We have received a heartbeat message from the websocket server
      heartbeatPingPongSuccess.current = true;
      isCodeServerActive.current = Object.assign(message).message.code_server_active;
    }
  }, [getSocketMessage]);

  useEffect(() => {
    if (isWebSocketReady && siteContext.env) {
      if (heartbeatInterval.current) {
        clearInterval(heartbeatInterval.current);
      }

      heartbeat();
      heartbeatInterval.current = setInterval(heartbeat, ONE_MINUTE_IN_MILLISECONDS);

      // Cleanup the interval on component unmount
      return () => clearInterval(heartbeatInterval.current);
    }
  }, [isWebSocketReady, heartbeatRestart]);

  useEffect(() => {
    if (isWebSocketReady && socketAttempts.current == 0 && siteContext.env) {
      socketAttempts.current++;
      checkStatus();
    }
  }, [isWebSocketReady]);

  useEffect(() => {
    if (siteContext.env) {
      const envStatus = getEnvStatus(siteContext.env);
      if (envStatus) {
        const result = Object.assign(envStatus);
        setWstatus(result.details);
        isCodeServerActive.current = result.details?.status === 'running';
      }
    }
  }, [wstatus, getEnvStatus]);

  useEffect(() => {
    // Update logs based on the current tab and workbench status
    const containerStatuses =
      wstatus && wstatus.containers
        ? currentTab === 'observe'
          ? wstatus.containers[TAB_TO_SERVICE[currentSubTab]]
          : wstatus.containers[TAB_TO_SERVICE[currentTab]]
        : [];

    if (containerStatuses) {
      const logs: string[] = [];
      containerStatuses.reverse().forEach((container) => {
        Object.keys(container).forEach((key) => {
          let title = key;

          switch (key) {
            case 'local-airflow':
              title = 'my-airflow';
              break;
            case 'code-server':
              title = 'vs-code';
              break;
            default:
          }

          logs.push(`${title} ${container[key]}...`);
        });
      });
      setWorkspaceLogs(logs);
    } else {
      setWorkspaceLogs([]);
    }
  }, [wstatus, currentTab, currentSubTab]);

  useEffect(() => {
    if (currentUser !== undefined) {
      const account = accounts?.find(
        (account: Account) => account.slug === currentUser.env_account
      );
      setCurrentAccount(account);
      onOpen();
      if (!HasWorkbenchAccess(currentUser)) {
        setErrorResponse("You don't have permissions to access this environment.");
      } else {
        setTimeout(() => {
          if (webSocketFailed) {
            setHeartbeatRestart(timer.current);
          }
        }, 500);
      }
    }
  }, [currentUser, webSocketFailed]);

  useEffect(
    () => updateTabProgress(),
    [wstatus, webSocketFailed, currentUser, currentTab, currentSubTab]
  );

  const updateTabProgress = () => {
    let tabStatus =
      wstatus && wstatus.services
        ? currentTab === 'observe'
          ? wstatus.services[TAB_TO_SERVICE[currentSubTab]]
          : wstatus.services[TAB_TO_SERVICE[currentTab]]
        : 'not_ready';

    if (tabStatus === undefined) {
      tabStatus = 'running';
    }

    if (tabStatus === 'in_progress' || tabStatus === 'not_found') {
      onOpen();
      if (webSocketFailed) {
        setHeartbeatRestart(timer.current);
      }
    } else if (tabStatus === 'running') {
      setErrorResponse('');
      onClose();
      if (timingState === 'started') {
        timingSpan[0]?.end();
        setTimingState('ended');
      }
    } else if (wstatus?.status === 'error') {
      setErrorResponse(
        'Sorry, we could not start your environment. Please try again in a few minutes or contact support'
      );
      if (timingState === 'started') {
        timingSpan[0]?.end();
        setTimingState('ended');
      }
    }
  };

  return (
    <Flex flexFlow="column" h="100vh">
      <Header isWorkbench wstatus={wstatus} />
      <PageSidebarContainer>
        <Flex flexFlow="column" flex="1" mt="12">
          <DocsTab isLoading={isOpen} />
          <LoadTab isLoading={isOpen} />
          <TransformTab isLoading={isOpen} />
          <ObserveTab isLoading={isOpen} />
          <OrchestrateTab isLoading={isOpen} />
          <AnalyzeTab isLoading={isOpen} />
          {errorResponse
            ? isOpen && <ModalSpinner message={errorResponse} showSpinner={false} />
            : isOpen && (
                <ModalSpinner
                  message={`Starting your ${
                    currentTab === 'observe' ? currentSubTab.replaceAll('-', ' ') : currentTab
                  } environment`}
                  showSpinner={true}
                  sidebar={currentTab === 'observe'}
                  details={workspaceLogs}
                />
              )}
        </Flex>
      </PageSidebarContainer>
    </Flex>
  );
};
