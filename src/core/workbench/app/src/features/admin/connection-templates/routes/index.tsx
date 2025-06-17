import { Route, Routes } from 'react-router-dom';

import { ConnectionTemplateFormPage } from './ConnectionTemplateFormPage';
import { ConnectionTemplates } from './ConnectionTemplates';
export const ConnectionTemplatesRoutes = () => {
  return (
    <Routes>
      <Route path="" element={<ConnectionTemplates />} />
      <Route path="create" element={<ConnectionTemplateFormPage />} />
      <Route path="edit/:id" element={<ConnectionTemplateFormPage />} />
    </Routes>
  );
};
