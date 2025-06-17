import { createContext } from 'react';

import { Account, IAccountContext } from './types';

export const AccountContext = createContext<IAccountContext>({
  currentAccount: undefined,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  setCurrentAccount: (account: Account | undefined) => {},
  accounts: [],
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  setAccounts: (accounts: Account[]) => {},
});
