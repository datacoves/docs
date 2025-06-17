import { createContext } from 'react';

export const TabsContext = createContext({
  currentTab: '',
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  setCurrentTab: (tabId: string) => {},
});
