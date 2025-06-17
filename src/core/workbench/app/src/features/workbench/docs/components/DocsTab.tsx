import React from 'react';

import { WorkbenchTab } from '../../../../components/WorkbenchTab';
import { docsLink } from '../../../../utils/link';

export function DocsTab({ isLoading }: { isLoading: boolean }) {
  return <WorkbenchTab name="docs" url={docsLink(false)} isLoading={isLoading} />;
}
