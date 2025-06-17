import { createContext } from 'react';

export const ObserveSubTabsContext = createContext({
  currentSubTab: '',
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  setCurrentSubTab: (subTabId: string) => {},
});
