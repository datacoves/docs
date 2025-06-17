import React from 'react';

import { WorkbenchTab } from '../../../../components/WorkbenchTab';
import { orchestrateLink } from '../../../../utils/link';

export function OrchestrateTab({ isLoading }: { isLoading: boolean }) {
  return <WorkbenchTab name="orchestrate" url={orchestrateLink()} isLoading={isLoading} />;
}
