import { Route, Routes } from 'react-router-dom';

import { GroupFormPage } from './GroupFormPage';
import { Groups } from './Groups';

export const GroupsRoutes = () => {
  return (
    <Routes>
      <Route path="" element={<Groups />} />
      <Route path="create" element={<GroupFormPage />} />
      <Route path="edit/:id" element={<GroupFormPage />} />
    </Routes>
  );
};
