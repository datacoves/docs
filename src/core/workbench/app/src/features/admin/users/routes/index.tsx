import { Route, Routes } from 'react-router-dom';

import { UserFormPage } from './UserFormPage';
import { Users } from './Users';

export const UsersRoutes = () => {
  return (
    <Routes>
      <Route path="" element={<Users />} />
      <Route path="edit/:id" element={<UserFormPage />} />
    </Routes>
  );
};
