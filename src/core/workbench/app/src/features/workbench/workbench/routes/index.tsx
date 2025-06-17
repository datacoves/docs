import { Route, Routes } from 'react-router-dom';

import { Workbench } from './Workbench';

export const WorkbenchRoutes = () => {
  return (
    <Routes>
      <Route path="" element={<Workbench />} />
    </Routes>
  );
};
