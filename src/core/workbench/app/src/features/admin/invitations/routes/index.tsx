import { Route, Routes } from 'react-router-dom';

import { InvitationFormPage } from './InvitationFormPage';
import { Invitations } from './Invitations';

export const InvitationsRoutes = () => {
  return (
    <Routes>
      <Route path="" element={<Invitations />} />
      <Route path="create" element={<InvitationFormPage />} />
    </Routes>
  );
};
