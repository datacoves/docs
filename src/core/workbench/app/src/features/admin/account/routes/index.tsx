import { Route, Routes } from 'react-router-dom';

import { Account } from './Account';

export const AccountRoutes = () => {
  return (
    <Routes>
      <Route path="" element={<Account />} />
    </Routes>
  );
};
