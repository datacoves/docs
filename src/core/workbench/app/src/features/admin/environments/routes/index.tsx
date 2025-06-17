import { Route, Routes } from 'react-router-dom';

import { EnvironmentFormPage } from './EnvironmentFormPage';
import { EnvironmentKeysPage } from './EnvironmentKeysPage';
import { Environments } from './Environments';
export const EnvironmentsRoutes = () => {
  return (
    <Routes>
      <Route path="" element={<Environments />} />
      <Route path="create" element={<EnvironmentFormPage />} />
      <Route path="edit/:id" element={<EnvironmentFormPage />} />
      <Route path="edit/:id/keys" element={<EnvironmentKeysPage />} />
    </Routes>
  );
};
