import { useMemo, useContext, useEffect } from 'react';
import { useLocation, Navigate } from 'react-router';

import { AccountContext } from '../../../context/AccountContext';

export const LaunchpadRedirect = () => {
  const { search } = useLocation();
  const query = useMemo(() => new URLSearchParams(search), [search]);
  const { accounts, currentAccount, setCurrentAccount } = useContext(AccountContext);
  const account = query.get('account');

  useEffect(() => {
    if (account && accounts && currentAccount?.slug !== account) {
      const foundAccount = accounts?.find(({ slug }) => slug === account);
      foundAccount && setCurrentAccount(foundAccount);
    }
  }, [account, accounts, currentAccount?.slug, setCurrentAccount]);
  return <>{accounts && <Navigate to="/launchpad" />}</>;
};
