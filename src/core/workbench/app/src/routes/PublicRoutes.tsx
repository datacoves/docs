import * as Sentry from '@sentry/react';
import { Navigate, Route, Routes } from 'react-router-dom';

import { ConnectionTemplatesRoutes } from '../features/admin';
import { AccountRoutes } from '../features/admin/account';
import { BillingRoutes } from '../features/admin/billing';
import { EnvironmentsRoutes } from '../features/admin/environments';
import { GroupsRoutes } from '../features/admin/groups';
import { IntegrationsRoutes } from '../features/admin/integrations';
import { InvitationsRoutes } from '../features/admin/invitations';
import { ProfilesRoutes } from '../features/admin/profiles';
import { ProjectsRoutes } from '../features/admin/projects';
import { SecretsRoutes } from '../features/admin/secrets';
import { ServiceCredentialsRoutes } from '../features/admin/service-credentials';
import { UsersRoutes } from '../features/admin/users';
import { GlobalRoutes } from '../features/global';
import { LaunchpadRedirect } from '../features/global/components/LaunchpadRedirect';
import { WorkbenchRoutes } from '../features/workbench/workbench';
import { getSiteContext } from '../utils/siteContext';

const SentryRoutes = Sentry.withSentryReactRouterV6Routing(Routes);

export const PublicRoutes = () => {
  const siteContext = getSiteContext();
  return (
    <SentryRoutes>
      <Route path="/workbench/*" element={<WorkbenchRoutes />} />
      <Route path="/admin/users/*" element={<UsersRoutes />} />
      <Route path="/admin/invitations/*" element={<InvitationsRoutes />} />
      <Route path="/admin/projects/*" element={<ProjectsRoutes />} />
      <Route path="/admin/environments/*" element={<EnvironmentsRoutes />} />
      <Route path="/admin/connection-templates/*" element={<ConnectionTemplatesRoutes />} />
      <Route path="/admin/service-connections/*" element={<ServiceCredentialsRoutes />} />
      <Route path="/admin/integrations/*" element={<IntegrationsRoutes />} />
      <Route path="/admin/secrets/*" element={<SecretsRoutes />} />
      <Route path="/admin/groups/*" element={<GroupsRoutes />} />
      <Route path="/admin/billing/*" element={<BillingRoutes />} />
      <Route path="/admin/account/*" element={<AccountRoutes />} />
      <Route path="/admin/profiles/*" element={<ProfilesRoutes />} />
      {siteContext.env && <Route path="/" element={<Navigate to="/workbench" />} />}
      {!siteContext.env && <Route path="/" element={<LaunchpadRedirect />} />}
      <Route path="*" element={<GlobalRoutes />} />
    </SentryRoutes>
  );
};
