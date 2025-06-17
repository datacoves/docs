import { createContext } from 'react';
import { object } from 'yup';

export interface IWebSocketContext {
  webSocket: WebSocket | undefined;
  isWebSocketReady: boolean;
  webSocketFailed: boolean;
  sendMessageBySocket: (message: object) => void;
  getEnvStatus: (envSlug: string) => object | null;
  getSocketMessage: (messageType: string) => object | null;
}

export const WebSocketContext = createContext<IWebSocketContext>({
  webSocket: undefined,
  isWebSocketReady: false,
  webSocketFailed: false,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  sendMessageBySocket: (message: object) => {},
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  getEnvStatus: (envSlug: string) => object,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  getSocketMessage: (messageType: string) => object,
});
