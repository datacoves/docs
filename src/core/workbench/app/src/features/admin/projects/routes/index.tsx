import { Route, Routes } from 'react-router-dom';

import { ProjectFormPage } from './ProjectFormPage';
import { ProjectKeysPage } from './ProjectKeysPage';
import { Projects } from './Projects';

export const ProjectsRoutes = () => {
  return (
    <Routes>
      <Route path="" element={<Projects />} />
      <Route path="edit/:id" element={<ProjectFormPage />} />
      <Route path="edit/:id/keys" element={<ProjectKeysPage />} />
      <Route path="create" element={<ProjectFormPage />} />
    </Routes>
  );
};
