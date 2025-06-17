import { Route, Routes } from 'react-router-dom';

import { SecretFormPage } from './SecretFormPage';
import { Secrets } from './Secrets';
export const SecretsRoutes = () => {
  return (
    <Routes>
      <Route path="" element={<Secrets />} />
      <Route path="create" element={<SecretFormPage />} />
      <Route path="edit/:id" element={<SecretFormPage />} />
    </Routes>
  );
};
