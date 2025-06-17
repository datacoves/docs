import { Route, Routes } from 'react-router-dom';

import { ServiceCredentialFormPage } from './ServiceCredentialFormPage';
import { ServiceCredentials } from './ServiceCredentials';
export const ServiceCredentialsRoutes = () => {
  return (
    <Routes>
      <Route path="" element={<ServiceCredentials />} />
      <Route path="create" element={<ServiceCredentialFormPage />} />
      <Route path="edit/:id" element={<ServiceCredentialFormPage />} />
    </Routes>
  );
};
