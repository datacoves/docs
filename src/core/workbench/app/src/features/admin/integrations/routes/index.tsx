import { Route, Routes } from 'react-router-dom';

import { IntegrationFormPage } from './IntegrationFormPage';
import { Integrations } from './Integrations';
export const IntegrationsRoutes = () => {
  return (
    <Routes>
      <Route path="" element={<Integrations />} />
      <Route path="create" element={<IntegrationFormPage />} />
      <Route path="edit/:id" element={<IntegrationFormPage />} />
    </Routes>
  );
};
