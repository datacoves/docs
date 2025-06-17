import { ChakraProvider, useToast } from '@chakra-ui/react';
import * as Sentry from '@sentry/react';
import React, { useState, useEffect, useRef, createElement } from 'react';
import { useErrorHandler } from 'react-error-boundary';
import { BrowserRouter as Router } from 'react-router-dom';

import ExpandibleToast from '../components/ExpandibleToast/ExpandibleToast';
import { API_URL, WS_URL } from '../config';
import { useGetUserAccounts } from '../context/AccountContext/api/getUserAccounts';
import { Account } from '../context/AccountContext/types';
import { useGetUserInfo } from '../context/UserContext/api/getUserInfo';
import { User } from '../context/UserContext/types';
import { WebSocketContext } from '../features/global/websocket/WebSocketContext';
import { usePersistedState } from '../hooks/usePersistedState';
import { main } from '../themes';
import { getSiteContext } from '../utils/siteContext';

import { AccountContext } from './AccountContext';
import { ObserveSubTabsContext } from './ObserveSubTabsContext';
import { TabsContext } from './TabsContext';
import { HasTabAccess, UserContext } from './UserContext';

type AppProviderProps = {
  children: React.ReactNode;
};

const isPublicPage = () => {
  // Public pages should not retrieve data from api
  return window.location.pathname === '/sign-in';
};

export const UIProvider = ({ children }: AppProviderProps) => {
  const toast = useToast();
  const [currentUser, setCurrentUser] = useState<User>();
  const [currentTab, setCurrentTab] = usePersistedState('currentTab', 'docs');
  const [currentObserveSubTab, setCurrentObserveSubTab] = usePersistedState(
    'currentObserveSubTab',
    'local-dbt-docs'
  );
  const handleError = useErrorHandler();
  const [currentAccount, setAccount] = useState<Account | undefined>();
  const [accountSlug, setAccountSlug] = usePersistedState('accountSlug', undefined);
  const [accounts, setAccounts] = useState<Account[]>();
  const [webSocket, setWebSocket] = useState<WebSocket>();
  const [webSocketFailed, setWebSocketFailed] = useState<boolean>(false);
  const [isWebSocketReady, setWebSocketReady] = useState<boolean>(false);
  const [envStatusMessages, setEnvStatusMessages] = useState<object[]>([]);
  const [socketMessages, setSocketMessages] = useState<object[]>([]);
  const siteContext = getSiteContext();
  const socketAttemptsConnection = useRef(1);
  const webSocketUrl = useRef('');

  const redirectOnError = (err: any) => {
    if (err.response && [401, 403].includes(err.response.status)) {
      window.location.href = `${API_URL}/iam/login?next=${window.location}`;
    } else {
      handleError(err);
    }
  };

  const datacovesSocket = () => {
    if (webSocket && webSocket.readyState == WebSocket.OPEN) {
      webSocket.close();
    }

    const socket = new WebSocket(webSocketUrl.current);
    socket.onopen = () => {
      console.log('[Websocket] opened.');
      setWebSocket(socket);
      setWebSocketReady(true);
      setWebSocketFailed(false);
      socketAttemptsConnection.current = 1;
    };

    socket.onclose = (event) => {
      if (!event.wasClean && socketAttemptsConnection.current) {
        socketAttemptsConnection.current++;
        setTimeout(() => datacovesSocket(), 1000);
      } else {
        console.log('[Websocket] closed.');
      }

      setWebSocketReady(false);
    };

    socket.onerror = (error) => {
      console.error('[Websocket]', error);
      socket.close();
      setWebSocketFailed(true);
    };

    socket.onmessage = (event) => {
      const receivedMessage = JSON.parse(event.data);
      const messageType = receivedMessage['message_type'];
      const message = receivedMessage['message'];

      // Store websocket messages in state
      setSocketMessages((messages) => {
        const socketMessages = messages.filter((msg: any) => msg.message_type !== messageType);
        return [...socketMessages, receivedMessage];
      });

      switch (messageType) {
        case 'user.toast': {
          toast({
            render: () => {
              return createElement(ExpandibleToast, {
                message: message['content'],
                extra: message['extra'],
                status: message['status'],
              });
            },
            isClosable: true,
          });
          break;
        }
        case 'env.heartbeat': {
          if (!message['code_server_active']) {
            /*
            We send this notifacton only once when the code server pod is not running.
            Since the startup process takes a bit longer.
            */
            setTimeout(() => {
              toast({
                render: () => {
                  return createElement(ExpandibleToast, {
                    message: 'Workspace loading',
                    extra:
                      'We are setting up your VS-Code. You will be able to access it in a few seconds.',
                    status: 'info',
                  });
                },
                isClosable: true,
                position: 'bottom',
                duration: 7000,
              });
            }, 2000); // 2 seconds
          }
          break;
        }
        case 'env.status':
          setEnvStatusMessages((messages) => {
            const updatedMessages = messages.filter((msg: any) => msg.env !== message.env);
            return [...updatedMessages, message];
          });
          break;

        default:
          console.log('Unknown websocket message:', receivedMessage);
      }
    };
  };

  useEffect(() => {
    if (currentAccount) {
      const wsUrl = `${WS_URL}/ws/account/${currentAccount.slug}/`;
      if (webSocketUrl.current !== wsUrl) {
        webSocketUrl.current = wsUrl;
        datacovesSocket();
      }
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentAccount]);

  const sendMessageBySocket = async (message: object) => {
    waitForSocketConnection(() => webSocket?.send(JSON.stringify(message)));
  };

  const waitForSocketConnection = (callback: () => void, attempts = 20) => {
    if (webSocket?.readyState === WebSocket.OPEN) {
      callback();
    } else if (attempts > 0) {
      setTimeout(() => waitForSocketConnection(callback, attempts - 1), 1000);
    } else {
      console.error('[Websocket] Could not establish connection.');
    }
  };

  const getEnvStatus = (envSlug: string) => {
    const items = envStatusMessages.filter((item) => Object.assign(item).env === envSlug);
    return items.length > 0 ? items[0] : {};
  };

  const getSocketMessage = (messageType: string) => {
    const items = socketMessages.filter((item) => Object.assign(item).message_type === messageType);
    const message = items.length > 0 ? items[0] : null;
    return message;
  };

  useGetUserInfo(
    {
      account: currentAccount?.slug,
      environment: siteContext.env,
    },
    {
      onSuccess: (resp: User) => {
        setCurrentUser(resp);
        // Sentry tags
        Sentry.setTag('user.slug', resp.slug);
        Sentry.setTag('account.slug', currentAccount?.slug);
        // Google Analytics properties
        if (window.gtag) {
          window.gtag('config', 'G-X8V16WM99D', {
            user_id: resp.slug,
          });
          window.gtag('set', 'user_properties', {
            user_slug: resp.slug,
            account_slug: currentAccount?.slug,
          });
        }
      },
      onError: redirectOnError,
      enabled: !isPublicPage() && !!accounts,
    }
  );

  useGetUserAccounts({
    onSuccess: (accounts: Account[]) => {
      setAccounts(accounts);
      if (accounts.length > 0) {
        if (accountSlug) {
          const storedAccount = accounts.filter((acc) => acc.slug === accountSlug);
          if (storedAccount.length > 0) {
            setAccount(storedAccount[0]);
          } else {
            setAccount(accounts[0]);
          }
        } else {
          setAccount(accounts[0]);
        }
      }
    },
    onError: redirectOnError,
    enabled: !isPublicPage(),
  });

  useEffect(() => {
    if (currentUser && !HasTabAccess(currentUser, currentTab)) {
      setCurrentTab('docs');
    }
  }, [currentTab, currentUser, setCurrentTab]);

  function setCurrentAccount(account: Account | undefined) {
    setAccount(account);
    setAccountSlug(account?.slug);
  }

  return (
    <ChakraProvider resetCSS theme={main}>
      <AccountContext.Provider value={{ currentAccount, setCurrentAccount, accounts, setAccounts }}>
        <WebSocketContext.Provider
          value={{
            webSocket,
            isWebSocketReady,
            webSocketFailed,
            sendMessageBySocket,
            getEnvStatus,
            getSocketMessage,
          }}
        >
          <TabsContext.Provider value={{ currentTab, setCurrentTab }}>
            <ObserveSubTabsContext.Provider
              value={{
                currentSubTab: currentObserveSubTab,
                setCurrentSubTab: setCurrentObserveSubTab,
              }}
            >
              <UserContext.Provider value={{ currentUser, setCurrentUser }}>
                <Router>{children}</Router>
              </UserContext.Provider>
            </ObserveSubTabsContext.Provider>
          </TabsContext.Provider>
        </WebSocketContext.Provider>
      </AccountContext.Provider>
    </ChakraProvider>
  );
};
