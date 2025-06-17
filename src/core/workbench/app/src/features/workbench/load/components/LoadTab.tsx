import React from 'react';

import { WorkbenchTab } from '../../../../components/WorkbenchTab';
import { loadLink } from '../../../../utils/link';

export function LoadTab({ isLoading }: { isLoading: boolean }) {
  return <WorkbenchTab name="load" url={loadLink()} isLoading={isLoading} />;
}
