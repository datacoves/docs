import { Route, Routes } from 'react-router-dom';

import { ProfileFormPage } from './ProfileFormPage';
import { Profiles } from './Profiles';
export const ProfilesRoutes = () => {
  return (
    <Routes>
      <Route path="" element={<Profiles />} />
      <Route path="create" element={<ProfileFormPage />} />
      <Route path="edit/:id" element={<ProfileFormPage />} />
    </Routes>
  );
};
