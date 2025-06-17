import { lazyImport } from '../utils/lazyImport';

const { PublicRoutes } = lazyImport(() => import('./PublicRoutes'), 'PublicRoutes');

export const AppRoutes = () => {
  return <PublicRoutes />;
};
