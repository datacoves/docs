import { Route, Routes } from 'react-router-dom';

import { Error404Page } from '../../../components/Error/404';

import { AccountSetup } from './AccountSetup';
import { Launchpad } from './Launchpad';
import { Profile } from './Profile';
import { SignIn } from './SignIn';

export const GlobalRoutes = () => {
  return (
    <Routes>
      <Route path="*" element={<Error404Page />} />
      <Route path="settings" element={<Profile />} />
      <Route path="account-setup" element={<AccountSetup />} />
      <Route path="launchpad" element={<Launchpad />} />
      <Route path="sign-in" element={<SignIn />} />
    </Routes>
  );
};
